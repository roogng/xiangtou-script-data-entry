# runner.py
from prompt import build_question


class Runner:
    def __init__(self, db, status_repo, pipeline, village_repo, overwrite):
        self._db = db
        self._status = status_repo
        self._pipe = pipeline
        self._village_repo = village_repo
        self._overwrite = overwrite

    def run(self, village_ids):
        done = self._status.done_ids()
        todo = [vid for vid in village_ids if vid not in done]
        for vid in todo:
            village = self._village_repo.fetch(vid)
            if not village:
                print(f"[skip] village {vid} not found")
                continue
            try:
                self._status.mark_pending(vid)
                q = build_question(
                    village.get("province_name", ""), village.get("city_name", ""),
                    village.get("area_name", ""), village.get("street_name", ""),
                    village.get("village_name", ""))
                count, raw = self._pipe.run(village, q, overwrite=self._overwrite)
                self._status.mark_done(vid, records_written=count, raw=raw)
                print(f"[done] village {vid}: {count} records")
            except Exception as e:
                self._status.mark_failed(vid, str(e))
                print(f"[fail] village {vid}: {e}")
