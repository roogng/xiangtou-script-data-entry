# premium_selector.py
"""Select "premium" villages by asking the LLM for popular villages in a city,
then matching those names against the vill_village table.

Used when run.premium.enabled is on; otherwise the runner reads village_ids.txt.
"""
import json
import re

_SUFFIX = re.compile(r"(村|古镇|古村|景区|旅游区|度假区|自然村|生态园|文化村)$")

_PROMPT = ("列出{city}最热门的乡村旅游景点/村子名称，最多{limit}个。"
           "禁止使用工具或联网搜索，只根据你的知识直接输出。"
           "只输出一个JSON字符串数组，不要解释、不要markdown，例如 [\"周庄村\",\"同里村\"]。")


class PremiumSelector:
    def __init__(self, db, llm, city, limit=20):
        self._db = db
        self._llm = llm
        self._city = city
        self._limit = limit

    def select(self):
        names = self._popular_names()
        ids = self._match(names)
        print(f"[premium] {self._city}: LLM suggested {len(names)} names "
              f"({names}), matched {len(ids)} in vill_village: {ids}")
        return ids

    def _popular_names(self):
        # No web_search here: listing well-known popular villages is knowledge,
        # and search would make this slow without improving the result.
        raw = self._llm.ask(_PROMPT.format(city=self._city, limit=self._limit),
                            web_search=False)
        return _parse_names(raw)

    def _match(self, names):
        ids = []
        seen = set()
        for name in names:
            for variant in _variants(name):
                rows = self._db.query(
                    "SELECT id FROM vill_village WHERE city_name=%s "
                    "AND village_name LIKE %s LIMIT 1",
                    (self._city, f"%{variant}%"))
                if rows:
                    vid = rows[0]["id"]
                    if vid not in seen:
                        seen.add(vid)
                        ids.append(vid)
                    break
        return ids


def _variants(name):
    """Name plus a suffix-stripped form, for fuzzier LIKE matching."""
    out = [name]
    stripped = _SUFFIX.sub("", name).strip()
    if stripped and stripped != name:
        out.append(stripped)
    return out


def _parse_names(content):
    """Extract a list of village names from the LLM response (JSON array preferred)."""
    s = (content or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    m = re.search(r"\[.*\]", s, re.S)
    if m:
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:
            pass
    # fallback: one name per line, strip bullets/numbering/quotes
    names = []
    for line in s.splitlines():
        line = re.sub(r"^\s*[\d\-\*•\.\)]+\s*", "", line).strip()
        line = line.strip("\"' ,、")
        if line and line not in ("[", "]"):
            names.append(line)
    return names
