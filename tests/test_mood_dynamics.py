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


def test_generate_caps_at_pool_size():
    recs = generate("X", 100)
    assert len(recs) == len(set(r.content for r in recs))  # no duplicates
