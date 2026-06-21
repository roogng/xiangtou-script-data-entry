# llm_client.py
"""OpenAI-compatible chat completions client (config-driven provider).

Currently targets Tencent LKEAP (MiniMax 2.7). The endpoint URL, model, and key
all come from config so switching providers is a config-only change.
"""
import time
import httpx


class LLMClient:
    def __init__(self, api_key, model, url, rpm, max_retries, timeout):
        self._api_key = api_key
        self._model = model
        self._url = url  # full chat/completions endpoint URL
        self._min_interval = 60.0 / rpm if rpm else 0
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_call = 0.0

    @classmethod
    def from_config(cls, cfg):
        c = cfg["llm"]
        return cls(api_key=c["api_key"], model=c["model"], url=c["url"],
                   rpm=int(c["rpm"]), max_retries=int(c["max_retries"]),
                   timeout=int(c["timeout"]))

    def ask(self, question: str) -> str:
        self._throttle()
        last_err = None
        for attempt in range(self._max_retries + 1):
            try:
                r = httpx.post(self._url,
                               headers={"Authorization": f"Bearer {self._api_key}",
                                        "Content-Type": "application/json"},
                               json={"model": self._model,
                                     "messages": [{"role": "user", "content": question}]},
                               timeout=self._timeout)
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"] or ""
            except Exception as e:  # transient: network / rate / 5xx
                last_err = e
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)
        raise last_err

    def _throttle(self):
        if self._min_interval:
            elapsed = time.time() - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()
