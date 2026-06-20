# pipeline.py
from writers.base import BaseWriter
from writers.tables import TABLE_CONFIGS
from parser import parse


class Pipeline:
    def __init__(self, db, kimi, uploader, file_repo, defaults, goods_category_id):
        self._db = db
        self._kimi = kimi
        self._uploader = uploader
        self._file_repo = file_repo
        self._defaults = defaults
        self._goods_category_id = goods_category_id

    def run(self, village: dict, question: str):
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

        total = 0
        try:
            for category, cfg in TABLE_CONFIGS.items():
                records = getattr(data, category, [])
                if not records:
                    continue
                if category == "specialty":
                    cfg.extra_defaults["category_id"] = self._goods_category_id
                writer = BaseWriter(self._db, cfg, resolve, village, self._defaults)
                total += writer.write(records)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return total, raw
