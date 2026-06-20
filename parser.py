# parser.py
import json
import re
from models import VillageData, Record, ImageRef, Room, Dish, Day, Trip


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _images(arr):
    return [ImageRef(url=u) for u in (arr or []) if isinstance(u, str) and u]


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sages_type(t):
    # DB: 1=先贤(已故), 2=乡贤(在世)
    return 2 if (t or "").lower() == "xiangxian" else 1


def _rooms(arr):
    out = []
    for o in (arr or []):
        out.append(Room(
            room_name=o.get("room_name", "") or "",
            room_type=int(o.get("room_type", 1) or 1),
            intro=o.get("intro", "") or "",
            price=_num(o.get("price")),
            images=_images(o.get("images")),
        ))
    return out


def _dishes(arr):
    out = []
    for o in (arr or []):
        out.append(Dish(
            dish_name=o.get("dish_name", "") or "",
            price=_num(o.get("price")),
            intro=o.get("intro", "") or "",
            images=_images(o.get("images")),
        ))
    return out


def _days(arr):
    out = []
    for o in (arr or []):
        out.append(Day(
            day_name=o.get("day_name", "") or "",
            intro=o.get("intro", "") or "",
            images=_images(o.get("images")),
            trips=[Trip(
                trip_name=t.get("trip_name", "") or "",
                trip_time=t.get("trip_time", "") or "",
                intro=t.get("intro", "") or "",
            ) for t in (o.get("trips") or [])],
        ))
    return out


def _record(obj):
    return Record(
        name=obj.get("name", "") or "",
        title=obj.get("title", "") or "",
        intro=obj.get("intro", "") or "",
        content=obj.get("content", "") or "",
        price=_num(obj.get("price")),
        detail=obj.get("detail", "") or "",
        head_name=obj.get("head_name", "") or "",
        secretary_intro=obj.get("secretary_intro", "") or "",
        contact_phone=obj.get("contact_phone", "") or "",
        village_intro=obj.get("village_intro", "") or "",
        sages_type=_sages_type(obj.get("type")),
        lng=_num(obj.get("lng")),
        lat=_num(obj.get("lat")),
        images=_images(obj.get("images")),
        rooms=_rooms(obj.get("rooms")),
        dishes=_dishes(obj.get("dishes")),
        days=_days(obj.get("days")),
    )


_CATEGORY_BUILDERS = {
    "basic_info": _record, "sages": _record, "minsu": _record,
    "specialty": _record, "news": _record, "activity": _record,
    "route": _record, "farmhouse": _record, "scenic": _record,
}

# categories where an empty identity field means skip the record
_IDENTITY_KEY = {
    "basic_info": None,        # keep the single record if present
    "sages": "name", "minsu": "title", "specialty": "name",
    "news": "content", "activity": "name", "route": "name",
    "farmhouse": "name", "scenic": "name",
}


def parse(raw_text: str) -> VillageData:
    obj = json.loads(_strip_fence(raw_text))
    data = VillageData()
    for key, builder in _CATEGORY_BUILDERS.items():
        items = obj.get(key, []) or []
        ident = _IDENTITY_KEY[key]
        kept = []
        for it in items:
            if not isinstance(it, dict):
                continue
            if ident is not None and not (it.get(ident) or "").strip():
                continue
            kept.append(builder(it))
        setattr(data, key, kept)
    return data
