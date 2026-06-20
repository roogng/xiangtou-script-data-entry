# tests/test_kimi_client.py
import pytest
from unittest.mock import patch, MagicMock
from kimi_client import KimiClient


def test_ask_returns_content_text():
    with patch("kimi_client.OpenAI") as MockOpenAI:
        client_inst = MagicMock()
        MockOpenAI.return_value = client_inst
        msg = MagicMock()
        msg.choices = [MagicMock(message=MagicMock(content='{"minsu":[]}'))]
        client_inst.chat.completions.create.return_value = msg
        kc = KimiClient(api_key="x", model="moonshot-v1-auto", rpm=600, max_retries=3, timeout=10)
        text = kc.ask("hi")
        assert text == '{"minsu":[]}'


def test_ask_retries_on_transient_then_succeeds():
    with patch("kimi_client.OpenAI") as MockOpenAI:
        client_inst = MagicMock()
        MockOpenAI.return_value = client_inst
        msg = MagicMock()
        msg.choices = [MagicMock(message=MagicMock(content='{"minsu":[]}'))]
        client_inst.chat.completions.create.side_effect = [
            RuntimeError("timeout"), RuntimeError("timeout"), msg
        ]
        kc = KimiClient(api_key="x", model="moonshot-v1-auto", rpm=60000, max_retries=3, timeout=10)
        with patch("kimi_client.time.sleep"):
            text = kc.ask("hi")
        assert text == '{"minsu":[]}'
        assert client_inst.chat.completions.create.call_count == 3


def test_ask_gives_up_after_max_retries():
    with patch("kimi_client.OpenAI") as MockOpenAI:
        client_inst = MagicMock()
        MockOpenAI.return_value = client_inst
        client_inst.chat.completions.create.side_effect = RuntimeError("boom")
        kc = KimiClient(api_key="x", model="moonshot-v1-auto", rpm=60000, max_retries=2, timeout=10)
        with patch("kimi_client.time.sleep"):
            with pytest.raises(RuntimeError):
                kc.ask("hi")
        assert client_inst.chat.completions.create.call_count == 3  # 1 + 2 retries
