# tests/test_homestay_rooms.py
from homestay_rooms import generate
from models import Room


def test_generate_returns_two_distinct_rooms():
    rooms = generate(2)
    assert len(rooms) == 2
    assert all(isinstance(r, Room) for r in rooms)
    types = [r.room_type for r in rooms]
    assert len(set(types)) == 2          # distinct room types
    assert all(1 <= t <= 5 for t in types)


def test_room_name_matches_room_type():
    names = {1: "大床房", 2: "双人房", 3: "亲子房", 4: "套房", 5: "VIP房"}
    for _ in range(20):
        rooms = generate(2)
        for r in rooms:
            assert r.room_name == names[r.room_type]


def test_generate_caps_at_pool_size():
    rooms = generate(100)
    assert len(rooms) == 5               # only 5 room types exist
    assert len({r.room_type for r in rooms}) == 5


def test_generate_assigns_distinct_image_sets():
    sets = [["public/common/a.jpg"], ["public/common/b.jpg"]]
    rooms = generate(2, image_sets=sets)
    assert rooms[0].image_keys == ["public/common/a.jpg"]
    assert rooms[1].image_keys == ["public/common/b.jpg"]
    assert rooms[0].image_keys != rooms[1].image_keys


def test_generate_no_image_sets_leaves_keys_empty():
    rooms = generate(2)
    assert all(r.image_keys == [] for r in rooms)
