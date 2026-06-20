# kimi_client.py
import time
from openai import OpenAI


class KimiClient:
    def __init__(self, api_key, model, rpm, max_retries, timeout):
        self._client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
        self._model = model
        self._min_interval = 60.0 / rpm if rpm else 0
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_call = 0.0

    @classmethod
    def from_config(cls, cfg):
        m = cfg["moonshot"]
        return cls(api_key=m["api_key"], model=m["model"], rpm=int(m["rpm"]),
                   max_retries=int(m["max_retries"]), timeout=int(m["timeout"]))

    def ask(self, question: str) -> str:
        self._throttle()
        last_err = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": question}],
                    timeout=self._timeout,
                )
                return resp.choices[0].message.content or ""
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
