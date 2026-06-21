# llm_client.py
"""OpenAI-compatible chat completions client (config-driven provider).

Currently targets GLM-5.1 with built-in web search. The endpoint URL, model,
key, and web_search flag all come from config so switching providers is a
config-only change.
"""
import time
import httpx


class LLMClient:
    def __init__(self, api_key, model, url, rpm, max_retries, timeout,
                 web_search=False, json_mode=False):
        self._api_key = api_key
        self._model = model
        self._url = url  # full chat/completions endpoint URL
        self._min_interval = 60.0 / rpm if rpm else 0
        self._max_retries = max_retries
        self._timeout = timeout
        self._web_search = web_search
        self._json_mode = json_mode
        self._last_call = 0.0

    @classmethod
    def from_config(cls, cfg):
        c = cfg["llm"]
        return cls(api_key=c["api_key"], model=c["model"], url=c["url"],
                   rpm=int(c["rpm"]), max_retries=int(c["max_retries"]),
                   timeout=int(c["timeout"]),
                   web_search=bool(c.get("web_search", False)),
                   json_mode=bool(c.get("json_mode", False)))

    def ask(self, question: str, web_search=None) -> str:
        """Call the LLM. web_search overrides the config default (e.g. False for
        the premium-village selection, which only lists known popular villages)."""
        if web_search is None:
            web_search = self._web_search
        self._throttle()
        last_err = None
        for attempt in range(self._max_retries + 1):
            try:
                body = {"model": self._model,
                        "messages": [{"role": "user", "content": question}]}
                if web_search:
                    # GLM built-in web search (platform-side, not agentic)
                    body["tools"] = [{"type": "web_search",
                                      "web_search": {"enable": True}}]
                if self._json_mode:
                    # force valid JSON (escapes quotes etc. inside string values)
                    body["response_format"] = {"type": "json_object"}
                r = httpx.post(self._url,
                               headers={"Authorization": f"Bearer {self._api_key}",
                                        "Content-Type": "application/json"},
                               json=body, timeout=self._timeout)
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
