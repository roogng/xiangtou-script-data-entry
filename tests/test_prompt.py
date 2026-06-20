# tests/test_prompt.py
from prompt import build_question


def test_question_contains_full_place_name():
    q = build_question(province="四川省", city="成都市", area="大邑县",
                       street="安仁镇", village="金星村")
    assert "四川省成都市大邑县安仁镇金星村" in q
    assert "basic_info" in q
    assert "rooms" in q
    assert "dishes" in q
    assert "days" in q
    assert "trips" in q
