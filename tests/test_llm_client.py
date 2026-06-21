# tests/test_llm_client.py
import pytest
from unittest.mock import patch, MagicMock
from llm_client import LLMClient


def _resp(content):
    r = MagicMock()
    r.json.return_value = {"choices": [{"message": {"content": content}}]}
    r.raise_for_status.return_value = None
    return r


def test_ask_returns_content_text():
    with patch("llm_client.httpx.post", return_value=_resp('{"minsu":[]}')) as p:
        c = LLMClient(api_key="x", model="m", url="http://u/chat/completions",
                      rpm=600, max_retries=3, timeout=10)
        assert c.ask("hi") == '{"minsu":[]}'
        _, kwargs = p.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer x"
        assert kwargs["json"]["model"] == "m"
        assert kwargs["json"]["messages"] == [{"role": "user", "content": "hi"}]


def test_ask_retries_on_transient_then_succeeds():
    with patch("llm_client.httpx.post") as p:
        p.side_effect = [RuntimeError("timeout"), RuntimeError("timeout"), _resp('{"minsu":[]}')]
        c = LLMClient(api_key="x", model="m", url="http://u", rpm=60000,
                      max_retries=3, timeout=10)
        with patch("llm_client.time.sleep"):
            assert c.ask("hi") == '{"minsu":[]}'
        assert p.call_count == 3


def test_ask_gives_up_after_max_retries():
    with patch("llm_client.httpx.post") as p:
        p.side_effect = RuntimeError("boom")
        c = LLMClient(api_key="x", model="m", url="http://u", rpm=60000,
                      max_retries=2, timeout=10)
        with patch("llm_client.time.sleep"):
            with pytest.raises(RuntimeError):
                c.ask("hi")
        assert p.call_count == 3  # 1 + 2 retries
