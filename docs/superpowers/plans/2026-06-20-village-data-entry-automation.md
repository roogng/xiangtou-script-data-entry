# 乡村数据自动化录入系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python pipeline that reads premium villages from MySQL, asks Kimi (Moonshot) for 9 categories of village data, uploads returned images to Qiniu, and writes structured records (with sub-tables) back into the same MySQL database — resumable, idempotent, single-machine.

**Architecture:** Single-process linear pipeline per village, driven by a `task_status` table for resume/idempotency. A generic `BaseWriter` + per-table config handles all 9 tables (one UPDATE for basic_info, INSERTs for the rest) plus 4 sub-tables, applying per-table explicit default columns. Images go through download → Pillow compress (>1MB) → Qiniu upload → `t_file` insert → file_key joined into business-table text fields.

**Tech Stack:** Python 3.11, pymysql, openai SDK (Moonshot-compatible), qiniu SDK, Pillow, pyyaml, pytest.

**Spec:** `docs/superpowers/specs/2026-06-20-village-data-entry-automation-design.md`

---

## Field Mapping Reference (from DDLs in `sql/`)

### Default values (the user-confirmed uniform set)
`create_user_id=43`, `update_user_id=43`, `approve_status=2`, `approve_id=43`, `online=1`, `comment_code=uuid4().hex`, `homeowner_id=4`, `shop_id=2`, `member_id=43`, `deleted_flag=0`. `create_time`/`update_time` use DB defaults. Goods-only: `goods_status=2`, `category_id=<config run.goods_category_id>`.

**Important:** Not every table has every column (e.g. `vill_village` has no `comment_code`/`online`/`member_id`; `vill_homestay` has no `member_id`; sub-tables differ again). Each `TableConfig` therefore declares an explicit `uniform_columns` list and `has_comment_code` flag — the writer only emits columns the table actually has.

### GPS write modes
- **point** (`vill_homestay.location`, `vill_restaurant.location_point`, `vill_attraction.location_point`): `ST_GeomFromText('POINT({lng} {lat})')`.
- **decimal** (`vill_dynamics.latitude/longitude`, `vill_village_activity.latitude/longitude`, `vill_village_travel.latitude/longitude`): plain values.
- **none**: basic_info, sages, specialty.

### Source village row (read from `vill_village`)
Provides `id, village_name, province_id, province_name, city_id, city_name, area_id, area_name, street_id, street_name, address, lng, lat` (`lng`/`lat` are generated but selectable). Used to (a) build the Kimi question, (b) propagate address fields into homestay/restaurant/attraction (only those tables have the address columns), (c) GPS fallback.

### Category → table field maps
| Category (JSON key) | Table | Write | Kimi field → column |
|---|---|---|---|
| basic_info | vill_village | UPDATE | secretary_intro→head_introduction, contact_phone→contact_phone, village_intro→introduce, head_name→head_name, images→entire_cover_img |
| sages | vill_village_sages | INSERT | type→sages_type(xiangxian=2,xianxian=1), name→sages_name, intro→context, images→img_url |
| minsu | vill_homestay + vill_homestay_room | INSERT | title→title, intro→introduce, images→cover_img; rooms: room_name,room_type,intro,price→week_day_price, images→cover_img |
| specialty | vill_goods | INSERT | name→goods_name, price→price, detail→introduce, images→goods_imgs |
| news | vill_dynamics | INSERT | content→context, images→img_url |
| activity | vill_village_activity + _day + _trip | INSERT | name→activity_name, intro→introduce, images→activity_imgs; days: day_name,intro,images→travel_day_imgs; trips: trip_name,trip_time,intro→introduce |
| route | vill_village_travel | INSERT | name→travel_name, intro→introduce, images→travel_imgs |
| farmhouse | vill_restaurant + vill_restaurant_dish | INSERT | name→restaurant_name, intro→introduction, images→cover_img; dishes: dish_name,price→unit_price,intro→introduction, images→cover_img |
| scenic | vill_attraction | INSERT | name→attraction_name, intro→introduction, images→cover_img |

---

## Task 1: Project setup (config, requirements, gitignore)

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml.example`
- Create: `.gitignore`
- Create: `config_loader.py`

- [ ] **Step 1: Create requirements.txt**

```
pymysql==1.1.1
openai==1.40.0
qiniu==7.14.0
Pillow==10.4.0
PyYAML==6.0.2
pytest==8.3.2
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
config.yaml
village_ids.txt
.pytest_cache/
```

- [ ] **Step 3: Create config.yaml.example**

```yaml
mysql:
  host: 127.0.0.1
  port: 3306
  user: root
  password: ""
  database: vill
moonshot:
  api_key: "sk-..."
  model: moonshot-v1-auto
  rpm: 60
  max_retries: 3
  timeout: 120
qiniu:
  access_key: "..."
  secret_key: "..."
  bucket: "..."
  domain: "https://example.com"
  image_path_template: "public/common/{uuid}.jpg"
  max_size_bytes: 1048576
run:
  concurrency: 1
  village_ids_file: village_ids.txt
  overwrite: true
  goods_category_id: 0   # TBD: user to fill real category id before full run
```

- [ ] **Step 4: Create config_loader.py**

```python
import yaml
from dataclasses import dataclass


@dataclass
class Config:
    raw: dict

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    def __getitem__(self, key: str):
        return self.raw[key]
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore config.yaml.example config_loader.py
git commit -m "chore: project setup, config, requirements"
```

---

## Task 2: db.py — MySQL connection wrapper

**Files:**
- Create: `db.py`
- Test: `tests/test_db.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db.py
from unittest.mock import MagicMock
from db import MySQL


def test_execute_returns_lastrowid():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.lastrowid = 42
    db = MySQL(conn)
    rowid = db.execute("INSERT INTO t (a) VALUES (%s)", (1,))
    cursor.execute.assert_called_once_with("INSERT INTO t (a) VALUES (%s)", (1,))
    assert rowid == 42


def test_query_returns_rows():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchall.return_value = [{"village_id": 1}]
    db = MySQL(conn)
    rows = db.query("SELECT village_id FROM task_status WHERE status='done'")
    assert rows == [{"village_id": 1}]


def test_query_one_returns_single():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = {"id": 7}
    db = MySQL(conn)
    row = db.query_one("SELECT * FROM vill_village WHERE id=%s", (7,))
    assert row == {"id": 7}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL (module `db` not found)

- [ ] **Step 3: Implement db.py**

```python
# db.py
import pymysql
from config_loader import Config
from pymysql.cursors import DictCursor


class MySQL:
    def __init__(self, conn):
        self._conn = conn

    @classmethod
    def from_config(cls, cfg: Config):
        m = cfg["mysql"]
        conn = pymysql.connect(
            host=m["host"], port=int(m["port"]), user=m["user"],
            password=m["password"], database=m["database"],
            charset="utf8mb4", autocommit=False, cursorclass=DictCursor,
        )
        return cls(conn)

    def execute(self, sql, args=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.lastrowid

    def query(self, sql, args=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def query_one(self, sql, args=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: MySQL connection wrapper"
```

---

## Task 3: models.py — parsed data dataclasses

**Files:**
- Create: `models.py`

- [ ] **Step 1: Create models.py**

```python
# models.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ImageRef:
    url: str           # original URL from Kimi
    file_key: str = "" # set after Qiniu upload


@dataclass
class Room:
    room_name: str = ""
    room_type: int = 1
    intro: str = ""
    price: Optional[float] = None
    images: List[ImageRef] = field(default_factory=list)


@dataclass
class Dish:
    dish_name: str = ""
    price: Optional[float] = None
    intro: str = ""
    images: List[ImageRef] = field(default_factory=list)


@dataclass
class Trip:
    trip_name: str = ""
    trip_time: str = ""
    intro: str = ""


@dataclass
class Day:
    day_name: str = ""
    intro: str = ""
    images: List[ImageRef] = field(default_factory=list)
    trips: List[Trip] = field(default_factory=list)


@dataclass
class Record:
    """One business record across categories. Only relevant fields filled."""
    name: str = ""
    title: str = ""
    intro: str = ""
    content: str = ""
    price: Optional[float] = None
    detail: str = ""
    head_name: str = ""
    secretary_intro: str = ""
    contact_phone: str = ""
    village_intro: str = ""
    sages_type: int = 0         # 2=乡贤(在世) 1=先贤(已故)
    lng: Optional[float] = None
    lat: Optional[float] = None
    images: List[ImageRef] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    dishes: List[Dish] = field(default_factory=list)
    days: List[Day] = field(default_factory=list)


@dataclass
class VillageData:
    """All parsed data for one village."""
    basic_info: List[Record] = field(default_factory=list)
    sages: List[Record] = field(default_factory=list)
    minsu: List[Record] = field(default_factory=list)
    specialty: List[Record] = field(default_factory=list)
    news: List[Record] = field(default_factory=list)
    activity: List[Record] = field(default_factory=list)
    route: List[Record] = field(default_factory=list)
    farmhouse: List[Record] = field(default_factory=list)
    scenic: List[Record] = field(default_factory=list)
```

- [ ] **Step 2: Commit**

```bash
git add models.py
git commit -m "feat: dataclasses for parsed village data"
```

---

## Task 4: prompt.py — build Kimi question

**Files:**
- Create: `prompt.py`
- Test: `tests/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompt.py
from prompt import build_question


def test_question_contains_full_place_name():
    q = build_question(province="四川省", city="成都市", area="大邑县",
                       street="安仁镇", village="金星村")
    assert "四川省成都市大邑县安仁镇金星村" in q
    assert "basic_info" in q
    assert "rooms" in q
    assert "dishes" in q
    assert "days" in q
    assert "trips" in q
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement prompt.py**

```python
# prompt.py
_TEMPLATE = """请联网搜索「{place}」的以下乡村信息，并严格按照给定JSON格式返回。
每条信息附带图片URL；有坐标则返回经纬度，没有则省略坐标字段。
基本信息返回1条；其余每类最多3条，找不到返回空数组 []，不要编造。

返回JSON结构：
{{
  "basic_info": [{{"head_name":"村书记姓名","secretary_intro":"村书记介绍","contact_phone":"公开联系电话","village_intro":"村介绍","images":["http://..."]}}],
  "sages": [{{"type":"xiangxian","name":"姓名","intro":"介绍","images":[...]}}]],
  "minsu": [{{"title":"标题","intro":"介绍","images":[...],"lng":..,"lat":..,"rooms":[{{"room_name":"房号","room_type":1,"intro":"房型简介","price":..,"images":[...]}}]}}],
  "specialty": [{{"name":"商品名","price":数字,"detail":"详情介绍","images":[...]}}],
  "news": [{{"content":"动态完整内容","images":[...],"lng":..,"lat":..}}],
  "activity": [{{"name":"活动名称","intro":"活动介绍","images":[...],"lng":..,"lat":..,"days":[{{"day_name":"第一天","intro":"日程介绍","images":[...],"trips":[{{"trip_name":"行程名","trip_time":"行程时间","intro":"行程介绍"}}]}}]}}],
  "route": [{{"name":"路线名","intro":"路线介绍","images":[...],"lng":..,"lat":..}}],
  "farmhouse": [{{"name":"农庄名","intro":"农庄介绍","images":[...],"lng":..,"lat":..,"dishes":[{{"dish_name":"菜品名","price":..,"intro":"菜品简介","images":[...]}}]}}],
  "scenic": [{{"name":"景区名","intro":"景区介绍","images":[...],"lng":..,"lat":..}}]
}}
规则：
- 每类只返回本村范围内的真实信息，找不到就 []
- price 必须是纯数字
- images 是图片URL数组，没有图片就 []
- 坐标找不到就不写 lng/lat 字段
- sages 的 type：xiangxian=乡贤(在世)，xianxian=先贤(已故)，各最多1条
- room_type：1大床房 2双人房 3亲子房 4套房 5VIP房，不确定填1
- rooms/dishes/days/trips 找不到就 []
"""


def build_question(province, city, area, street, village):
    place = f"{province}{city}{area}{street}{village}"
    return _TEMPLATE.format(place=place)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add prompt.py tests/test_prompt.py
git commit -m "feat: Kimi question builder with sub-table fields"
```

---

## Task 5: parser.py — parse Kimi JSON → VillageData

**Files:**
- Create: `parser.py`
- Create: `tests/fixtures/sample_response.json`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Create fixture tests/fixtures/sample_response.json**

```json
{
  "basic_info": [{"head_name":"张三","secretary_intro":"书记介绍","contact_phone":"0571-123","village_intro":"村介绍","images":["http://img/a.jpg"]}],
  "sages": [{"type":"xiangxian","name":"李四","intro":"乡贤介绍","images":["http://img/b.jpg"]}],
  "minsu": [{"title":"民宿A","intro":"介绍","images":["http://img/c.jpg"],"lng":120.1,"lat":30.2,"rooms":[{"room_name":"101","room_type":2,"intro":"房型","price":200,"images":["http://img/r.jpg"]}]}],
  "specialty": [{"name":"笋干","price":50,"detail":"详情","images":["http://img/d.jpg"]}],
  "news": [{"content":"动态内容","images":["http://img/e.jpg"],"lng":120.1,"lat":30.2}],
  "activity": [{"name":"活动A","intro":"活动介绍","images":["http://img/f.jpg"],"lng":120.1,"lat":30.2,"days":[{"day_name":"第一天","intro":"日程","images":["http://img/g.jpg"],"trips":[{"trip_name":"行程1","trip_time":"09:00","intro":"行程介绍"}]}]}],
  "route": [{"name":"路线A","intro":"路线介绍","images":["http://img/h.jpg"],"lng":120.1,"lat":30.2}],
  "farmhouse": [{"name":"农庄A","intro":"农庄介绍","images":["http://img/i.jpg"],"lng":120.1,"lat":30.2,"dishes":[{"dish_name":"土鸡","price":80,"intro":"菜品","images":["http://img/dish.jpg"]}]}],
  "scenic": [{"name":"景区A","intro":"景区介绍","images":["http://img/j.jpg"],"lng":120.1,"lat":30.2}]
}
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_parser.py
import os
from parser import parse

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "sample_response.json")


def _load():
    with open(FIX, encoding="utf-8") as f:
        return f.read()


def test_parse_full_structure():
    data = parse(_load())
    assert len(data.minsu) == 1
    m = data.minsu[0]
    assert m.title == "民宿A"
    assert m.lng == 120.1
    assert len(m.images) == 1 and m.images[0].url == "http://img/c.jpg"
    assert len(m.rooms) == 1
    assert m.rooms[0].room_type == 2


def test_parse_sages_type_mapping():
    data = parse(_load())
    assert data.sages[0].sages_type == 2  # xiangxian -> 2


def test_parse_activity_nested_days_trips():
    data = parse(_load())
    a = data.activity[0]
    assert len(a.days) == 1
    assert a.days[0].trips[0].trip_name == "行程1"


def test_parse_strips_markdown_fence():
    raw = "```json\n" + _load() + "\n```"
    data = parse(raw)
    assert len(data.scenic) == 1


def test_parse_skips_record_missing_required_name():
    raw = '{"minsu": [{"intro":"无标题"}]}'  # title empty -> skipped
    data = parse(raw)
    assert data.minsu == []


def test_parse_empty_arrays_ok():
    data = parse('{"minsu":[]}')
    assert data.minsu == []
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL (module not found)

- [ ] **Step 4: Implement parser.py**

```python
# parser.py
import json
import re
from models import VillageData, Record, ImageRef, Room, Dish, Day, Trip


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _images(arr):
    return [ImageRef(url=u) for u in (arr or []) if isinstance(u, str) and u]


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sages_type(t):
    # DB: 1=先贤(已故), 2=乡贤(在世)
    return 2 if (t or "").lower() == "xiangxian" else 1


def _rooms(arr):
    out = []
    for o in (arr or []):
        out.append(Room(
            room_name=o.get("room_name", "") or "",
            room_type=int(o.get("room_type", 1) or 1),
            intro=o.get("intro", "") or "",
            price=_num(o.get("price")),
            images=_images(o.get("images")),
        ))
    return out


def _dishes(arr):
    out = []
    for o in (arr or []):
        out.append(Dish(
            dish_name=o.get("dish_name", "") or "",
            price=_num(o.get("price")),
            intro=o.get("intro", "") or "",
            images=_images(o.get("images")),
        ))
    return out


def _days(arr):
    out = []
    for o in (arr or []):
        out.append(Day(
            day_name=o.get("day_name", "") or "",
            intro=o.get("intro", "") or "",
            images=_images(o.get("images")),
            trips=[Trip(
                trip_name=t.get("trip_name", "") or "",
                trip_time=t.get("trip_time", "") or "",
                intro=t.get("intro", "") or "",
            ) for t in (o.get("trips") or [])],
        ))
    return out


def _record(obj):
    return Record(
        name=obj.get("name", "") or "",
        title=obj.get("title", "") or "",
        intro=obj.get("intro", "") or "",
        content=obj.get("content", "") or "",
        price=_num(obj.get("price")),
        detail=obj.get("detail", "") or "",
        head_name=obj.get("head_name", "") or "",
        secretary_intro=obj.get("secretary_intro", "") or "",
        contact_phone=obj.get("contact_phone", "") or "",
        village_intro=obj.get("village_intro", "") or "",
        sages_type=_sages_type(obj.get("type")),
        lng=_num(obj.get("lng")),
        lat=_num(obj.get("lat")),
        images=_images(obj.get("images")),
        rooms=_rooms(obj.get("rooms")),
        dishes=_dishes(obj.get("dishes")),
        days=_days(obj.get("days")),
    )


_CATEGORY_BUILDERS = {
    "basic_info": _record, "sages": _record, "minsu": _record,
    "specialty": _record, "news": _record, "activity": _record,
    "route": _record, "farmhouse": _record, "scenic": _record,
}

# categories where an empty identity field means skip the record
_IDENTITY_KEY = {
    "basic_info": None,        # keep the single record if present
    "sages": "name", "minsu": "title", "specialty": "name",
    "news": "content", "activity": "name", "route": "name",
    "farmhouse": "name", "scenic": "name",
}


def parse(raw_text: str) -> VillageData:
    obj = json.loads(_strip_fence(raw_text))
    data = VillageData()
    for key, builder in _CATEGORY_BUILDERS.items():
        items = obj.get(key, []) or []
        ident = _IDENTITY_KEY[key]
        kept = []
        for it in items:
            if not isinstance(it, dict):
                continue
            if ident is not None and not (it.get(ident) or "").strip():
                continue
            kept.append(builder(it))
        setattr(data, key, kept)
    return data
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Commit**

```bash
git add parser.py tests/test_parser.py tests/fixtures/sample_response.json
git commit -m "feat: parse Kimi JSON into VillageData with tolerance"
```

---

## Task 6: kimi_client.py — Moonshot call with retry + rate limit

**Files:**
- Create: `kimi_client.py`
- Test: `tests/test_kimi_client.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_kimi_client.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement kimi_client.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_kimi_client.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add kimi_client.py tests/test_kimi_client.py
git commit -m "feat: Moonshot client with retry and rate limiting"
```

---

## Task 7: qiniu_uploader.py — download, compress, upload

**Files:**
- Create: `qiniu_uploader.py`
- Test: `tests/test_qiniu.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qiniu.py
import io
from unittest.mock import patch, MagicMock
from PIL import Image
from qiniu_uploader import compress_if_needed, generate_key, upload_image_bytes


def _png_bytes(size=500):
    img = Image.new("RGB", (size, size), "red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_compress_under_limit_unchanged():
    data = _png_bytes(10)
    out, _ = compress_if_needed(data, max_size=1048576)
    assert len(out) <= 1048576


def test_compress_large_image_under_1mb():
    data = _png_bytes(2000)
    assert len(data) > 1048576
    out, _ = compress_if_needed(data, max_size=1048576)
    assert len(out) <= 1048576


def test_generate_key_format():
    key = generate_key()
    assert key.startswith("public/common/")
    assert key.endswith(".jpg")


def test_upload_returns_file_key():
    with patch("qiniu_uploader.put_data") as mock_put:
        mock_put.return_value = ({"key": "public/common/abc.jpg"}, None)
        key = upload_image_bytes(b"imgbytes", "public/common/abc.jpg",
                                 bucket="b", auth=MagicMock())
        assert key == "public/common/abc.jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_qiniu.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement qiniu_uploader.py**

```python
# qiniu_uploader.py
import io
import uuid
import requests
from PIL import Image
from qiniu import Auth, put_data


def generate_key(template: str = "public/common/{uuid}.jpg") -> str:
    return template.format(uuid=uuid.uuid4().hex)


def compress_if_needed(data: bytes, max_size: int) -> tuple:
    """Return (bytes, ext). Compress to JPEG under max_size by lowering quality."""
    if len(data) <= max_size:
        return data, _sniff_ext(data)
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    quality = 90
    out = b""
    while quality >= 20:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        out = buf.getvalue()
        if len(out) <= max_size:
            return out, "jpg"
        quality -= 10
    return out, "jpg"  # best effort


def _sniff_ext(data: bytes) -> str:
    if data[:8].startswith(b"\x89PNG"):
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"GIF8":
        return "gif"
    return "jpg"


def upload_image_bytes(data: bytes, key: str, bucket: str, auth: Auth) -> str:
    token = auth.upload_token(bucket, key, 3600)
    ret, _ = put_data(token, key, data)
    return ret["key"]


class QiniuUploader:
    def __init__(self, access_key, secret_key, bucket, domain, max_size, template):
        self._auth = Auth(access_key, secret_key)
        self._bucket = bucket
        self._domain = domain
        self._max_size = max_size
        self._template = template

    @classmethod
    def from_config(cls, cfg):
        q = cfg["qiniu"]
        return cls(q["access_key"], q["secret_key"], q["bucket"], q["domain"],
                   int(q["max_size_bytes"]), q["image_path_template"])

    def upload_url(self, url: str):
        """Download a remote image, compress, upload. Returns (file_key, size) or ('', 0) on failure."""
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.content
        except Exception:
            return "", 0
        data, _ext = compress_if_needed(data, self._max_size)
        key = generate_key(self._template)
        try:
            fk = upload_image_bytes(data, key, self._bucket, self._auth)
            return fk, len(data)
        except Exception:
            return "", 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_qiniu.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add qiniu_uploader.py tests/test_qiniu.py
git commit -m "feat: Qiniu upload with Pillow compression"
```

---

## Task 8: file_repo.py — insert into t_file

**Files:**
- Create: `file_repo.py`
- Test: `tests/test_file_repo.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_file_repo.py
from unittest.mock import MagicMock
from file_repo import FileRepo


def test_insert_returns_file_id_and_uses_defaults():
    db = MagicMock()
    db.execute.return_value = 99
    repo = FileRepo(db, creator_id=43, creator_user_type=1, creator_name="乡投会员5446")
    fid = repo.insert(file_key="public/common/abc.jpg", file_name="a.jpg",
                      file_size=1234, file_type="jpg")
    sql, args = db.execute.call_args.args
    assert "t_file" in sql
    assert args[0] == 1          # folder_type
    assert args[1] == "a.jpg"    # file_name
    assert args[2] == 1234       # file_size
    assert args[3] == "public/common/abc.jpg"
    assert args[4] == "jpg"
    assert args[5] == 43         # creator_id
    assert args[6] == 1          # creator_user_type
    assert args[7] == "乡投会员5446"
    assert fid == 99
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_file_repo.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement file_repo.py**

```python
# file_repo.py

_INSERT_SQL = """
INSERT INTO t_file
  (folder_type, file_name, file_size, file_key, file_type,
   creator_id, creator_user_type, creator_name)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
"""


class FileRepo:
    def __init__(self, db, creator_id, creator_user_type, creator_name):
        self._db = db
        self._creator_id = creator_id
        self._creator_user_type = creator_user_type
        self._creator_name = creator_name

    def insert(self, file_key, file_name, file_size, file_type):
        return self._db.execute(_INSERT_SQL, (
            1, file_name, file_size, file_key, file_type,
            self._creator_id, self._creator_user_type, self._creator_name,
        ))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_file_repo.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add file_repo.py tests/test_file_repo.py
git commit -m "feat: t_file insert repository"
```

---

## Task 9: geo.py — GPS resolution + point SQL

**Files:**
- Create: `geo.py`
- Test: `tests/test_geo.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_geo.py
from geo import resolve_point, point_wkt


def test_uses_kimi_coords_when_present():
    assert resolve_point(120.1, 30.2, village_lng=119.0, village_lat=29.0) == (120.1, 30.2)


def test_falls_back_to_village_coords():
    assert resolve_point(None, None, village_lng=119.0, village_lat=29.0) == (119.0, 29.0)


def test_returns_none_when_nothing():
    assert resolve_point(None, None, village_lng=None, village_lat=None) is None


def test_point_wkt_format():
    assert point_wkt(120.1, 30.2) == "POINT(120.1 30.2)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_geo.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement geo.py**

```python
# geo.py
from typing import Optional, Tuple


def resolve_point(lng, lat, village_lng, village_lat) -> Optional[Tuple[float, float]]:
    if lng is not None and lat is not None:
        return (float(lng), float(lat))
    if village_lng is not None and village_lat is not None:
        return (float(village_lng), float(village_lat))
    return None


def point_wkt(lng, lat) -> str:
    return f"POINT({lng} {lat})"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_geo.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add geo.py tests/test_geo.py
git commit -m "feat: GPS resolution and WKT helper"
```

---

## Task 10: writers/base.py — generic BaseWriter

**Files:**
- Create: `writers/__init__.py`
- Create: `writers/base.py`
- Test: `tests/test_writer_base.py`

This is the core engine. `BaseWriter` takes a `TableConfig` and writes records. Each config explicitly declares which default columns the table has (`uniform_columns` + `has_comment_code`), so the writer never emits a column the table lacks. Images are resolved to file_keys via a passed-in `image_resolver(image_refs) -> list[file_key]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_writer_base.py
from unittest.mock import MagicMock
from models import Record, ImageRef
from writers.base import BaseWriter, TableConfig, SubTableConfig, GpsMode

# The default value map (mirrors module constant in base.py)
D = {"create_user_id": 43, "update_user_id": 43, "approve_status": 2,
     "approve_id": 43, "online": 1, "deleted_flag": 0, "member_id": 43}


def _cfg_goods():
    return TableConfig(
        table="vill_goods", mode="insert", gps=GpsMode.NONE,
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "online", "deleted_flag"],
        has_comment_code=True,
        field_map={"name": "goods_name", "price": "price", "detail": "introduce"},
        image_fields={"images": "goods_imgs"},
        extra_defaults={"goods_status": 2, "category_id": 7, "shop_id": 2},
    )


def _args_to_dict(sql, args):
    inside = sql.split("(", 1)[1].split(")", 1)[0]
    cols = [c.strip() for c in inside.split(",")]
    return dict(zip(cols, args))


def test_insert_builds_row_with_defaults_and_images():
    db = MagicMock()
    db.execute.return_value = 5
    def resolver(refs):
        return ["public/common/" + r.url[-5:] + ".jpg" for r in refs]
    w = BaseWriter(db, _cfg_goods(), resolver,
                   village={"id": 1, "village_name": "X"}, defaults={})
    rec = Record(name="笋干", price=50, detail="详情",
                 images=[ImageRef(url="http://x/12345")])
    count = w.write([rec])
    sql, args = db.execute.call_args.args
    adict = _args_to_dict(sql, args)
    assert adict["goods_name"] == "笋干"
    assert adict["price"] == 50
    assert adict["village_id"] == 1
    assert "village_name" not in adict   # goods has no village_name column
    assert adict["category_id"] == 7
    assert adict["goods_status"] == 2
    assert adict["create_user_id"] == 43
    assert adict["comment_code"]            # generated
    assert "member_id" not in adict         # goods config doesn't list member_id
    assert adict["goods_imgs"] == "public/common/12345.jpg"
    assert count == 1


def test_update_mode_uses_where_id_and_no_village_id():
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs): return []
    cfg = TableConfig(
        table="vill_village", mode="update", gps=GpsMode.NONE,
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "deleted_flag"],
        has_comment_code=False,
        field_map={"village_intro": "introduce"},
        image_fields={"images": "entire_cover_img"}, extra_defaults={})
    w = BaseWriter(db, cfg, resolver, village={"id": 77, "village_name": "X"}, defaults={})
    rec = Record(village_intro="村介绍")
    w.write([rec])
    sql, args = db.execute.call_args.args
    assert sql.startswith("UPDATE vill_village SET")
    assert "WHERE id = %s" in sql
    assert args[-1] == 77
    adict = _set_cols(sql, args[:-1])
    assert "village_id" not in adict
    assert "comment_code" not in adict


def _set_cols(sql, args):
    set_part = sql.split("SET", 1)[1]
    cols = [c.split("=")[0].strip() for c in set_part.split(",")]
    return dict(zip(cols, args))


def test_point_gps_uses_wkt():
    db = MagicMock()
    db.execute.return_value = 1
    def resolver(refs): return []
    cfg = TableConfig(
        table="vill_attraction", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "online", "deleted_flag"],
        has_comment_code=True,
        address_columns=["village_name", "province_id", "province_name", "city_id",
                         "city_name", "area_id", "area_name", "street_id", "street_name", "address"],
        field_map={"name": "attraction_name", "intro": "introduction"},
        image_fields={"images": "cover_img"}, extra_defaults={})
    w = BaseWriter(db, cfg, resolver,
                   village={"id": 1, "lng": 119.0, "lat": 29.0, "village_name": "v",
                            "province_name": "p", "city_name": "c", "area_name": "a",
                            "street_name": "s", "address": "addr",
                            "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4},
                   defaults={})
    rec = Record(name="景区", intro="介绍", lng=None, lat=None)
    w.write([rec])
    sql, args = db.execute.call_args.args
    assert "location_point" in sql
    assert "ST_GeomFromText(%s)" in sql
    assert "POINT(119.0 29.0)" in args


def test_subtable_rooms_inserted_with_fk():
    db = MagicMock()
    db.execute.side_effect = [100, 200]  # homestay id, then room id
    def resolver(refs): return []
    cfg = TableConfig(
        table="vill_homestay", mode="insert", gps=GpsMode.POINT,
        point_column="location",
        uniform_columns=["create_user_id", "update_user_id", "approve_status",
                         "approve_id", "online", "deleted_flag"],
        has_comment_code=True,
        field_map={"title": "title", "intro": "introduce"},
        image_fields={"images": "cover_img"}, extra_defaults={"homeowner_id": 4},
        sub_tables=[SubTableConfig(
            table="vill_homestay_room", fk_column="homestay_id", records_attr="rooms",
            uniform_columns=["create_user_id", "update_user_id", "approve_status",
                             "approve_id", "online", "deleted_flag"],
            has_comment_code=False,
            field_map={"room_name": "room_name", "room_type": "room_type",
                       "intro": "introduction", "price": "week_day_price"},
            image_fields={"images": "cover_img"})])
    w = BaseWriter(db, cfg, resolver, village={"id": 1, "village_name": "X",
                                               "lng": 1.0, "lat": 2.0}, defaults={})
    rec = Record(title="t", intro="i", images=[], lng=1.0, lat=2.0,
                 rooms=[__import__("models").Room(room_name="101")])
    w.write([rec])
    # second execute is the room insert; its args must include the homestay id 100
    room_sql, room_args = db.execute.call_args_list[1].args
    assert "vill_homestay_room" in room_sql
    assert 100 in room_args
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_writer_base.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement writers/base.py**

```python
# writers/base.py
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional
from models import Record, ImageRef
from geo import resolve_point, point_wkt


class GpsMode(Enum):
    NONE = "none"
    POINT = "point"
    DECIMAL = "decimal"


# default values for the uniform columns (only applied where a table lists them)
DEFAULT_VALUES = {
    "create_user_id": 43,
    "update_user_id": 43,
    "approve_status": 2,
    "approve_id": 43,
    "online": 1,
    "deleted_flag": 0,
    "member_id": 43,
}


@dataclass
class SubTableConfig:
    table: str
    fk_column: str              # column referencing parent id
    records_attr: str           # attr on Record: "rooms" | "dishes" | "days"
    uniform_columns: List[str]
    has_comment_code: bool
    field_map: Dict[str, str]
    image_fields: Dict[str, str] = field(default_factory=dict)
    extra_defaults: Dict[str, object] = field(default_factory=dict)
    children: List["SubTableConfig"] = field(default_factory=list)
    child_attr: str = ""        # attr on the sub-record holding nested children


@dataclass
class TableConfig:
    table: str
    mode: str                          # "insert" | "update"
    gps: GpsMode
    uniform_columns: List[str]         # which DEFAULT_VALUES columns this table has
    has_comment_code: bool
    field_map: Dict[str, str]          # record-attr -> column
    image_fields: Dict[str, str]       # record-attr(list of images) -> column (comma-joined)
    image_first_fields: Dict[str, str] = field(default_factory=dict)  # first image only -> column
    extra_defaults: Dict[str, object] = field(default_factory=dict)
    point_column: str = "location_point"
    address_columns: List[str] = field(default_factory=list)  # village/address cols this table has
    sub_tables: List[SubTableConfig] = field(default_factory=list)
    skip_if_no_images: bool = False    # e.g. dynamics cover/img_url NOT NULL


ImageResolver = Callable[[List[ImageRef]], List[str]]


class BaseWriter:
    def __init__(self, db, cfg: TableConfig, image_resolver: ImageResolver,
                 village: dict, defaults: dict):
        self._db = db
        self._cfg = cfg
        self._resolve = image_resolver
        self._village = village
        self._defaults = defaults

    def write(self, records: List[Record]) -> int:
        count = 0
        for rec in records:
            if self._cfg.skip_if_no_images and not rec.images:
                continue
            row = self._build_row(rec)
            if self._cfg.mode == "update":
                self._update(row)
            else:
                parent_id = self._insert(self._cfg.table, row)
                self._write_sub_tables(rec, parent_id)
            count += 1
        return count

    def _build_row(self, rec: Record) -> Dict[str, object]:
        row: Dict[str, object] = {}
        for col in self._cfg.uniform_columns:
            row[col] = DEFAULT_VALUES[col]
        if self._cfg.has_comment_code:
            row["comment_code"] = uuid.uuid4().hex
        for col, val in self._cfg.extra_defaults.items():
            row[col] = val
        for col, val in self._defaults.items():
            row[col] = val
        if self._cfg.mode == "insert":
            row["village_id"] = self._village["id"]
            for col in self._cfg.address_columns:
                if col in self._village:
                    row[col] = self._village[col]
        for attr, col in self._cfg.field_map.items():
            val = getattr(rec, attr, None)
            if val is not None and val != "":
                row[col] = val
        for attr, col in self._cfg.image_fields.items():
            refs = getattr(rec, attr, None) or []
            keys = self._resolve(refs)
            if keys:
                row[col] = ",".join(keys)
        for attr, col in self._cfg.image_first_fields.items():
            refs = getattr(rec, attr, None) or []
            keys = self._resolve(refs)
            if keys:
                row[col] = keys[0]
        self._apply_gps(rec, row)
        return row

    def _apply_gps(self, rec, row):
        if self._cfg.gps == GpsMode.NONE:
            return
        pt = resolve_point(rec.lng, rec.lat,
                           self._village.get("lng"), self._village.get("lat"))
        if pt is None:
            return
        if self._cfg.gps == GpsMode.POINT:
            row[self._cfg.point_column] = ("__POINT__", point_wkt(*pt))
        else:  # DECIMAL
            row["latitude"] = pt[1]
            row["longitude"] = pt[0]

    def _insert(self, table, row) -> int:
        cols, args, point_pos = self._split_row(row)
        ph = ["ST_GeomFromText(%s)" if i == point_pos else "%s" for i in range(len(cols))]
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(ph)})"
        return self._db.execute(sql, tuple(args))

    def _update(self, row):
        vid = self._village["id"]
        cols, args, point_pos = self._split_row(row)
        set_clause = ", ".join(
            f"{c} = ST_GeomFromText(%s)" if i == point_pos else f"{c} = %s"
            for i, c in enumerate(cols))
        sql = f"UPDATE {self._cfg.table} SET {set_clause} WHERE id = %s"
        self._db.execute(sql, tuple(args) + (vid,))

    def _split_row(self, row):
        cols, args, point_pos = [], [], None
        for col, val in row.items():
            if isinstance(val, tuple) and val and val[0] == "__POINT__":
                cols.append(col)
                args.append(val[1])
                point_pos = len(args) - 1
            else:
                cols.append(col)
                args.append(val)
        return cols, args, point_pos

    def _write_sub_tables(self, rec, parent_id):
        for sub in self._cfg.sub_tables:
            items = getattr(rec, sub.records_attr, None) or []
            for it in items:
                row = self._build_sub_row(sub, it, parent_id)
                child_id = self._insert(sub.table, row)
                for child in sub.children:
                    child_items = getattr(it, child.child_attr, None) or []
                    for ci in child_items:
                        crow = self._build_sub_row(child, ci, child_id)
                        self._insert(child.table, crow)

    def _build_sub_row(self, sub, item, fk_id) -> Dict[str, object]:
        row: Dict[str, object] = {}
        for col in sub.uniform_columns:
            row[col] = DEFAULT_VALUES[col]
        if sub.has_comment_code:
            row["comment_code"] = uuid.uuid4().hex
        for col, val in sub.extra_defaults.items():
            row[col] = val
        row[sub.fk_column] = fk_id
        for attr, col in sub.field_map.items():
            val = getattr(item, attr, None)
            if val is not None and val != "":
                row[col] = val
        for attr, col in sub.image_fields.items():
            refs = getattr(item, attr, None) or []
            keys = self._resolve(refs)
            if keys:
                row[col] = ",".join(keys)
        return row
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_writer_base.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add writers/__init__.py writers/base.py tests/test_writer_base.py
git commit -m "feat: generic BaseWriter with explicit per-table columns, GPS, sub-tables"
```

---

## Task 11: writers/tables.py — all 9 table configs

**Files:**
- Create: `writers/tables.py`
- Test: `tests/test_tables.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tables.py
from writers.tables import TABLE_CONFIGS
from writers.base import GpsMode


def test_all_nine_categories_present():
    expected = {"basic_info", "sages", "minsu", "specialty", "news",
                "activity", "route", "farmhouse", "scenic"}
    assert set(TABLE_CONFIGS.keys()) == expected


def test_basic_info_is_update_without_comment_code():
    c = TABLE_CONFIGS["basic_info"]
    assert c.mode == "update"
    assert c.table == "vill_village"
    assert c.has_comment_code is False
    assert "comment_code" not in c.uniform_columns
    assert "entire_cover_img" in c.image_fields.values()


def test_minsu_has_rooms_subtable():
    subs = TABLE_CONFIGS["minsu"].sub_tables
    assert len(subs) == 1
    assert subs[0].table == "vill_homestay_room"
    assert subs[0].fk_column == "homestay_id"


def test_activity_has_days_with_trips():
    subs = TABLE_CONFIGS["activity"].sub_tables
    assert subs[0].table == "vill_village_activity_day"
    assert len(subs[0].children) == 1
    assert subs[0].children[0].table == "vill_village_activity_trip"
    assert subs[0].children[0].fk_column == "day_id"


def test_point_categories():
    assert TABLE_CONFIGS["minsu"].gps == GpsMode.POINT
    assert TABLE_CONFIGS["minsu"].point_column == "location"
    assert TABLE_CONFIGS["scenic"].gps == GpsMode.POINT
    assert TABLE_CONFIGS["farmhouse"].point_column == "location_point"


def test_address_columns_only_on_address_tables():
    assert "village_name" in TABLE_CONFIGS["minsu"].address_columns
    assert "village_name" in TABLE_CONFIGS["farmhouse"].address_columns
    assert "village_name" in TABLE_CONFIGS["scenic"].address_columns
    assert TABLE_CONFIGS["specialty"].address_columns == []
    assert TABLE_CONFIGS["news"].address_columns == []


def test_news_skips_when_no_images():
    assert TABLE_CONFIGS["news"].skip_if_no_images is True
    assert TABLE_CONFIGS["news"].image_first_fields == {"images": "cover"}  # cover NOT NULL


def test_sages_avatar_first_image():
    assert TABLE_CONFIGS["sages"].image_first_fields == {"images": "avatar"}


def test_specialty_has_goods_defaults():
    ed = TABLE_CONFIGS["specialty"].extra_defaults
    assert ed["goods_status"] == 2
    assert "category_id" in ed
    assert ed["shop_id"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tables.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement writers/tables.py**

```python
# writers/tables.py
from writers.base import TableConfig, SubTableConfig, GpsMode

# uniform column groups reused across tables
_U_COMMON = ["create_user_id", "update_user_id", "approve_status",
             "approve_id", "online", "deleted_flag"]
_U_COMMON_NO_ONLINE = ["create_user_id", "update_user_id", "approve_status",
                        "approve_id", "deleted_flag"]
_U_WITH_MEMBER = ["create_user_id", "update_user_id", "approve_status",
                   "approve_id", "online", "deleted_flag", "member_id"]
_U_MINIMAL = ["create_user_id", "update_user_id", "deleted_flag"]  # activity_day / activity_trip

_ADDR = ["village_name", "province_id", "province_name", "city_id",
         "city_name", "area_id", "area_name", "street_id", "street_name", "address"]

TABLE_CONFIGS = {
    "basic_info": TableConfig(
        table="vill_village", mode="update", gps=GpsMode.NONE,
        uniform_columns=_U_COMMON_NO_ONLINE,
        has_comment_code=False,
        field_map={"secretary_intro": "head_introduction", "contact_phone": "contact_phone",
                   "village_intro": "introduce", "head_name": "head_name"},
        image_fields={"images": "entire_cover_img"},
    ),
    "sages": TableConfig(
        table="vill_village_sages", mode="insert", gps=GpsMode.NONE,
        uniform_columns=_U_WITH_MEMBER,
        has_comment_code=True,
        field_map={"name": "sages_name", "intro": "context"},
        image_fields={"images": "img_url"},
        image_first_fields={"images": "avatar"},
    ),
    "minsu": TableConfig(
        table="vill_homestay", mode="insert", gps=GpsMode.POINT,
        point_column="location",
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        address_columns=_ADDR,
        field_map={"title": "title", "intro": "introduce"},
        image_fields={"images": "cover_img"},
        extra_defaults={"homeowner_id": 4},
        sub_tables=[
            SubTableConfig(
                table="vill_homestay_room", fk_column="homestay_id",
                records_attr="rooms",
                uniform_columns=_U_COMMON, has_comment_code=False,
                field_map={"room_name": "room_name", "room_type": "room_type",
                           "intro": "introduction", "price": "week_day_price"},
                image_fields={"images": "cover_img"},
            ),
        ],
    ),
    "specialty": TableConfig(
        table="vill_goods", mode="insert", gps=GpsMode.NONE,
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        field_map={"name": "goods_name", "price": "price", "detail": "introduce"},
        image_fields={"images": "goods_imgs"},
        extra_defaults={"goods_status": 2, "category_id": 0, "shop_id": 2},
    ),
    "news": TableConfig(
        table="vill_dynamics", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=_U_WITH_MEMBER,
        has_comment_code=True,
        field_map={"content": "context"},
        image_fields={"images": "img_url"},
        image_first_fields={"images": "cover"},  # cover is NOT NULL single image
        skip_if_no_images=True,   # cover + img_url are NOT NULL
    ),
    "activity": TableConfig(
        table="vill_village_activity", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        field_map={"name": "activity_name", "intro": "introduce"},
        image_fields={"images": "activity_imgs"},
        extra_defaults={"activity_status": 1},
        sub_tables=[
            SubTableConfig(
                table="vill_village_activity_day", fk_column="activity_id",
                records_attr="days",
                uniform_columns=_U_MINIMAL, has_comment_code=False,
                field_map={"day_name": "day_name", "intro": "introduce"},
                image_fields={"images": "travel_day_imgs"},
                extra_defaults={"activity_type": 2},
                children=[
                    SubTableConfig(
                        table="vill_village_activity_trip", fk_column="day_id",
                        records_attr="trips",
                        uniform_columns=_U_MINIMAL, has_comment_code=False,
                        field_map={"trip_name": "trip_name", "trip_time": "trip_time",
                                   "intro": "introduce"},
                        image_fields={},
                    ),
                ],
                child_attr="trips",
            ),
        ],
    ),
    "route": TableConfig(
        table="vill_village_travel", mode="insert", gps=GpsMode.DECIMAL,
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        field_map={"name": "travel_name", "intro": "introduce"},
        image_fields={"images": "travel_imgs"},
    ),
    "farmhouse": TableConfig(
        table="vill_restaurant", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        address_columns=_ADDR,
        field_map={"name": "restaurant_name", "intro": "introduction"},
        image_fields={"images": "cover_img"},
        extra_defaults={"shop_id": 2},
        sub_tables=[
            SubTableConfig(
                table="vill_restaurant_dish", fk_column="restaurant_id",
                records_attr="dishes",
                uniform_columns=_U_COMMON, has_comment_code=False,
                field_map={"dish_name": "dish_name", "price": "unit_price",
                           "intro": "introduction"},
                image_fields={"images": "cover_img"},
            ),
        ],
    ),
    "scenic": TableConfig(
        table="vill_attraction", mode="insert", gps=GpsMode.POINT,
        point_column="location_point",
        uniform_columns=_U_COMMON,
        has_comment_code=True,
        address_columns=_ADDR,
        field_map={"name": "attraction_name", "intro": "introduction"},
        image_fields={"images": "cover_img"},
    ),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tables.py -v`
Expected: PASS (9 passed)

- [ ] **Step 5: Commit**

```bash
git add writers/tables.py tests/test_tables.py
git commit -m "feat: table configs for all 9 categories + sub-tables"
```

---

## Task 12: status_repo.py — task_status CRUD

**Files:**
- Create: `status_repo.py`
- Test: `tests/test_status_repo.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_status_repo.py
from unittest.mock import MagicMock
from status_repo import StatusRepo


def test_mark_pending_inserts():
    db = MagicMock()
    repo = StatusRepo(db)
    repo.mark_pending(123)
    sql, args = db.execute.call_args.args
    assert "INSERT INTO task_status" in sql
    assert args[0] == 123


def test_mark_done_updates_status():
    db = MagicMock()
    repo = StatusRepo(db)
    repo.mark_done(123, records_written=5, raw="raw")
    sql, args = db.execute.call_args.args
    assert "UPDATE task_status SET" in sql
    assert "status = %s" in sql
    assert args[0] == "done"


def test_done_ids_queried():
    db = MagicMock()
    db.query.return_value = [{"village_id": 1}, {"village_id": 2}]
    repo = StatusRepo(db)
    assert repo.done_ids() == {1, 2}


def test_failed_ids_queried():
    db = MagicMock()
    db.query.return_value = [{"village_id": 9}]
    repo = StatusRepo(db)
    assert repo.failed_ids() == {9}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_status_repo.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement status_repo.py**

```python
# status_repo.py

_INSERT = """INSERT INTO task_status (village_id, status, started_at)
VALUES (%s, 'pending', NOW())"""
_UPDATE = """UPDATE task_status SET status=%s, error_msg=%s, records_written=%s,
raw_response=%s, retry_count=retry_count+%s, finished_at=NOW() WHERE village_id=%s"""
_DONE_IDS = "SELECT village_id FROM task_status WHERE status='done'"
_FAILED_IDS = "SELECT village_id FROM task_status WHERE status='failed'"


class StatusRepo:
    def __init__(self, db):
        self._db = db

    def mark_pending(self, village_id):
        self._db.execute(_INSERT, (village_id,))

    def mark_done(self, village_id, records_written=0, raw=""):
        self._db.execute(_UPDATE, ("done", None, records_written, raw, 0, village_id))

    def mark_failed(self, village_id, error_msg, raw=""):
        self._db.execute(_UPDATE, ("failed", error_msg, 0, raw, 1, village_id))

    def done_ids(self):
        rows = self._db.query(_DONE_IDS)
        return {r["village_id"] for r in rows}

    def failed_ids(self):
        rows = self._db.query(_FAILED_IDS)
        return {r["village_id"] for r in rows}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_status_repo.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add status_repo.py tests/test_status_repo.py
git commit -m "feat: task_status repository for resume"
```

---

## Task 13: pipeline.py — orchestrate one village

**Files:**
- Create: `pipeline.py`
- Test: `tests/test_pipeline.py`

The pipeline: ask Kimi → parse → for each category, resolve images (upload to Qiniu, insert t_file, get file_keys) → write via BaseWriter → return total records. Image resolution is shared: a single closure uploads each ImageRef once (cached by url). Whole village in one DB transaction; on any unrecoverable error, rollback + re-raise.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import json, pytest
from unittest.mock import MagicMock
from pipeline import Pipeline


def test_pipeline_writes_all_categories_and_commits():
    raw = json.dumps({
        "basic_info": [{"head_name":"张","secretary_intro":"s","contact_phone":"p","village_intro":"v","images":["http://a"]}],
        "minsu": [{"title":"t","intro":"i","images":["http://b"],"lng":1.0,"lat":2.0,"rooms":[{"room_name":"101","images":["http://r"]}]}],
        "specialty": [{"name":"n","price":10,"detail":"d","images":["http://c"]}],
        "news": [{"content":"c","images":["http://e"]}],
        "activity": [{"name":"a","intro":"i","images":["http://f"],"days":[{"day_name":"d1","images":[],"trips":[{"trip_name":"t1"}]}]}],
        "route": [{"name":"r","intro":"i","images":[]}],
        "farmhouse": [{"name":"f","intro":"i","images":[],"dishes":[{"dish_name":"x","images":[]}]}],
        "scenic": [{"name":"s","intro":"i","images":[]}],
        "sages": [{"type":"xiangxian","name":"李","intro":"i","images":[]}],
    }, ensure_ascii=False)

    kimi = MagicMock(); kimi.ask.return_value = raw
    uploader = MagicMock()
    uploader.upload_url.side_effect = lambda url: ("public/common/" + url[-1] + ".jpg", 123)
    db = MagicMock(); db.execute.return_value = 1
    village = {"id": 1, "village_name": "V", "province_name": "P", "city_name": "C",
               "area_name": "A", "street_name": "S", "address": "addr", "lng": 119.0, "lat": 29.0,
               "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={},
                    goods_category_id=7)
    count, raw_back = pipe.run(village, question="q")
    assert db.execute.call_count >= 8   # at least one write per category record
    assert count >= 8
    db.commit.assert_called_once()


def test_pipeline_rolls_back_on_parse_failure():
    kimi = MagicMock(); kimi.ask.return_value = "not json"
    uploader = MagicMock()
    db = MagicMock()
    village = {"id": 1, "village_name": "V"}
    pipe = Pipeline(db, kimi, uploader, file_repo=MagicMock(), defaults={}, goods_category_id=7)
    with pytest.raises(RuntimeError):
        pipe.run(village, question="q")
    db.rollback.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement pipeline.py**

```python
# pipeline.py
from writers.base import BaseWriter
from writers.tables import TABLE_CONFIGS
from parser import parse


class Pipeline:
    def __init__(self, db, kimi, uploader, file_repo, defaults, goods_category_id):
        self._db = db
        self._kimi = kimi
        self._uploader = uploader
        self._file_repo = file_repo
        self._defaults = defaults
        self._goods_category_id = goods_category_id

    def run(self, village: dict, question: str):
        raw = self._kimi.ask(question)
        try:
            data = parse(raw)
        except Exception as e:
            self._db.rollback()
            raise RuntimeError(f"parse failed: {e}") from e

        cache = {}

        def resolve(refs):
            keys = []
            for ref in refs:
                if not ref.url:
                    continue
                if ref.url in cache:
                    keys.append(cache[ref.url])
                    continue
                file_key, size = self._uploader.upload_url(ref.url)
                if not file_key:
                    continue
                self._file_repo.insert(file_key=file_key,
                                       file_name=ref.url.split("/")[-1] or "image",
                                       file_size=size, file_type="jpg")
                cache[ref.url] = file_key
                keys.append(file_key)
            return keys

        total = 0
        try:
            for category, cfg in TABLE_CONFIGS.items():
                records = getattr(data, category, [])
                if not records:
                    continue
                if category == "specialty":
                    cfg.extra_defaults["category_id"] = self._goods_category_id
                writer = BaseWriter(self._db, cfg, resolve, village, self._defaults)
                total += writer.write(records)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return total, raw
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline.py tests/test_pipeline.py
git commit -m "feat: per-village pipeline orchestration with transaction"
```

---

## Task 14: runner.py — entry loop with resume / overwrite / retry-failed

**Files:**
- Create: `runner.py`
- Test: `tests/test_runner.py`

Runner loads village rows from `vill_village`, filters done (unless `--retry-failed`), deletes existing business data for the village when `overwrite` is set, then runs the pipeline and marks status.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runner.py
from unittest.mock import MagicMock
from runner import Runner

_V = {"id": 3, "village_name": "V", "province_name": "P", "city_name": "C",
      "area_name": "A", "street_name": "S", "address": "x", "lng": 1.0, "lat": 2.0,
      "province_id": 1, "city_id": 2, "area_id": 3, "street_id": 4}


def test_runner_skips_done_villages():
    db = MagicMock(); db.query_one.return_value = _V
    status = MagicMock(); status.done_ids.return_value = {1, 2}
    pipe = MagicMock(); pipe.run.return_value = (5, "raw")
    runner = Runner(db, status, pipe, village_repo=MagicMock(), overwrite=False)
    runner.run([1, 2, 3])
    pipe.run.assert_called_once()
    assert pipe.run.call_args.args[0]["id"] == 3


def test_runner_marks_failed_on_pipeline_error(capsys):
    db = MagicMock(); db.query_one.return_value = _V
    status = MagicMock(); status.done_ids.return_value = set()
    pipe = MagicMock(); pipe.run.side_effect = RuntimeError("boom")
    runner = Runner(db, status, pipe, village_repo=MagicMock(), overwrite=False)
    runner.run([3])
    status.mark_failed.assert_called_once()
    assert status.mark_failed.call_args.args[0] == 3


def test_runner_overwrite_deletes_existing():
    db = MagicMock(); db.query_one.return_value = _V
    status = MagicMock(); status.done_ids.return_value = set()
    pipe = MagicMock(); pipe.run.return_value = (1, "raw")
    runner = Runner(db, status, pipe, village_repo=MagicMock(), overwrite=True)
    runner.run([3])
    sqls = [c.args[0] for c in db.execute.call_args_list]
    assert any("DELETE FROM" in s for s in sqls)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_runner.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement runner.py**

```python
# runner.py
from prompt import build_question

# business tables to clear on overwrite, in child-first safe order
_OVERWRITE_TABLES = [
    "vill_homestay_room", "vill_homestay",
    "vill_restaurant_dish", "vill_restaurant",
    "vill_village_activity_trip", "vill_village_activity_day", "vill_village_activity",
    "vill_village_travel", "vill_dynamics", "vill_goods",
    "vill_village_sages", "vill_attraction",
]


class Runner:
    def __init__(self, db, status_repo, pipeline, village_repo, overwrite):
        self._db = db
        self._status = status_repo
        self._pipe = pipeline
        self._village_repo = village_repo
        self._overwrite = overwrite

    def run(self, village_ids):
        done = self._status.done_ids()
        todo = [vid for vid in village_ids if vid not in done]
        for vid in todo:
            village = self._village_repo.fetch(vid)
            if not village:
                print(f"[skip] village {vid} not found")
                continue
            try:
                if self._overwrite:
                    self._delete_existing(vid)
                self._status.mark_pending(vid)
                q = build_question(
                    village.get("province_name", ""), village.get("city_name", ""),
                    village.get("area_name", ""), village.get("street_name", ""),
                    village.get("village_name", ""))
                count, raw = self._pipe.run(village, q)
                self._status.mark_done(vid, records_written=count, raw=raw)
                print(f"[done] village {vid}: {count} records")
            except Exception as e:
                self._status.mark_failed(vid, str(e))
                print(f"[fail] village {vid}: {e}")

    def _delete_existing(self, vid):
        for t in _OVERWRITE_TABLES:
            self._db.execute(f"DELETE FROM {t} WHERE village_id = %s", (vid,))
        self._db.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_runner.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add runner.py tests/test_runner.py
git commit -m "feat: runner with resume, overwrite, retry-failed"
```

---

## Task 15: wiring + main entry + village_repo

**Files:**
- Create: `village_repo.py`
- Create: `main.py`
- Create: `village_ids.txt` (example, gitignored)

- [ ] **Step 1: Implement village_repo.py**

```python
# village_repo.py

_FETCH_SQL = """SELECT id, village_name, province_id, province_name, city_id, city_name,
  area_id, area_name, street_id, street_name, address, lng, lat
FROM vill_village WHERE id = %s"""


class VillageRepo:
    def __init__(self, db):
        self._db = db

    def fetch(self, village_id):
        return self._db.query_one(_FETCH_SQL, (village_id,))
```

- [ ] **Step 2: Implement main.py**

```python
# main.py
import argparse
from config_loader import Config
from db import MySQL
from kimi_client import KimiClient
from qiniu_uploader import QiniuUploader
from file_repo import FileRepo
from status_repo import StatusRepo
from village_repo import VillageRepo
from pipeline import Pipeline
from runner import Runner


def load_village_ids(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                out.append(int(s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--retry-failed", action="store_true")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    db = MySQL.from_config(cfg)
    kimi = KimiClient.from_config(cfg)
    uploader = QiniuUploader.from_config(cfg)
    file_repo = FileRepo(db, creator_id=43, creator_user_type=1, creator_name="乡投会员5446")
    status = StatusRepo(db)
    village_repo = VillageRepo(db)
    pipe = Pipeline(db, kimi, uploader, file_repo, defaults={},
                    goods_category_id=cfg["run"].get("goods_category_id", 0))
    overwrite = bool(cfg["run"].get("overwrite", False))

    ids = load_village_ids(cfg["run"]["village_ids_file"])
    if args.retry_failed:
        ids = list(status.failed_ids())
    runner = Runner(db, status, pipe, village_repo, overwrite)
    runner.run(ids)
    db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create example village_ids.txt**

```
1
2
3
```

- [ ] **Step 4: Run full test suite**

Run: `pytest -v`
Expected: all tests PASS (≈39 tests)

- [ ] **Step 5: Commit**

```bash
git add village_repo.py main.py village_ids.txt
git commit -m "feat: wire up main entry and village repo"
```

---

## Task 16: End-to-end validation (manual)

- [ ] **Step 1: Install deps**

Run: `pip install -r requirements.txt`

- [ ] **Step 2: Fill `config.yaml`** (copy from `config.yaml.example`) with real Moonshot key, Qiniu keys, MySQL creds, and real `goods_category_id`.

- [ ] **Step 3: Put 2-3 real premium village IDs in `village_ids.txt`**

- [ ] **Step 4: Run**

Run: `python main.py`
Expected: prints `[done] village X: N records` for each; `task_status` rows show `done`.

- [ ] **Step 5: Verify in DB**

- `SELECT * FROM task_status;` — all `done`.
- Sample one village's rows across `vill_homestay`, `vill_goods`, `vill_dynamics`, `vill_village_activity`, `vill_village` (basic_info updated), etc. — fields populated, `cover_img`/`goods_imgs`/`img_url` contain `public/common/xxx.jpg` keys.
- `SELECT * FROM t_file WHERE creator_id=43 ORDER BY file_id DESC LIMIT 5;` — file rows exist with matching keys.
- Confirm images display (prepend Qiniu domain to a file_key, open in browser).
- Confirm `location`/`location_point` populated for homestay/restaurant/attraction; `latitude`/`longitude` for dynamics/activity/travel.

- [ ] **Step 6: If issues, fix and re-run with `--retry-failed`** (and `overwrite: true` to avoid dupes).

- [ ] **Step 7: Commit any fixes**

```bash
git add -A
git commit -m "fix: validation adjustments"
```

---

## Open Items (require user input before full run)

- **Moonshot RPM / 并发上限** → fill `config.yaml` `moonshot.rpm`.
- **Qiniu bucket / access_key / secret_key / domain** → fill `config.yaml`.
- **`goods_category_id`** real value → fill `config.yaml` `run.goods_category_id`.
- **MySQL credentials** → fill `config.yaml`.
- Confirm `vill_village_job` stays unused (per spec).
