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
    def resolver(refs, keyword=None, table=None, column=None):
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
    def resolver(refs, keyword=None, table=None, column=None): return []
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
    def resolver(refs, keyword=None, table=None, column=None): return []
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
    def resolver(refs, keyword=None, table=None, column=None): return []
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


def test_skip_when_skip_if_no_images_and_all_uploads_fail():
    # vill_dynamics.cover/img_url are NOT NULL: a record whose image uploads all fail
    # must be skipped, not inserted with empty image columns.
    db = MagicMock(); db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []  # all uploads fail
    cfg = TableConfig(
        table="vill_dynamics", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=["create_user_id"], has_comment_code=True,
        field_map={"content": "context"},
        image_fields={"images": "img_url"},
        image_first_fields={"images": "cover"},
        skip_if_no_images=True)
    w = BaseWriter(db, cfg, resolver, village={"id": 1, "lng": 1.0, "lat": 2.0}, defaults={})
    rec = Record(content="c", images=[ImageRef(url="http://x/broken.jpg")])
    count = w.write([rec])
    assert count == 0
    db.execute.assert_not_called()


def test_point_record_skipped_when_no_coords():
    # POINT columns (location) are NOT NULL: skip when GPS can't be resolved.
    db = MagicMock(); db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TableConfig(
        table="vill_attraction", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=["create_user_id"], has_comment_code=True,
        field_map={"name": "attraction_name", "intro": "introduction"},
        image_fields={"images": "cover_img"})
    w = BaseWriter(db, cfg, resolver,
                   village={"id": 1, "lng": None, "lat": None}, defaults={})
    rec = Record(name="s", intro="i", lng=None, lat=None)
    count = w.write([rec])
    assert count == 0
    db.execute.assert_not_called()


def test_specialty_price_defaults_to_zero_when_missing():
    # vill_goods.price is NOT NULL: when Kimi omits price, fall back to 0.
    db = MagicMock(); db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TableConfig(
        table="vill_goods", mode="insert", gps=GpsMode.NONE,
        uniform_columns=["create_user_id"], has_comment_code=True,
        field_map={"name": "goods_name", "price": "price", "detail": "introduce"},
        image_fields={"images": "goods_imgs"},
        extra_defaults={"goods_status": 2, "category_id": 0, "shop_id": 2, "price": 0})
    w = BaseWriter(db, cfg, resolver, village={"id": 1}, defaults={})
    rec = Record(name="笋干", price=None, detail="d")  # no price
    w.write([rec])
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    adict = dict(zip(cols, args))
    assert adict["price"] == 0


def test_basic_info_writes_head_introduction_html_wrapped_in_p():
    # secretary_intro goes to head_introduction verbatim AND to
    # head_introduction_html wrapped as <p>...</p>.
    from writers.tables import TABLE_CONFIGS
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TABLE_CONFIGS["basic_info"]
    w = BaseWriter(db, cfg, resolver, village={"id": 1}, defaults={})
    rec = Record(secretary_intro="书记介绍", village_intro="村介绍", head_name="张三")
    w.write([rec])
    sql, args = db.execute.call_args.args
    set_part = sql.split("SET", 1)[1].split("WHERE", 1)[0]
    cols = [c.split("=")[0].strip() for c in set_part.split(",")]
    adict = dict(zip(cols, args[:-1]))  # last arg is the WHERE id
    assert adict["head_introduction"] == "书记介绍"
    assert adict["head_introduction_html"] == "<p>书记介绍</p>"


def test_sages_writes_context_html_wrapped_in_p():
    # sages.intro goes to context verbatim AND to context_html as <p>...</p>.
    from writers.tables import TABLE_CONFIGS
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TABLE_CONFIGS["sages"]
    w = BaseWriter(db, cfg, resolver, village={"id": 1}, defaults={})
    rec = Record(name="村贤", intro="村贤介绍")
    w.write([rec])
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    adict = dict(zip(cols, args))
    assert adict["context"] == "村贤介绍"
    assert adict["context_html"] == "<p>村贤介绍</p>"


def test_minsu_writes_introduce_html_wrapped_in_p():
    # minsu.intro goes to introduce verbatim AND to introduce_html as <p>...</p>.
    from writers.tables import TABLE_CONFIGS
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TABLE_CONFIGS["minsu"]
    w = BaseWriter(db, cfg, resolver,
                   village={"id": 1, "village_name": "X", "lng": 1.0, "lat": 2.0}, defaults={})
    rec = Record(title="t", intro="民宿介绍", images=[], lng=1.0, lat=2.0)
    w.write([rec])
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    adict = dict(zip(cols, args))
    assert adict["introduce"] == "民宿介绍"
    assert adict["introduce_html"] == "<p>民宿介绍</p>"


def test_minsu_score_defaults_to_10():
    from writers.tables import TABLE_CONFIGS
    assert TABLE_CONFIGS["minsu"].extra_defaults["score"] == 10


def test_room_price_derived_from_given_base():
    # Room.price present -> week_day=base, holiday=base*1.3, special=base*0.7;
    # max_residents=2; roomarea random in 10..30.
    from writers.tables import TABLE_CONFIGS
    db = MagicMock()
    db.execute.side_effect = [100, 200]  # homestay id, room id
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TABLE_CONFIGS["minsu"]
    w = BaseWriter(db, cfg, resolver,
                   village={"id": 1, "village_name": "X", "lng": 1.0, "lat": 2.0}, defaults={})
    rec = Record(title="t", intro="i", images=[], lng=1.0, lat=2.0,
                 rooms=[Room(room_name="101", price=200)])
    w.write([rec])
    room_sql, room_args = db.execute.call_args_list[1].args
    inside = room_sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    adict = dict(zip(cols, room_args))
    assert adict["week_day_price"] == 200
    assert adict["holiday_price"] == 260.0
    assert adict["special_day_price"] == 140.0
    assert adict["max_residents"] == 2
    assert 10 <= int(adict["roomarea"]) <= 30


def test_room_price_random_when_missing():
    # Room.price None -> base random 100..300; the three prices stay consistent
    # with each other (holiday == base*1.3, special == base*0.7).
    from writers.tables import TABLE_CONFIGS
    db = MagicMock()
    db.execute.side_effect = [100, 200]
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TABLE_CONFIGS["minsu"]
    w = BaseWriter(db, cfg, resolver,
                   village={"id": 1, "village_name": "X", "lng": 1.0, "lat": 2.0}, defaults={})
    rec = Record(title="t", intro="i", images=[], lng=1.0, lat=2.0,
                 rooms=[Room(room_name="101", price=None)])
    w.write([rec])
    room_sql, room_args = db.execute.call_args_list[1].args
    inside = room_sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    adict = dict(zip(cols, room_args))
    base = adict["week_day_price"]
    assert 100 <= base <= 300
    assert adict["holiday_price"] == round(base * 1.3, 2)
    assert adict["special_day_price"] == round(base * 0.7, 2)


def test_specialty_writes_introduce_html_wrapped_in_p():
    # specialty.detail -> introduce verbatim AND introduce_html as <p>...</p>.
    from writers.tables import TABLE_CONFIGS
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs, keyword=None, table=None, column=None): return []
    cfg = TABLE_CONFIGS["specialty"]
    w = BaseWriter(db, cfg, resolver, village={"id": 1}, defaults={"category_id": 7})
    rec = Record(name="笋干", detail="详情介绍")
    w.write([rec])
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    adict = dict(zip(cols, args))
    assert adict["introduce"] == "详情介绍"
    assert adict["introduce_html"] == "<p>详情介绍</p>"


def test_approve_id_default_is_75():
    from writers.base import DEFAULT_VALUES
    assert DEFAULT_VALUES["approve_id"] == 75


def test_basic_info_sets_approve_time():
    from writers.tables import TABLE_CONFIGS
    assert "approve_time" in TABLE_CONFIGS["basic_info"].derived_fields
    assert "approve_time" in TABLE_CONFIGS["minsu"].derived_fields
    assert "approve_time" in TABLE_CONFIGS["specialty"].derived_fields
    # tables WITHOUT the column must NOT set it
    assert "approve_time" not in TABLE_CONFIGS["sages"].derived_fields
    assert "approve_time" not in TABLE_CONFIGS["news"].derived_fields
    assert "approve_time" not in TABLE_CONFIGS["farmhouse"].derived_fields


def test_room_transform_sets_approve_time():
    from writers.tables import _room_transform
    row = {}
    _room_transform(_DummyPrice(200), row)
    assert "approve_time" in row


class _DummyPrice:
    def __init__(self, p): self.price = p


def test_news_uses_pre_resolved_image_keys_without_resolve():
    # mood-dynamic records carry pre-resolved file_keys (from vill_dynamics);
    # the writer must use them directly and NOT call the resolver (which would
    # upload a duplicate Pixabay image).
    from writers.tables import TABLE_CONFIGS
    db = MagicMock(); db.execute.return_value = 1
    calls = {"n": 0}
    def resolver(refs, keyword=None, table=None, column=None):
        calls["n"] += 1
        return ["public/common/should-not-be-used.jpg"]
    cfg = TABLE_CONFIGS["news"]
    w = BaseWriter(db, cfg, resolver, village={"id": 1, "village_name": "V"}, defaults={})
    rec = Record(content="心情", image_keys=["public/common/a.jpg", "public/common/b.jpg"])
    w.write([rec])
    assert calls["n"] == 0  # resolver never called — keys used directly
    sql, args = db.execute.call_args.args
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    adict = dict(zip([c.strip() for c in inside.split(",")], args))
    assert adict["img_url"] == "public/common/a.jpg,public/common/b.jpg"
    assert adict["cover"] == "public/common/a.jpg"
