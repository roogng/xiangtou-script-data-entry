# image_search.py
"""Fallback image search when Kimi returns no usable images.

Pixabay first (Pixabay License — free to use, no attribution, no watermark),
then Pexels (Pexels License — free to use, no attribution). Both are reachable
from China. Returns one direct image URL, or None.
"""
import httpx

PIXABAY_URL = "https://pixabay.com/api/"
PEXELS_URL = "https://api.pexels.com/v1/search"


class ImageSearcher:
    def __init__(self, pixabay_key: str = "", pexels_key: str = "", timeout: float = 15.0):
        self._pixabay_key = pixabay_key
        self._pexels_key = pexels_key
        self._timeout = timeout

    def search(self, keyword: str):
        """Return one image URL for the keyword, or None if no source has one."""
        if not keyword:
            return None
        url = self._pixabay(keyword)
        if url:
            return url
        return self._pexels(keyword)

    def _pixabay(self, keyword: str):
        if not self._pixabay_key:
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

    def _pexels(self, keyword: str):
        if not self._pexels_key:
            return None
        try:
            r = httpx.get(PEXELS_URL, params={"query": keyword, "per_page": 1},
                          headers={"Authorization": self._pexels_key},
                          timeout=self._timeout)
            r.raise_for_status()
            photos = (r.json().get("photos") or [])
            if photos:
                return photos[0].get("src", {}).get("large")
        except Exception as e:
            print(f"[warn] pexels search failed: {e}")
        return None
