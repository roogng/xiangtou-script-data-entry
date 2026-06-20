# writers/base.py
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional
from models import Record, ImageRef
from geo import resolve_point, point_wkt


class GpsMode(Enum):
    NONE = "none"
    POINT = "point"
    DECIMAL = "decimal"


# default values for the uniform columns (only applied where a table lists them)
DEFAULT_VALUES = {
    "create_user_id": 43,
    "update_user_id": 43,
    "approve_status": 2,
    "approve_id": 43,
    "online": 1,
    "deleted_flag": 0,
    "member_id": 43,
}


@dataclass
class SubTableConfig:
    table: str
    fk_column: str              # column referencing parent id
    records_attr: str           # attr on Record: "rooms" | "dishes" | "days"
    uniform_columns: List[str]
    has_comment_code: bool
    field_map: Dict[str, str]
    image_fields: Dict[str, str] = field(default_factory=dict)
    extra_defaults: Dict[str, object] = field(default_factory=dict)
    children: List["SubTableConfig"] = field(default_factory=list)
    child_attr: str = ""        # attr on the sub-record holding nested children


@dataclass
class TableConfig:
    table: str
    mode: str                          # "insert" | "update"
    gps: GpsMode
    uniform_columns: List[str]         # which DEFAULT_VALUES columns this table has
    has_comment_code: bool
    field_map: Dict[str, str]          # record-attr -> column
    image_fields: Dict[str, str]       # record-attr(list of images) -> column (comma-joined)
    image_first_fields: Dict[str, str] = field(default_factory=dict)  # first image only -> column
    extra_defaults: Dict[str, object] = field(default_factory=dict)
    point_column: str = "location_point"
    address_columns: List[str] = field(default_factory=list)  # village/address cols this table has
    sub_tables: List[SubTableConfig] = field(default_factory=list)
    skip_if_no_images: bool = False    # e.g. dynamics cover/img_url NOT NULL


ImageResolver = Callable[[List[ImageRef]], List[str]]


class BaseWriter:
    def __init__(self, db, cfg: TableConfig, image_resolver: ImageResolver,
                 village: dict, defaults: dict):
        self._db = db
        self._cfg = cfg
        self._resolve = image_resolver
        self._village = village
        self._defaults = defaults

    def write(self, records: List[Record]) -> int:
        count = 0
        for rec in records:
            if self._cfg.skip_if_no_images and not self._resolve(rec.images or []):
                continue  # NOT NULL image columns can't be satisfied
            if self._cfg.gps == GpsMode.POINT:
                pt = resolve_point(rec.lng, rec.lat,
                                   self._village.get("lng"), self._village.get("lat"))
                if pt is None:
                    continue  # POINT column is NOT NULL; cannot insert without coords
            row = self._build_row(rec)
            if self._cfg.mode == "update":
                self._update(row)
            else:
                parent_id = self._insert(self._cfg.table, row)
                self._write_sub_tables(rec, parent_id)
            count += 1
        return count

    def _build_row(self, rec: Record) -> Dict[str, object]:
        row: Dict[str, object] = {}
        for col in self._cfg.uniform_columns:
            row[col] = DEFAULT_VALUES[col]
        if self._cfg.has_comment_code:
            row["comment_code"] = uuid.uuid4().hex
        for col, val in self._cfg.extra_defaults.items():
            row[col] = val
        for col, val in self._defaults.items():
            row[col] = val
        if self._cfg.mode == "insert":
            row["village_id"] = self._village["id"]
            for col in self._cfg.address_columns:
                if col in self._village:
                    row[col] = self._village[col]
        for attr, col in self._cfg.field_map.items():
            val = getattr(rec, attr, None)
            if val is not None and val != "":
                row[col] = val
        for attr, col in self._cfg.image_fields.items():
            refs = getattr(rec, attr, None) or []
            keys = self._resolve(refs)
            if keys:
                row[col] = ",".join(keys)
        for attr, col in self._cfg.image_first_fields.items():
            refs = getattr(rec, attr, None) or []
            keys = self._resolve(refs)
            if keys:
                row[col] = keys[0]
        self._apply_gps(rec, row)
        return row

    def _apply_gps(self, rec, row):
        if self._cfg.gps == GpsMode.NONE:
            return
        pt = resolve_point(rec.lng, rec.lat,
                           self._village.get("lng"), self._village.get("lat"))
        if pt is None:
            return
        if self._cfg.gps == GpsMode.POINT:
            row[self._cfg.point_column] = ("__POINT__", point_wkt(*pt))
        else:  # DECIMAL
            row["latitude"] = pt[1]
            row["longitude"] = pt[0]

    def _insert(self, table, row) -> int:
        cols, args, point_pos = self._split_row(row)
        ph = ["ST_GeomFromText(%s)" if i == point_pos else "%s" for i in range(len(cols))]
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(ph)})"
        return self._db.execute(sql, tuple(args))

    def _update(self, row):
        vid = self._village["id"]
        cols, args, point_pos = self._split_row(row)
        set_clause = ", ".join(
            f"{c} = ST_GeomFromText(%s)" if i == point_pos else f"{c} = %s"
            for i, c in enumerate(cols))
        sql = f"UPDATE {self._cfg.table} SET {set_clause} WHERE id = %s"
        self._db.execute(sql, tuple(args) + (vid,))

    def _split_row(self, row):
        cols, args, point_pos = [], [], None
        for col, val in row.items():
            if isinstance(val, tuple) and val and val[0] == "__POINT__":
                cols.append(col)
                args.append(val[1])
                point_pos = len(args) - 1
            else:
                cols.append(col)
                args.append(val)
        return cols, args, point_pos

    def _write_sub_tables(self, rec, parent_id):
        for sub in self._cfg.sub_tables:
            items = getattr(rec, sub.records_attr, None) or []
            for it in items:
                row = self._build_sub_row(sub, it, parent_id)
                child_id = self._insert(sub.table, row)
                for child in sub.children:
                    child_items = getattr(it, child.child_attr, None) or []
                    for ci in child_items:
                        crow = self._build_sub_row(child, ci, child_id)
                        self._insert(child.table, crow)

    def _build_sub_row(self, sub, item, fk_id) -> Dict[str, object]:
        row: Dict[str, object] = {}
        for col in sub.uniform_columns:
            row[col] = DEFAULT_VALUES[col]
        if sub.has_comment_code:
            row["comment_code"] = uuid.uuid4().hex
        for col, val in sub.extra_defaults.items():
            row[col] = val
        row[sub.fk_column] = fk_id
        for attr, col in sub.field_map.items():
            val = getattr(item, attr, None)
            if val is not None and val != "":
                row[col] = val
        for attr, col in sub.image_fields.items():
            refs = getattr(item, attr, None) or []
            keys = self._resolve(refs)
            if keys:
                row[col] = ",".join(keys)
        return row
