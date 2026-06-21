# image_search.py
"""Fallback image search when Kimi returns no usable images.

Pixabay (Pixabay License — free to use, no attribution, no watermark), reachable
from China. Returns one direct image URL, or None.
"""
import httpx

PIXABAY_URL = "https://pixabay.com/api/"


class ImageSearcher:
    def __init__(self, pixabay_key: str = "", timeout: float = 15.0):
        self._pixabay_key = pixabay_key
        self._timeout = timeout

    def search(self, keyword: str):
        """Return one image URL for the keyword, or None if no result."""
        if not keyword or not self._pixabay_key:
            return None
        params = {"key": self._pixabay_key, "q": keyword, "lang": "zh",
                  "image_type": "photo", "per_page": 3, "safesearch": "true"}
        try:
            r = httpx.get(PIXABAY_URL, params=params, timeout=self._timeout)
            r.raise_for_status()
            hits = (r.json().get("hits") or [])
            if hits:
                return hits[0].get("largeImageURL")
        except Exception as e:
            print(f"[warn] pixabay search failed: {e}")
        return None
