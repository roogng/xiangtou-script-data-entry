# pipeline.py
from writers.base import BaseWriter
from writers.tables import TABLE_CONFIGS
from parser import parse

# Overwrite cleanup. Child tables lacking village_id are deleted via subquery on
# their parent's id. Order is child-first. All run inside the pipeline transaction
# so a failure rolls the deletes back too (no data loss on transient errors).
_DELETE_SQLS = [
    "DELETE FROM vill_homestay_room WHERE homestay_id IN (SELECT id FROM vill_homestay WHERE village_id=%s)",
    "DELETE FROM vill_homestay WHERE village_id=%s",
    "DELETE FROM vill_restaurant_dish WHERE restaurant_id IN (SELECT id FROM vill_restaurant WHERE village_id=%s)",
    "DELETE FROM vill_restaurant WHERE village_id=%s",
    "DELETE FROM vill_village_activity_trip WHERE day_id IN (SELECT id FROM vill_village_activity_day WHERE activity_id IN (SELECT id FROM vill_village_activity WHERE village_id=%s))",
    "DELETE FROM vill_village_activity_day WHERE activity_id IN (SELECT id FROM vill_village_activity WHERE village_id=%s)",
    "DELETE FROM vill_village_activity WHERE village_id=%s",
    "DELETE FROM vill_village_travel WHERE village_id=%s",
    "DELETE FROM vill_dynamics WHERE village_id=%s",
    "DELETE FROM vill_goods WHERE village_id=%s",
    "DELETE FROM vill_village_sages WHERE village_id=%s",
    "DELETE FROM vill_attraction WHERE village_id=%s",
]


class Pipeline:
    def __init__(self, db, kimi, uploader, file_repo, defaults, goods_category_id):
        self._db = db
        self._kimi = kimi
        self._uploader = uploader
        self._file_repo = file_repo
        self._defaults = defaults
        self._goods_category_id = goods_category_id

    def run(self, village: dict, question: str, overwrite: bool = False):
        raw = self._kimi.ask(question)
        try:
            data = parse(raw)
        except Exception as e:
            self._db.rollback()
            raise RuntimeError(f"parse failed: {e}") from e

        cache = {}

        def resolve(refs):
            keys = []
            for ref in refs:
                if not ref.url:
                    continue
                if ref.url in cache:
                    keys.append(cache[ref.url])
                    continue
                file_key, size = self._uploader.upload_url(ref.url)
                if not file_key:
                    continue
                self._file_repo.insert(file_key=file_key,
                                       file_name=ref.url.split("/")[-1] or "image",
                                       file_size=size, file_type="jpg")
                cache[ref.url] = file_key
                keys.append(file_key)
            return keys

        vid = village["id"]
        total = 0
        try:
            if overwrite:
                for sql in _DELETE_SQLS:
                    self._db.execute(sql, (vid,))
            for category, cfg in TABLE_CONFIGS.items():
                records = getattr(data, category, [])
                if not records:
                    continue
                defaults = dict(self._defaults)
                if category == "specialty":
                    defaults["category_id"] = self._goods_category_id
                writer = BaseWriter(self._db, cfg, resolve, village, defaults)
                total += writer.write(records)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return total, raw
