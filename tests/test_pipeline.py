# tests/test_pipeline.py
import json, pytest
from unittest.mock import MagicMock
from pipeline import Pipeline


def test_pipeline_writes_all_categories_and_commits():
    raw = json.dumps({
        "basic_info": [{"head_name":"张","secretary_intro":"s","contact_phone":"p","village_intro":"v","images":["http://a"]}],
        "minsu": [{"title":"t","intro":"i","images":["http://b"],"lng":1.0,"lat":2.0,"rooms":[{"room_name":"101","images":["http://r"]}]}],
        "specialty": [{"name":"n","price":10,"detail":"d","category":"炒货","images":["http://c"]}],
        "news": [{"content":"c","images":["http://e"]}],
        "activity": [{"name":"a","intro":"i","images":["http://f"],"days":[{"day_name":"d1","images":[],"trips":[{"trip_name":"t1"}]}]}],
        "route": [{"name":"r","intro":"i","images":[]}],
        "farmhouse": [{"name":"f","intro":"i","images":[],"dishes":[{"dish_name":"x","images":[]}]}],
        "scenic": [{"name":"s","intro":"i","images":[]}],
        "sages": [{"type":"xiangxian","name":"李","intro":"i","images":[]}],
    }, ensure_ascii=False)

    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock()
    uploader.upload_url.side_effect = lambda url: ("public/common/" + url[-1] + ".jpg", 123)
    db = MagicMock(); db.execute.return_value = 1
    category_repo = MagicMock(); category_repo.get.return_value = 376  # 炒货
    village = {"id": 1, "village_name": "V", "province_name": "P", "city_name": "C",
               "area_name": "A", "street_name": "S", "address": "addr", "lng": 119.0, "lat": 29.0,
               "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=category_repo, goods_category_fallback=0)
    count, raw_back = pipe.run(village, question="q")
    assert db.execute.call_count >= 8   # at least one write per category record
    assert count >= 8
    db.commit.assert_called_once()


def test_pipeline_rolls_back_on_parse_failure():
    kimi = MagicMock(); kimi.ask.return_value = "not json"
    uploader = MagicMock()
    db = MagicMock()
    village = {"id": 1, "village_name": "V"}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0)
    with pytest.raises(RuntimeError):
        pipe.run(village, question="q")
    db.rollback.assert_called_once()


def test_pipeline_overwrite_deletes_existing_before_writes():
    raw = json.dumps({"scenic": [{"name": "s", "intro": "i", "images": [],
                                   "lng": 1.0, "lat": 2.0}]}, ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock(); uploader.upload_url.return_value = ("", 0)
    db = MagicMock(); db.execute.return_value = 1
    village = {"id": 5, "village_name": "V", "province_name": "P", "city_name": "C",
               "area_name": "A", "street_name": "S", "address": "x", "lng": 1.0, "lat": 2.0,
               "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0)
    pipe.run(village, "q", overwrite=True)
    sqls = [c.args[0] for c in db.execute.call_args_list]
    delete_idxs = [i for i, s in enumerate(sqls) if s.startswith("DELETE")]
    write_idxs = [i for i, s in enumerate(sqls)
                  if s.startswith("INSERT") or s.startswith("UPDATE")]
    assert delete_idxs, "expected overwrite DELETEs"
    assert write_idxs
    assert max(delete_idxs) < min(write_idxs)   # deletes before writes (atomic)
    assert any("vill_homestay_room" in s for s in sqls)  # sub-table via subquery, not village_id
    db.commit.assert_called_once()


def test_pipeline_skips_specialty_when_category_unmatched_and_no_fallback():
    raw = json.dumps({"specialty": [{"name": "n", "price": 10, "detail": "d",
                                     "category": "不存在的类", "images": ["http://c"]}]},
                     ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock(); uploader.upload_url.return_value = ("public/common/c.jpg", 9)
    db = MagicMock(); db.execute.return_value = 1
    category_repo = MagicMock(); category_repo.get.return_value = None  # no match
    village = {"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=category_repo, goods_category_fallback=0)
    count, _ = pipe.run(village, "q")
    assert count == 0
    # no INSERT into vill_goods happened
    sqls = [c.args[0] for c in db.execute.call_args_list]
    assert not any("vill_goods" in s and s.startswith("INSERT") for s in sqls)
    db.commit.assert_called_once()


def test_pipeline_failed_image_cached_and_warned_once(capsys):
    # sages has image_fields(img_url) + image_first_fields(avatar): two resolve calls
    # for the same images. A failing URL must be uploaded once, warned once.
    raw = json.dumps({"sages": [{"type": "xiangxian", "name": "李", "intro": "i",
                                 "images": ["http://x/bad.jpg"]}]}, ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock(); uploader.upload_url.return_value = ("", 0)  # always fails
    db = MagicMock(); db.execute.return_value = 1
    village = {"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0)
    count, _ = pipe.run(village, "q")
    assert count == 1  # sages has no skip_if_no_images -> record still written
    assert uploader.upload_url.call_count == 1  # cached, not retried for avatar
    out = capsys.readouterr().out
    assert out.count("[warn]") == 1
