# tests/test_image_search.py
from unittest.mock import patch, MagicMock
from image_search import ImageSearcher


def _resp(payload):
    r = MagicMock()
    r.json.return_value = payload
    return r


def test_pixabay_hit_returns_large_image_url():
    s = ImageSearcher(pixabay_key="pk")
    payload = {"hits": [{"largeImageURL": "https://cdn/a.jpg"}]}
    with patch("image_search.httpx.get", return_value=_resp(payload)) as g:
        assert s.search("民宿 t") == "https://cdn/a.jpg"
    _, kwargs = g.call_args
    assert kwargs["params"]["key"] == "pk"
    assert kwargs["params"]["lang"] == "zh"


def test_pixabay_empty_returns_none():
    s = ImageSearcher(pixabay_key="pk")
    with patch("image_search.httpx.get", return_value=_resp({"hits": []})):
        assert s.search("whatever") is None


def test_pixabay_error_returns_none():
    s = ImageSearcher(pixabay_key="pk")
    bad = MagicMock(); bad.raise_for_status.side_effect = Exception("net")
    with patch("image_search.httpx.get", return_value=bad):
        assert s.search("k") is None


def test_missing_key_skips_search():
    s = ImageSearcher()
    with patch("image_search.httpx.get") as g:
        assert s.search("k") is None
        g.assert_not_called()


def test_empty_keyword_returns_none_without_call():
    s = ImageSearcher(pixabay_key="pk")
    with patch("image_search.httpx.get") as g:
        assert s.search("") is None
        g.assert_not_called()
