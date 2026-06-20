# tests/test_tables.py
from writers.tables import TABLE_CONFIGS
from writers.base import GpsMode


def test_all_nine_categories_present():
    expected = {"basic_info", "sages", "minsu", "specialty", "news",
                "activity", "route", "farmhouse", "scenic"}
    assert set(TABLE_CONFIGS.keys()) == expected


def test_basic_info_is_update_without_comment_code():
    c = TABLE_CONFIGS["basic_info"]
    assert c.mode == "update"
    assert c.table == "vill_village"
    assert c.has_comment_code is False
    assert "comment_code" not in c.uniform_columns
    assert "entire_cover_img" in c.image_fields.values()


def test_minsu_has_rooms_subtable():
    subs = TABLE_CONFIGS["minsu"].sub_tables
    assert len(subs) == 1
    assert subs[0].table == "vill_homestay_room"
    assert subs[0].fk_column == "homestay_id"


def test_activity_has_days_with_trips():
    subs = TABLE_CONFIGS["activity"].sub_tables
    assert subs[0].table == "vill_village_activity_day"
    assert len(subs[0].children) == 1
    assert subs[0].children[0].table == "vill_village_activity_trip"
    assert subs[0].children[0].fk_column == "day_id"


def test_point_categories():
    assert TABLE_CONFIGS["minsu"].gps == GpsMode.POINT
    assert TABLE_CONFIGS["minsu"].point_column == "location"
    assert TABLE_CONFIGS["scenic"].gps == GpsMode.POINT
    assert TABLE_CONFIGS["farmhouse"].point_column == "location_point"


def test_address_columns_only_on_address_tables():
    assert "village_name" in TABLE_CONFIGS["minsu"].address_columns
    assert "village_name" in TABLE_CONFIGS["farmhouse"].address_columns
    assert "village_name" in TABLE_CONFIGS["scenic"].address_columns
    assert TABLE_CONFIGS["specialty"].address_columns == []
    assert TABLE_CONFIGS["news"].address_columns == []


def test_news_skips_when_no_images():
    assert TABLE_CONFIGS["news"].skip_if_no_images is True
    assert TABLE_CONFIGS["news"].image_first_fields == {"images": "cover"}  # cover NOT NULL


def test_sages_avatar_first_image():
    assert TABLE_CONFIGS["sages"].image_first_fields == {"images": "avatar"}


def test_specialty_has_goods_defaults():
    ed = TABLE_CONFIGS["specialty"].extra_defaults
    assert ed["goods_status"] == 2
    assert "category_id" in ed
    assert ed["shop_id"] == 2
