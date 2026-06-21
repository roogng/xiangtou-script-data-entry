# tests/test_pipeline.py
import json, pytest
from unittest.mock import MagicMock, patch
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
    db = MagicMock(); db.execute.return_value = 1; db.query.return_value = []
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
    db = MagicMock(); db.execute.return_value = 1; db.query.return_value = []
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


def _scenic_raw(images):
    return json.dumps({"scenic": [{"name": "s", "intro": "i", "images": images,
                                    "lng": 1.0, "lat": 2.0}]}, ensure_ascii=False)


def test_pipeline_falls_back_to_search_when_no_images():
    # Kimi gave no images -> searcher fills one; cover_img gets the searched key.
    kimi = MagicMock(); kimi.ask.return_value = _scenic_raw([])
    uploader = MagicMock()
    uploader.upload_url.return_value = ("public/common/found.jpg", 50)
    searcher = MagicMock(); searcher.search.return_value = "http://found/x.jpg"
    db = MagicMock(); db.execute.return_value = 1
    file_repo = MagicMock()
    village = {"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0,
               "province_name": "P", "city_name": "C", "area_name": "A",
               "street_name": "S", "address": "x",
               "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}
    pipe = Pipeline(db, kimi, uploader, file_repo, defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0,
                    image_searcher=searcher)
    with patch.object(Pipeline, "_fill_news"):
        pipe.run(village, "q")
    searcher.search.assert_called_once_with("景区 s")
    # the searched image went through upload + t_file insert
    uploader.upload_url.assert_called_with("http://found/x.jpg")
    file_repo.insert.assert_called_with(file_key="public/common/found.jpg",
                                        file_name="x.jpg", file_size=50, file_type="jpg")
    # and landed in the scenic cover_img column
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    adict = dict(zip([c.strip() for c in inside.split(",")], args))
    assert adict["cover_img"] == "public/common/found.jpg"


def test_pipeline_falls_back_to_search_when_all_uploads_fail():
    # Kimi gave an image but the upload fails -> fallback search still applies.
    kimi = MagicMock(); kimi.ask.return_value = _scenic_raw(["http://broken"])
    uploader = MagicMock()
    uploader.upload_url.side_effect = [("", 0), ("public/common/found.jpg", 50)]
    searcher = MagicMock(); searcher.search.return_value = "http://found/x.jpg"
    db = MagicMock(); db.execute.return_value = 1
    village = {"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0,
               "province_name": "P", "city_name": "C", "area_name": "A",
               "street_name": "S", "address": "x",
               "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0,
                    image_searcher=searcher)
    with patch.object(Pipeline, "_fill_news"):
        pipe.run(village, "q")
    searcher.search.assert_called_once_with("景区 s")
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    adict = dict(zip([c.strip() for c in inside.split(",")], args))
    assert adict["cover_img"] == "public/common/found.jpg"


def _full_village():
    return {"id": 1, "village_name": "V", "province_name": "P", "city_name": "C",
            "area_name": "A", "street_name": "S", "address": "x", "lng": 1.0, "lat": 2.0,
            "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}


def _insert_cols(sql):
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    return [c.strip() for c in inside.split(",")]


def test_pipeline_falls_back_to_existing_db_image_when_search_empty():
    # No searcher, no Kimi image -> reuse an existing image value from the same
    # table/column (random pick of recent non-empty rows).
    kimi = MagicMock(); kimi.ask.return_value = _scenic_raw([])
    uploader = MagicMock()
    db = MagicMock(); db.execute.return_value = 1
    db.query.return_value = [{"v": "public/common/existing.jpg,public/common/second.jpg"}]
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0)  # no searcher
    with patch.object(Pipeline, "_fill_news"):
        pipe.run(_full_village(), "q")
    uploader.upload_url.assert_not_called()           # no Kimi image, no web search
    qsql = db.query.call_args.args[0]
    assert "vill_attraction" in qsql and "cover_img" in qsql
    sql, args = db.execute.call_args.args
    adict = dict(zip(_insert_cols(sql), args))
    assert adict["cover_img"] == "public/common/existing.jpg,public/common/second.jpg"


def test_pipeline_sages_no_image_fallback():
    # sages has fallback_images=False: no web search, no DB query, image left empty.
    raw = json.dumps({"sages": [{"type": "xiangxian", "name": "李", "intro": "i",
                                 "images": []}]}, ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock()
    searcher = MagicMock()  # present, but must NOT be called for sages
    db = MagicMock(); db.execute.return_value = 1
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0,
                    image_searcher=searcher)
    with patch.object(Pipeline, "_fill_news"):
        count, _ = pipe.run({"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0}, "q")
    assert count == 1
    searcher.search.assert_not_called()
    db.query.assert_not_called()
    sql, args = db.execute.call_args.args
    cols = _insert_cols(sql)
    assert "img_url" not in cols and "avatar" not in cols


def test_pipeline_retries_parse_until_success():
    # First ask returns malformed JSON, second returns valid -> pipeline proceeds.
    good = json.dumps({"scenic": [{"name": "s", "intro": "i", "images": [],
                                    "lng": 1.0, "lat": 2.0}]}, ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.side_effect = ["not json", good]
    uploader = MagicMock(); uploader.upload_url.return_value = ("", 0)
    db = MagicMock(); db.execute.return_value = 1; db.query.return_value = []
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0)
    count, _ = pipe.run(_full_village(), "q")
    assert kimi.ask.call_count == 2
    assert count == 1
    db.commit.assert_called_once()


def test_pipeline_gives_up_after_parse_retries():
    kimi = MagicMock(); kimi.ask.return_value = "not json"
    db = MagicMock()
    pipe = Pipeline(db, kimi, MagicMock(), file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0, parse_retries=2)
    with pytest.raises(RuntimeError):
        pipe.run({"id": 1, "village_name": "V"}, "q")
    assert kimi.ask.call_count == 3   # 1 + 2 retries
    db.rollback.assert_called_once()


def test_pipeline_fills_two_mood_dynamics_when_news_empty():
    # LLM returns no news -> pipeline generates 2 mood-dynamic records and writes
    # them to vill_dynamics (images filled by the searcher fallback).
    raw = json.dumps({"scenic": [{"name": "s", "intro": "i", "images": [],
                                   "lng": 1.0, "lat": 2.0}]}, ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock()
    uploader.upload_url.return_value = ("public/common/m.jpg", 50)
    searcher = MagicMock(); searcher.search.return_value = "http://x/m.jpg"
    db = MagicMock(); db.execute.return_value = 1; db.query.return_value = []
    village = {"id": 1, "village_name": "金星村", "lng": 1.0, "lat": 2.0}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0,
                    image_searcher=searcher)
    pipe.run(village, "q")
    dyn_sqls = [c.args[0] for c in db.execute.call_args_list
                if "vill_dynamics" in c.args[0] and c.args[0].startswith("INSERT")]
    assert len(dyn_sqls) == 2  # two mood-dynamic records written


def test_pipeline_fills_two_rooms_when_minsu_has_none():
    # homestay with no rooms -> pipeline generates 2 random rooms and writes
    # them to vill_homestay_room (images filled by the searcher fallback).
    raw = json.dumps({"minsu": [{"title": "t", "intro": "i", "images": [],
                                  "lng": 1.0, "lat": 2.0, "rooms": []}]},
                     ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock()
    uploader.upload_url.return_value = ("public/common/r.jpg", 50)
    searcher = MagicMock(); searcher.search.return_value = "http://x/r.jpg"
    db = MagicMock(); db.execute.return_value = 1; db.query.return_value = []
    village = {"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0,
                    image_searcher=searcher)
    pipe.run(village, "q")
    room_sqls = [c.args[0] for c in db.execute.call_args_list
                 if "vill_homestay_room" in c.args[0] and c.args[0].startswith("INSERT")]
    assert len(room_sqls) == 2


def test_pipeline_mood_records_get_distinct_db_images():
    # No news -> 2 mood records generated, each reusing a DISTINCT existing
    # image from vill_dynamics (no upload, no duplicate).
    raw = json.dumps({}, ensure_ascii=False)
    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock()
    db = MagicMock(); db.execute.return_value = 1
    db.query.return_value = [
        {"img_url": "public/common/a.jpg,public/common/b.jpg"},
        {"img_url": "public/common/c.jpg"},
    ]
    village = {"id": 1, "village_name": "V", "lng": 1.0, "lat": 2.0}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    category_repo=MagicMock(), goods_category_fallback=0)
    pipe.run(village, "q")
    uploader.upload_url.assert_not_called()  # images came from DB, no upload
    dyn = [(c.args[0], c.args[1]) for c in db.execute.call_args_list
           if "vill_dynamics" in c.args[0] and c.args[0].startswith("INSERT")]
    assert len(dyn) == 2
    img_urls = []
    for sql, args in dyn:
        inside = sql.split("(", 1)[1].split(")", 1)[0]
        adict = dict(zip([c.strip() for c in inside.split(",")], args))
        img_urls.append(adict["img_url"])
    assert len(set(img_urls)) == 2  # the two records have distinct images
    assert "public/common/a.jpg,public/common/b.jpg" in img_urls
    assert "public/common/c.jpg" in img_urls
