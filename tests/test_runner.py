# tests/test_runner.py
from unittest.mock import MagicMock
from runner import Runner

_V = {"id": 3, "village_name": "V", "province_name": "P", "city_name": "C",
      "area_name": "A", "street_name": "S", "address": "x", "lng": 1.0, "lat": 2.0,
      "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}


def _village_repo():
    vr = MagicMock()
    vr.fetch.return_value = _V
    return vr


def test_runner_skips_done_villages():
    db = MagicMock()
    status = MagicMock(); status.done_ids.return_value = {1, 2}
    pipe = MagicMock(); pipe.run.return_value = (5, "raw")
    runner = Runner(db, status, pipe, village_repo=_village_repo(), overwrite=False)
    runner.run([1, 2, 3])
    pipe.run.assert_called_once()
    assert pipe.run.call_args.args[0]["id"] == 3


def test_runner_marks_failed_on_pipeline_error(capsys):
    db = MagicMock()
    status = MagicMock(); status.done_ids.return_value = set()
    pipe = MagicMock(); pipe.run.side_effect = RuntimeError("boom")
    runner = Runner(db, status, pipe, village_repo=_village_repo(), overwrite=False)
    runner.run([3])
    status.mark_failed.assert_called_once()
    assert status.mark_failed.call_args.args[0] == 3


def test_runner_overwrite_passes_flag_to_pipeline():
    db = MagicMock()
    status = MagicMock(); status.done_ids.return_value = set()
    pipe = MagicMock(); pipe.run.return_value = (1, "raw")
    runner = Runner(db, status, pipe, village_repo=_village_repo(), overwrite=True)
    runner.run([3])
    # deletes now happen inside the pipeline (atomic); runner just forwards the flag
    assert pipe.run.call_args.kwargs.get("overwrite") is True
