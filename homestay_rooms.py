# homestay_rooms.py
"""Generate filler homestay room records (vill_homestay_room) when the LLM
returns none for a homestay's rooms. room_name is the room-type name and
room_type is the matching code; price/occupancy/area are filled by the writer's
room transform, and images by the pipeline's fallback chain.
"""
import random

from models import Room

# (room_type code, room_name) — matches vill_homestay_room.room_type comment
_ROOM_TYPES = [
    (1, "大床房"),
    (2, "双人房"),
    (3, "亲子房"),
    (4, "套房"),
    (5, "VIP房"),
]


def generate(n: int = 2):
    """Return n distinct room Records with random types."""
    picks = random.sample(_ROOM_TYPES, min(n, len(_ROOM_TYPES)))
    return [Room(room_name=name, room_type=code, intro="", price=None, images=[])
            for code, name in picks]
