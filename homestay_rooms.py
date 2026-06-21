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


def generate(n: int = 2, image_sets=None):
    """Return n distinct room Records with random types.

    image_sets: optional list of file_key lists, one per room, sourced from
    existing vill_homestay_room rows so generated rooms reuse real images
    (distinct per room) instead of all hitting the same Pixabay keyword.
    """
    picks = random.sample(_ROOM_TYPES, min(n, len(_ROOM_TYPES)))
    image_sets = image_sets or []
    rooms = []
    for i, (code, name) in enumerate(picks):
        keys = image_sets[i] if i < len(image_sets) else []
        rooms.append(Room(room_name=name, room_type=code, intro="", price=None,
                          images=[], image_keys=keys))
    return rooms
