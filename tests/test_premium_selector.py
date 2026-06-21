# tests/test_premium_selector.py
from unittest.mock import MagicMock
from premium_selector import PremiumSelector, _parse_names, _variants


def test_parse_names_json_array():
    assert _parse_names('["周庄村","同里村"]') == ["周庄村", "同里村"]


def test_parse_names_fenced_json():
    s = "```json\n[\"周庄\", \"同里\"]\n```"
    assert _parse_names(s) == ["周庄", "同里"]


def test_parse_names_fallback_lines():
    s = "1. 周庄村\n2. 同里村\n3. 陆巷村"
    assert _parse_names(s) == ["周庄村", "同里村", "陆巷村"]


def test_variants_strips_suffix():
    v = _variants("周庄古镇")
    assert "周庄古镇" in v and "周庄" in v


def test_select_matches_names_to_village_ids():
    db = MagicMock()
    # first name matches on raw variant; second needs suffix stripping
    db.query.side_effect = [
        [{"id": 100}],   # 周庄村 -> 100
        [],              # 同里古镇 raw -> no match
        [{"id": 200}],   # 同里古镇 stripped -> 同里 -> 200
    ]
    llm = MagicMock()
    llm.ask.return_value = '["周庄村","同里古镇"]'
    sel = PremiumSelector(db, llm, "苏州市", limit=20)
    ids = sel.select()
    assert ids == [100, 200]
    # queried with city and LIKE pattern (params passed as a tuple)
    args0 = db.query.call_args_list[0].args
    assert args0[1] == ("苏州市", "%周庄村%")


def test_select_dedups_ids():
    db = MagicMock()
    db.query.side_effect = [
        [{"id": 100}],   # 周庄村
        [{"id": 100}],   # 周庄 -> same village
    ]
    llm = MagicMock()
    llm.ask.return_value = '["周庄村","周庄"]'
    sel = PremiumSelector(db, llm, "苏州市", limit=20)
    assert sel.select() == [100]


def test_select_no_matches_returns_empty():
    db = MagicMock()
    db.query.return_value = []
    llm = MagicMock()
    llm.ask.return_value = '["不存在村"]'
    sel = PremiumSelector(db, llm, "苏州市", limit=20)
    assert sel.select() == []
