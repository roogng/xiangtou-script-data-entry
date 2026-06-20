# tests/test_runner.py
from unittest.mock import MagicMock
from runner import Runner

_V = {"id": 3, "village_name": "V", "province_name": "P", "city_name": "C",
      "area_name": "A", "street_name": "S", "address": "x", "lng": 1.0, "lat": 2.0,
      "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}


def test_runner_skips_done_villages():
    db = MagicMock(); db.query_one.return_value = _V
    status = MagicMock(); status.done_ids.return_value = {1, 2}
    pipe = MagicMock(); pipe.run.return_value = (5, "raw")
    runner = Runner(db, status, pipe, village_repo=MagicMock(), overwrite=False)
    runner.run([1, 2, 3])
    pipe.run.assert_called_once()
    assert pipe.run.call_args.args[0]["id"] == 3


def test_runner_marks_failed_on_pipeline_error(capsys):
    db = MagicMock(); db.query_one.return_value = _V
    status = MagicMock(); status.done_ids.return_value = set()
    pipe = MagicMock(); pipe.run.side_effect = RuntimeError("boom")
    runner = Runner(db, status, pipe, village_repo=MagicMock(), overwrite=False)
    runner.run([3])
    status.mark_failed.assert_called_once()
    assert status.mark_failed.call_args.args[0] == 3


def test_runner_overwrite_deletes_existing():
    db = MagicMock(); db.query_one.return_value = _V
    status = MagicMock(); status.done_ids.return_value = set()
    pipe = MagicMock(); pipe.run.return_value = (1, "raw")
    runner = Runner(db, status, pipe, village_repo=MagicMock(), overwrite=True)
    runner.run([3])
    sqls = [c.args[0] for c in db.execute.call_args_list]
    assert any("DELETE FROM" in s for s in sqls)
