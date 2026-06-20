# tests/test_writer_base.py
from unittest.mock import MagicMock
from models import Record, ImageRef, Room
from writers.base import BaseWriter, TableConfig, SubTableConfig, GpsMode


def _cfg_goods():
    return TableConfig(
        table="vill_goods", mode="insert", gps=GpsMode.NONE,
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "online", "deleted_flag"],
        has_comment_code=True,
        field_map={"name": "goods_name", "price": "price", "detail": "introduce"},
        image_fields={"images": "goods_imgs"},
        extra_defaults={"goods_status": 2, "category_id": 7, "shop_id": 2},
    )


def _args_to_dict(sql, args):
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    return dict(zip(cols, args))


def test_insert_builds_row_with_defaults_and_images():
    db = MagicMock()
    db.execute.return_value = 5
    def resolver(refs):
        return ["public/common/" + r.url[-5:] + ".jpg" for r in refs]
    w = BaseWriter(db, _cfg_goods(), resolver,
                   village={"id": 1, "village_name": "X"}, defaults={})
    rec = Record(name="笋干", price=50, detail="详情",
                 images=[ImageRef(url="http://x/12345")])
    count = w.write([rec])
    sql, args = db.execute.call_args.args
    adict = _args_to_dict(sql, args)
    assert adict["goods_name"] == "笋干"
    assert adict["price"] == 50
    assert adict["village_id"] == 1
    assert "village_name" not in adict   # goods has no village_name column
    assert adict["category_id"] == 7
    assert adict["goods_status"] == 2
    assert adict["create_user_id"] == 43
    assert adict["comment_code"]            # generated
    assert "member_id" not in adict         # goods config doesn't list member_id
    assert adict["goods_imgs"] == "public/common/12345.jpg"
    assert count == 1


def _set_cols(sql, args):
    set_part = sql.split("SET", 1)[1]
    cols = [c.split("=")[0].strip() for c in set_part.split(",")]
    return dict(zip(cols, args))


def test_update_mode_uses_where_id_and_no_village_id():
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs): return []
    cfg = TableConfig(
        table="vill_village", mode="update", gps=GpsMode.NONE,
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "deleted_flag"],
        has_comment_code=False,
        field_map={"village_intro": "introduce"},
        image_fields={"images": "entire_cover_img"}, extra_defaults={})
    w = BaseWriter(db, cfg, resolver, village={"id": 77, "village_name": "X"}, defaults={})
    rec = Record(village_intro="村介绍")
    w.write([rec])
    sql, args = db.execute.call_args.args
    assert sql.startswith("UPDATE vill_village SET")
    assert "WHERE id = %s" in sql
    assert args[-1] == 77
    adict = _set_cols(sql, args[:-1])
    assert "village_id" not in adict
    assert "comment_code" not in adict


def test_point_gps_uses_wkt():
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs): return []
    cfg = TableConfig(
        table="vill_attraction", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "online", "deleted_flag"],
        has_comment_code=True,
        address_columns=["village_name", "province_id", "province_name", "city_id",
                         "city_name", "area_id", "area_name", "street_id", "street_name", "address"],
        field_map={"name": "attraction_name", "intro": "introduction"},
        image_fields={"images": "cover_img"}, extra_defaults={})
    w = BaseWriter(db, cfg, resolver,
                   village={"id": 1, "lng": 119.0, "lat": 29.0, "village_name": "v",
                            "province_name": "p", "city_name": "c", "area_name": "a",
                            "street_name": "s", "address": "addr",
                            "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4},
                   defaults={})
    rec = Record(name="景区", intro="介绍", lng=None, lat=None)
    w.write([rec])
    sql, args = db.execute.call_args.args
    assert "location_point" in sql
    assert "ST_GeomFromText(%s)" in sql
    assert "POINT(119.0 29.0)" in args


def test_subtable_rooms_inserted_with_fk():
    db = MagicMock()
    db.execute.side_effect = [100, 200]  # homestay id, then room id
    def resolver(refs): return []
    cfg = TableConfig(
        table="vill_homestay", mode="insert", gps=GpsMode.POINT,
        point_column="location",
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "online", "deleted_flag"],
        has_comment_code=True,
        field_map={"title": "title", "intro": "introduce"},
        image_fields={"images": "cover_img"}, extra_defaults={"homeowner_id": 4},
        sub_tables=[SubTableConfig(
            table="vill_homestay_room", fk_column="homestay_id", records_attr="rooms",
            uniform_columns=["create_user_id", "update_user_id", "approve_status",
                             "approve_id", "online", "deleted_flag"],
            has_comment_code=False,
            field_map={"room_name": "room_name", "room_type": "room_type",
                       "intro": "introduction", "price": "week_day_price"},
            image_fields={"images": "cover_img"})])
    w = BaseWriter(db, cfg, resolver, village={"id": 1, "village_name": "X",
                                               "lng": 1.0, "lat": 2.0}, defaults={})
    rec = Record(title="t", intro="i", images=[], lng=1.0, lat=2.0,
                 rooms=[Room(room_name="101")])
    w.write([rec])
    # second execute is the room insert; its args must include the homestay id 100
    room_sql, room_args = db.execute.call_args_list[1].args
    assert "vill_homestay_room" in room_sql
    assert 100 in room_args
