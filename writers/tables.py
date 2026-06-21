# writers/tables.py
from writers.base import TableConfig, SubTableConfig, GpsMode


def _wrap_p(attr):
    """Return a fn that wraps a record's text attr in <p>...</p> (None if empty)."""
    def fn(rec):
        val = getattr(rec, attr, None)
        if not val:
            return None
        return f"<p>{val}</p>"
    return fn

# uniform column groups reused across tables
_U_COMMON = ["create_user_id", "update_user_id", "approve_status",
             "approve_id", "online", "deleted_flag"]
_U_COMMON_NO_ONLINE = ["create_user_id", "update_user_id", "approve_status",
                        "approve_id", "deleted_flag"]
_U_WITH_MEMBER = ["create_user_id", "update_user_id", "approve_status",
                   "approve_id", "online", "deleted_flag", "member_id"]
_U_MINIMAL = ["create_user_id", "update_user_id", "deleted_flag"]  # activity_day / activity_trip

_ADDR = ["village_name", "province_id", "province_name", "city_id",
         "city_name", "area_id", "area_name", "street_id", "street_name", "address"]

TABLE_CONFIGS = {
    "basic_info": TableConfig(
        table="vill_village", mode="update", gps=GpsMode.NONE,
        uniform_columns=_U_COMMON_NO_ONLINE,
        has_comment_code=False,
        field_map={"secretary_intro": "head_introduction", "contact_phone": "contact_phone",
                   "village_intro": "introduce", "head_name": "head_name"},
        image_fields={"images": "entire_cover_img"},
        derived_fields={"head_introduction_html": _wrap_p("secretary_intro")},
    ),
    "sages": TableConfig(
        table="vill_village_sages", mode="insert", gps=GpsMode.NONE,
        uniform_columns=_U_WITH_MEMBER,
        has_comment_code=True,
        field_map={"name": "sages_name", "intro": "context"},
        image_fields={"images": "img_url"},
        image_first_fields={"images": "avatar"},
        derived_fields={"context_html": _wrap_p("intro")},
    ),
    "minsu": TableConfig(
        table="vill_homestay", mode="insert", gps=GpsMode.POINT,
        point_column="location",
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        address_columns=_ADDR,
        field_map={"title": "title", "intro": "introduce"},
        image_fields={"images": "cover_img"},
        extra_defaults={"homeowner_id": 4},
        sub_tables=[
            SubTableConfig(
                table="vill_homestay_room", fk_column="homestay_id",
                records_attr="rooms",
                uniform_columns=_U_COMMON, has_comment_code=False,
                field_map={"room_name": "room_name", "room_type": "room_type",
                           "intro": "introduction", "price": "week_day_price"},
                image_fields={"images": "cover_img"},
            ),
        ],
    ),
    "specialty": TableConfig(
        table="vill_goods", mode="insert", gps=GpsMode.NONE,
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        field_map={"name": "goods_name", "price": "price", "detail": "introduce",
                   "category_id": "category_id"},
        image_fields={"images": "goods_imgs"},
        extra_defaults={"goods_status": 2, "shop_id": 2, "price": 0},
    ),
    "news": TableConfig(
        table="vill_dynamics", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=_U_WITH_MEMBER,
        has_comment_code=True,
        field_map={"content": "context"},
        image_fields={"images": "img_url"},
        image_first_fields={"images": "cover"},  # cover is NOT NULL single image
        skip_if_no_images=True,   # cover + img_url are NOT NULL
    ),
    "activity": TableConfig(
        table="vill_village_activity", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        field_map={"name": "activity_name", "intro": "introduce"},
        image_fields={"images": "activity_imgs"},
        extra_defaults={"activity_status": 1},
        sub_tables=[
            SubTableConfig(
                table="vill_village_activity_day", fk_column="activity_id",
                records_attr="days",
                uniform_columns=_U_MINIMAL, has_comment_code=False,
                field_map={"day_name": "day_name", "intro": "introduce"},
                image_fields={"images": "travel_day_imgs"},
                extra_defaults={"activity_type": 2},
                children=[
                    SubTableConfig(
                        table="vill_village_activity_trip", fk_column="day_id",
                        records_attr="trips",
                        uniform_columns=_U_MINIMAL, has_comment_code=False,
                        field_map={"trip_name": "trip_name", "trip_time": "trip_time",
                                   "intro": "introduce"},
                        image_fields={},
                    ),
                ],
                child_attr="trips",
            ),
        ],
    ),
    "route": TableConfig(
        table="vill_village_travel", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        field_map={"name": "travel_name", "intro": "introduce"},
        image_fields={"images": "travel_imgs"},
    ),
    "farmhouse": TableConfig(
        table="vill_restaurant", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        address_columns=_ADDR,
        field_map={"name": "restaurant_name", "intro": "introduction"},
        image_fields={"images": "cover_img"},
        extra_defaults={"shop_id": 2},
        sub_tables=[
            SubTableConfig(
                table="vill_restaurant_dish", fk_column="restaurant_id",
                records_attr="dishes",
                uniform_columns=_U_COMMON, has_comment_code=False,
                field_map={"dish_name": "dish_name", "price": "unit_price",
                           "intro": "introduction"},
                image_fields={"images": "cover_img"},
            ),
        ],
    ),
    "scenic": TableConfig(
        table="vill_attraction", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        address_columns=_ADDR,
        field_map={"name": "attraction_name", "intro": "introduction"},
        image_fields={"images": "cover_img"},
    ),
}
