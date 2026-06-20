# tests/test_parser.py
import os
from parser import parse

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "sample_response.json")


def _load():
    with open(FIX, encoding="utf-8") as f:
        return f.read()


def test_parse_full_structure():
    data = parse(_load())
    assert len(data.minsu) == 1
    m = data.minsu[0]
    assert m.title == "民宿A"
    assert m.lng == 120.1
    assert len(m.images) == 1 and m.images[0].url == "http://img/c.jpg"
    assert len(m.rooms) == 1
    assert m.rooms[0].room_type == 2


def test_parse_sages_type_mapping():
    data = parse(_load())
    assert data.sages[0].sages_type == 2  # xiangxian -> 2


def test_parse_specialty_category():
    data = parse(_load())
    assert data.specialty[0].category == "炒货"


def test_parse_activity_nested_days_trips():
    data = parse(_load())
    a = data.activity[0]
    assert len(a.days) == 1
    assert a.days[0].trips[0].trip_name == "行程1"


def test_parse_strips_markdown_fence():
    raw = "```json\n" + _load() + "\n```"
    data = parse(raw)
    assert len(data.scenic) == 1


def test_parse_skips_record_missing_required_name():
    raw = '{"minsu": [{"intro":"无标题"}]}'  # title empty -> skipped
    data = parse(raw)
    assert data.minsu == []


def test_parse_empty_arrays_ok():
    data = parse('{"minsu":[]}')
    assert data.minsu == []
