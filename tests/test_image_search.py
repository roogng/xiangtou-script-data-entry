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


def test_pixabay_empty_falls_back_to_pexels():
    s = ImageSearcher(pixabay_key="pk", pexels_key="pxk")
    pb = _resp({"hits": []})
    px = _resp({"photos": [{"src": {"large": "https://p/x.jpg"}}]})
    with patch("image_search.httpx.get", side_effect=[pb, px]) as g:
        assert s.search("景区 x") == "https://p/x.jpg"
    # pexels call carries the authorization header
    pexels_kwargs = g.call_args_list[1].kwargs
    assert pexels_kwargs["headers"]["Authorization"] == "pxk"


def test_both_empty_returns_none():
    s = ImageSearcher(pixabay_key="pk", pexels_key="pxk")
    pb = _resp({"hits": []})
    px = _resp({"photos": []})
    with patch("image_search.httpx.get", side_effect=[pb, px]):
        assert s.search("whatever") is None


def test_pixabay_error_falls_back_to_pexels():
    s = ImageSearcher(pixabay_key="pk", pexels_key="pxk")
    pb = MagicMock(); pb.raise_for_status.side_effect = Exception("net")
    px = _resp({"photos": [{"src": {"large": "https://p/f.jpg"}}]})
    with patch("image_search.httpx.get", side_effect=[pb, px]):
        assert s.search("k") == "https://p/f.jpg"


def test_missing_keys_skips_search():
    # no keys configured -> search returns None without calling out
    s = ImageSearcher()
    with patch("image_search.httpx.get") as g:
        assert s.search("k") is None
        g.assert_not_called()


def test_empty_keyword_returns_none_without_call():
    s = ImageSearcher(pixabay_key="pk")
    with patch("image_search.httpx.get") as g:
        assert s.search("") is None
        g.assert_not_called()
