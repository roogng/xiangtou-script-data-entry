# tests/test_mood_dynamics.py
from mood_dynamics import generate


def test_generate_returns_two_distinct_records():
    recs = generate("金星村", 2)
    assert len(recs) == 2
    contents = [r.content for r in recs]
    assert len(set(contents)) == 2  # distinct
    assert all("金星村" in c for c in contents)
    assert all(r.images == [] for r in recs)


def test_generate_falls_back_to_default_name():
    recs = generate("", 2)
    assert len(recs) == 2
    assert all(r.content for r in recs)


def test_generate_assigns_distinct_image_sets():
    sets = [["public/common/a.jpg", "public/common/b.jpg"],
            ["public/common/c.jpg"]]
    recs = generate("金星村", 2, image_sets=sets)
    assert recs[0].image_keys == sets[0]
    assert recs[1].image_keys == sets[1]
    # distinct between the two records
    assert recs[0].image_keys != recs[1].image_keys


def test_generate_no_image_sets_leaves_keys_empty():
    recs = generate("金星村", 2)
    assert all(r.image_keys == [] for r in recs)


def test_generate_caps_at_pool_size():
    recs = generate("X", 100)
    assert len(recs) == len(set(r.content for r in recs))  # no duplicates
