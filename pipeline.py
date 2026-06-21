# pipeline.py
import random
from writers.base import BaseWriter
from writers.tables import TABLE_CONFIGS
from parser import parse
import mood_dynamics
import homestay_rooms

# Overwrite cleanup. Child tables lacking village_id are deleted via subquery on
# their parent's id. Order is child-first. All run inside the pipeline transaction
# so a failure rolls the deletes back too (no data loss on transient errors).
_DELETE_SQLS = [
    "DELETE FROM vill_homestay_room WHERE homestay_id IN (SELECT id FROM vill_homestay WHERE village_id=%s)",
    "DELETE FROM vill_homestay WHERE village_id=%s",
    "DELETE FROM vill_restaurant_dish WHERE restaurant_id IN (SELECT id FROM vill_restaurant WHERE village_id=%s)",
    "DELETE FROM vill_restaurant WHERE village_id=%s",
    "DELETE FROM vill_village_activity_trip WHERE day_id IN (SELECT id FROM vill_village_activity_day WHERE activity_id IN (SELECT id FROM vill_village_activity WHERE village_id=%s))",
    "DELETE FROM vill_village_activity_day WHERE activity_id IN (SELECT id FROM vill_village_activity WHERE village_id=%s)",
    "DELETE FROM vill_village_activity WHERE village_id=%s",
    "DELETE FROM vill_village_travel WHERE village_id=%s",
    "DELETE FROM vill_dynamics WHERE village_id=%s",
    "DELETE FROM vill_goods WHERE village_id=%s",
    "DELETE FROM vill_village_sages WHERE village_id=%s",
    "DELETE FROM vill_attraction WHERE village_id=%s",
]


class Pipeline:
    def __init__(self, db, llm, uploader, file_repo, defaults, category_repo,
                 goods_category_fallback=0, image_searcher=None, parse_retries=2):
        self._db = db
        self._llm = llm
        self._uploader = uploader
        self._file_repo = file_repo
        self._defaults = defaults
        self._category_repo = category_repo
        self._fallback = goods_category_fallback
        self._searcher = image_searcher
        self._parse_retries = parse_retries

    def run(self, village: dict, question: str, overwrite: bool = False):
        # The LLM's JSON is non-deterministic and occasionally malformed/truncated;
        # re-asking usually yields valid JSON. Retry before giving up.
        data = None
        raw = ""
        last_err = None
        for attempt in range(self._parse_retries + 1):
            raw = self._llm.ask(question)
            try:
                data = parse(raw)
                break
            except Exception as e:
                last_err = e
                if attempt < self._parse_retries:
                    print(f"[warn] parse attempt {attempt + 1}/{self._parse_retries + 1} failed, retrying: {e}")
        if data is None:
            self._db.rollback()
            raise RuntimeError(f"parse failed after {self._parse_retries + 1} attempts: {last_err}")

        # If the LLM gave no dynamics (vill_dynamics), fill 2 mood-dynamic records
        # so the village always has some "心情动态" content.
        self._fill_news(data, village)

        # If a homestay has no rooms (vill_homestay_room), fill 2 random rooms so
        # every homestay has some room data.
        for rec in data.minsu:
            if not rec.rooms:
                rec.rooms = homestay_rooms.generate(2)

        cache = {}
        search_cache = {}  # keyword -> file_key (or "" if search/upload failed)
        db_cache = {}      # "table.column" -> [existing comma-joined image values]

        def resolve(refs, keyword=None, table=None, column=None):
            keys = []
            for ref in refs:
                if not ref.url:
                    continue
                if ref.url in cache:
                    if cache[ref.url]:
                        keys.append(cache[ref.url])
                    continue
                file_key, size = self._uploader.upload_url(ref.url)
                if not file_key:
                    cache[ref.url] = ""  # cache the failure so we don't retry/warn repeatedly
                    print(f"[warn] image upload failed, skipped: {ref.url}")
                    continue
                self._file_repo.insert(file_key=file_key,
                                       file_name=ref.url.split("/")[-1] or "image",
                                       file_size=size, file_type="jpg")
                cache[ref.url] = file_key
                keys.append(file_key)
            # Fallback 1: no usable image (LLM gave none, or all uploads failed).
            # Search the web by keyword and upload the first hit.
            if not keys and keyword and self._searcher is not None:
                if keyword in search_cache:
                    if search_cache[keyword]:
                        keys = [search_cache[keyword]]
                else:
                    url = self._searcher.search(keyword)
                    if not url:
                        search_cache[keyword] = ""
                        print(f"[warn] image search found nothing: {keyword}")
                    else:
                        file_key, size = self._uploader.upload_url(url)
                        if not file_key:
                            search_cache[keyword] = ""
                            print(f"[warn] searched image upload failed: {url}")
                        else:
                            self._file_repo.insert(file_key=file_key,
                                                   file_name=url.split("/")[-1] or "image",
                                                   file_size=size, file_type="jpg")
                            cache[url] = file_key
                            search_cache[keyword] = file_key
                            keys = [file_key]
            # Fallback 2: web search also empty -> reuse an existing image value
            # from the same table/column (random pick of recent non-empty rows).
            if not keys and table and column:
                ck = f"{table}.{column}"
                vals = db_cache.get(ck)
                if vals is None:
                    rows = self._db.query(
                        f"SELECT {column} AS v FROM {table} "
                        f"WHERE {column} IS NOT NULL AND {column} != '' "
                        f"ORDER BY id DESC LIMIT 50")
                    vals = [r["v"] for r in rows] if rows else []
                    db_cache[ck] = vals
                if vals:
                    keys = (random.choice(vals) or "").split(",")
            return keys

        vid = village["id"]
        total = 0
        try:
            if overwrite:
                for sql in _DELETE_SQLS:
                    self._db.execute(sql, (vid,))
            for category, cfg in TABLE_CONFIGS.items():
                records = getattr(data, category, [])
                if not records:
                    continue
                if category == "specialty":
                    records = self._resolve_specialty_categories(records)
                    if not records:
                        continue
                writer = BaseWriter(self._db, cfg, resolve, village, dict(self._defaults))
                total += writer.write(records)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return total, raw

    def _fill_news(self, data, village):
        """Generate 2 mood-dynamic records when the LLM gave none, each reusing a
        distinct existing image from vill_dynamics so they don't duplicate."""
        if data.news:
            return
        image_sets = self._dynamics_image_sets(2)
        data.news = mood_dynamics.generate(village.get("village_name", ""), 2,
                                           image_sets=image_sets)

    def _dynamics_image_sets(self, n):
        """Return up to n distinct file_key lists from existing vill_dynamics rows,
        so generated mood-dynamic records can reuse real images (distinct per record)."""
        rows = self._db.query(
            "SELECT img_url FROM vill_dynamics "
            "WHERE img_url IS NOT NULL AND img_url != '' ORDER BY id DESC LIMIT 50")
        seen = set()
        out = []
        for r in rows:
            u = r["img_url"]
            if not u or u in seen:
                continue
            seen.add(u)
            keys = [k for k in u.split(",") if k]
            if keys:
                out.append(keys)
            if len(out) >= n:
                break
        return out

    def _resolve_specialty_categories(self, records):
        """Set category_id on each goods record from its LLM-returned sub-category
        name via t_category (parent_id > 0). Records that can't be matched and have
        no fallback are skipped (vill_goods.category_id is NOT NULL)."""
        out = []
        for rec in records:
            cid = self._category_repo.get(rec.category) or self._fallback
            if cid:
                rec.category_id = cid
                out.append(rec)
        return out
