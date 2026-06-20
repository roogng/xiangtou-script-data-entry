# models.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ImageRef:
    url: str           # original URL from Kimi
    file_key: str = "" # set after Qiniu upload


@dataclass
class Room:
    room_name: str = ""
    room_type: int = 1
    intro: str = ""
    price: Optional[float] = None
    images: List[ImageRef] = field(default_factory=list)


@dataclass
class Dish:
    dish_name: str = ""
    price: Optional[float] = None
    intro: str = ""
    images: List[ImageRef] = field(default_factory=list)


@dataclass
class Trip:
    trip_name: str = ""
    trip_time: str = ""
    intro: str = ""


@dataclass
class Day:
    day_name: str = ""
    intro: str = ""
    images: List[ImageRef] = field(default_factory=list)
    trips: List[Trip] = field(default_factory=list)


@dataclass
class Record:
    """One business record across categories. Only relevant fields filled."""
    name: str = ""
    title: str = ""
    intro: str = ""
    content: str = ""
    price: Optional[float] = None
    detail: str = ""
    head_name: str = ""
    secretary_intro: str = ""
    contact_phone: str = ""
    village_intro: str = ""
    sages_type: int = 0         # 2=乡贤(在世) 1=先贤(已故)
    category: str = ""          # specialty: sub-category name from Kimi
    category_id: Optional[int] = None  # specialty: resolved t_category.category_id
    lng: Optional[float] = None
    lat: Optional[float] = None
    images: List[ImageRef] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    dishes: List[Dish] = field(default_factory=list)
    days: List[Day] = field(default_factory=list)


@dataclass
class VillageData:
    """All parsed data for one village."""
    basic_info: List[Record] = field(default_factory=list)
    sages: List[Record] = field(default_factory=list)
    minsu: List[Record] = field(default_factory=list)
    specialty: List[Record] = field(default_factory=list)
    news: List[Record] = field(default_factory=list)
    activity: List[Record] = field(default_factory=list)
    route: List[Record] = field(default_factory=list)
    farmhouse: List[Record] = field(default_factory=list)
    scenic: List[Record] = field(default_factory=list)
