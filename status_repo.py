# status_repo.py

_INSERT = """INSERT INTO task_status (village_id, status, started_at)
VALUES (%s, 'pending', NOW())"""
_UPDATE = """UPDATE task_status SET status=%s, error_msg=%s, records_written=%s,
raw_response=%s, retry_count=retry_count+%s, finished_at=NOW() WHERE village_id=%s"""
_DONE_IDS = "SELECT village_id FROM task_status WHERE status='done'"
_FAILED_IDS = "SELECT village_id FROM task_status WHERE status='failed'"


class StatusRepo:
    def __init__(self, db):
        self._db = db

    def mark_pending(self, village_id):
        self._db.execute(_INSERT, (village_id,))

    def mark_done(self, village_id, records_written=0, raw=""):
        self._db.execute(_UPDATE, ("done", None, records_written, raw, 0, village_id))

    def mark_failed(self, village_id, error_msg, raw=""):
        self._db.execute(_UPDATE, ("failed", error_msg, 0, raw, 1, village_id))

    def done_ids(self):
        rows = self._db.query(_DONE_IDS)
        return {r["village_id"] for r in rows}

    def failed_ids(self):
        rows = self._db.query(_FAILED_IDS)
        return {r["village_id"] for r in rows}
