# tests/test_status_repo.py
from unittest.mock import MagicMock
from status_repo import StatusRepo


def test_mark_pending_inserts():
    db = MagicMock()
    repo = StatusRepo(db)
    repo.mark_pending(123)
    sql, args = db.execute.call_args.args
    assert "INSERT INTO task_status" in sql
    assert args[0] == 123


def test_mark_done_updates_status():
    db = MagicMock()
    repo = StatusRepo(db)
    repo.mark_done(123, records_written=5, raw="raw")
    sql, args = db.execute.call_args.args
    assert "UPDATE task_status SET" in sql
    assert "status=%s" in sql
    assert args[0] == "done"


def test_done_ids_queried():
    db = MagicMock()
    db.query.return_value = [{"village_id": 1}, {"village_id": 2}]
    repo = StatusRepo(db)
    assert repo.done_ids() == {1, 2}


def test_failed_ids_queried():
    db = MagicMock()
    db.query.return_value = [{"village_id": 9}]
    repo = StatusRepo(db)
    assert repo.failed_ids() == {9}
