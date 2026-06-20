# 乡村数据自动化录入系统 — 设计文档

- 日期：2026-06-20
- 状态：已通过设计评审，待写实现计划

## 1. 背景与目标

代替手工操作，自动化为另一平台录入乡村信息。

**手工现状**：

1. 通过 Kimi 2.6 大模型提问，获得相关数据。
2. 登录目标平台，手动复制数据填表单，点保存。

**自动化目标**：脚本读源村庄数据 → 调 Kimi 提问 → 解析返回 → 图片传七牛云 → 直接写目标 MySQL 库（不走平台表单）。

**范围**：只处理「精品村」子集（通过 ID 清单提供），非全部 60 万村庄。

## 2. 关键决策汇总

| 维度       | 决策                                                |
| -------- | ------------------------------------------------- |
| 架构       | 方案 A：单进程线性管道 + 状态表续跑，并发做成可配置参数（默认 1）              |
| Kimi 图片  | Moonshot 官方 API 联网搜索，返回图片 URL，脚本下载后传七牛            |
| 目标库      | 有直写权限 + 表结构，DDL 放 `sql/`                          |
| 源村庄      | 村名 + 行政区划，拼完整地名提问；与目标表同一 MySQL 库                  |
| 七牛       | 有 bucket + 路径规则 `public/common/{UUID}.jpg` + 参考数据 |
| Kimi API | Moonshot 官方 API，有 Key 知限额（具体 RPM 写代码前提供）          |
| 运行       | 单机 + 状态表断点续跑；先小批量验证再全量                            |
| GPS      | Kimi 返回坐标优先，没有则用源表村庄中心坐标兜底                        |
| 精品村      | 提供 ID 清单（`village_ids.txt`）                       |
| 数据量约束    | 基本信息 1 条；其余每类最多 3 条；找不到返回 `[]`                    |
| 图片存储     | 独立 `file` 表；业务表 text 字段存逗号分隔的 file_key            |
| 图片压缩     | >1MB 用 Pillow 压缩到 1MB 以内                          |
| 容错       | 单图/单条缺失跳过，不整村失败                                   |

## 3. 类别 → 目标表映射

共 9 类，对应平台表（编号沿用用户提供的平台编号）：

| #   | 类别   | JSON key     | 关键字段             | 数量  | 坐标  | 图片  |
| --- | ---- | ------------ | ---------------- | --- | --- | --- |
| 6   | 基本信息 | `basic_info` | 村书记介绍、公开联系电话、村介绍 | 1   | 否   | 是   |
| 7   | 村贤   | `sages`      | 乡贤(在世)、先贤(已故)    | 各1  | 否   | 是   |
| 1   | 民宿   | `minsu`      | 标题、介绍            | ≤3  | 是   | 是   |
| 2   | 土特产  | `specialty`  | 商品名、价格(纯数字)、详情   | ≤3  | 否   | 是   |
| 3   | 动态   | `news`       | 完整内容             | ≤3  | 是   | 是   |
| 4   | 活动   | `activity`   | 名称、介绍            | ≤3  | 是   | 是   |
| 5   | 旅游路线 | `route`      | 名称、介绍            | ≤3  | 是   | 是   |
| 8   | 农庄   | `farmhouse`  | 名称、介绍            | ≤3  | 是   | 是   |
| 9   | 景区   | `scenic`     | 名称、介绍            | ≤3  | 是   | 是   |

> 注：基本信息、村贤的目标表名以用户提供的 DDL 为准；坐标需求按本表（基本信息/村贤/土特产不需要坐标）。

## 4. 整体架构

### 4.1 处理管道（单村庄）

```
读源表取一个 pending 村庄
  → 拼「省市区县+村名」构造提问
  → 调 Moonshot API（联网搜索）要求返回结构化 JSON
  → 解析 JSON，得到 9 类数据 + 图片URL + 坐标
  → 逐张下载图片URL → 压缩(>1MB) → 上传七牛 → INSERT file表 → 得 file_key
  → GPS：Kimi有则用，无则用源表村庄坐标
  → 按 9 张目标表 DDL 组装记录，file_key 逗号拼接写入业务表图片字段
  → 更新 task_status = done
任何不可恢复环节失败 → task_status = failed + error_msg，跳过继续下一村
```

### 4.2 项目结构

```
data-entry/
├── config.yaml                  # 配置：DB、Moonshot Key、七牛 Key、并发、限流
├── config_loader.py             # 读配置
├── db.py                        # MySQL 读写封装（源库/目标库同一实例）
├── kimi_client.py               # Moonshot API 调用 + 限流 + 重试
├── prompt.py                    # 构造提问 + 约束 JSON 输出格式
├── parser.py                    # 解析 Kimi JSON → 结构化 dataclass
├── qiniu_uploader.py            # 下载 → 压缩 → 上传七牛 → 返回 file_key
├── geo.py                       # GPS 兜底（Kimi坐标 vs 村庄坐标）
├── file_repo.py                 # file 表写入
├── writers/                     # 每张目标表一个 writer
│   ├── basic_info.py
│   ├── sages.py
│   ├── minsu.py
│   ├── specialty.py
│   ├── news.py
│   ├── activity.py
│   ├── route.py
│   ├── farmhouse.py
│   └── scenic.py
├── models.py                    # dataclass 数据对象，各类字段定义
├── pipeline.py                  # 主流程编排：单村庄处理
├── runner.py                    # 入口：取村庄、调 pipeline、写状态
├── status_repo.py               # task_status 表读写
├── village_ids.txt              # 精品村 ID 清单
├── requirements.txt
├── sql/                         # 表结构 DDL
└── tests/
    ├── test_parser.py
    ├── test_writers.py
    ├── test_qiniu.py
    └── fixtures/                # Kimi 返回样例 JSON、表 DDL
```

**设计要点**：

- `writers/` 一表一文件，字段差异独立处理，好测好改。
- `pipeline.py` 只编排，不含业务细节。
- `task_status` 是续跑核心，由 `status_repo` 独立管理。
- 子表（若有）主表先 INSERT 拿自增 id → 外键 INSERT 子表，事务包裹。

## 5. 数据模型

### 5.1 源村庄表（用户提供 DDL，预期字段）

| 字段            | 用途                   |
| ------------- | -------------------- |
| `id`          | 村庄主键，task_status 关联键 |
| 村名            | 拼 Kimi 提问            |
| 省/市/县/乡镇等行政区划 | 拼 Kimi 提问            |
| `lng` / `lat` | 村庄中心经纬度，GPS 兜底       |

### 5.2 task_status 表（脚本自建）

```sql
CREATE TABLE task_status (
  village_id      BIGINT PRIMARY KEY,
  status          VARCHAR(16) NOT NULL,   -- pending / done / failed
  error_msg       TEXT,
  retry_count     INT DEFAULT 0,
  records_written INT DEFAULT 0,
  raw_response    MEDIUMTEXT,             -- Kimi 原始返回，便于排查
  started_at      DATETIME,
  finished_at     DATETIME,
  INDEX idx_status (status)
);
```

续跑逻辑：启动 `SELECT village_id FROM task_status WHERE status='done'` 得已完成集合 → 从 ID 清单过滤 → 新村庄插 `pending` → 处理完更新 `done/failed`。崩了重启自动接着跑。

### 5.3 file 表（用户提供 DDL）

字段：file_type、file_name、file_size、file_key、creator、create_time 等。

### 5.4 业务表（用户提供 DDL，共 9 张）

每张表包含：

- 业务字段（标题/介绍/价格等）
- 图片 text 字段（如 `goods_imgs`），存逗号分隔的 file_key
- 坐标字段 `lng`/`lat`（基本信息、村贤、土特产除外）
- 关联字段（村庄 id、子表外键等）

### 5.5 统一字段（所有业务表共有，字段名相同）

各业务表都含以下统一字段，代码侧抽成公共基类，所有 writer 统一注入默认值：

| 字段 | 默认值 |
|------|--------|
| `create_user_id` | 43 |
| `approve_status` | 2 |
| `create_time` | now() |
| `update_time` | now() |
| `online` | 1 |
| `approve_id` | 43 |
| `homeowner_id` | 4 |
| `shopId` | 2 |
| `comment_code` | UUID 生成 |

> 注：`comment_code` 每条记录生成一个新 UUID。这些字段是否在 9 张表里全部出现、有无例外，以用户 DDL 为准；writer 实现时按各表实际字段动态写入（基类提供默认值，表里没该字段则跳过）。

## 6. Kimi 提问与解析

### 6.1 提问构造

拼入完整地名，要求严格 JSON：

```
请联网搜索「{省}{市}{县}{村名}」的以下乡村信息，并严格按照给定JSON格式返回。
每条信息附带图片URL；有坐标则返回经纬度，没有则省略坐标字段。
基本信息返回1条；其余每类最多3条，找不到返回空数组 []，不要编造。

返回JSON结构：
{
  "basic_info": [{"secretary_intro":"...","contact_phone":"...","village_intro":"...","images":["http://..."]}],
  "sages": [{"type":"xiangxian","name":"...","intro":"...","images":[...]}, {"type":"xianxian","name":"...","intro":"...","images":[...]}],
  "minsu": [{"title":"...","intro":"...","images":[...],"lng":...,"lat":...}],
  "specialty": [{"name":"...","price":数字,"detail":"...","images":[...]}],
  "news": [{"content":"...","images":[...],"lng":...,"lat":...}],
  "activity": [{"name":"...","intro":"...","images":[...],"lng":...,"lat":...}],
  "route": [{"name":"...","intro":"...","images":[...],"lng":...,"lat":...}],
  "farmhouse": [{"name":"...","intro":"...","images":[...],"lng":...,"lat":...}],
  "scenic": [{"name":"...","intro":"...","images":[...],"lng":...,"lat":...}]
}
规则：
- 每类只返回本村范围内的真实信息，找不到就 []
- price 必须是纯数字
- images 是图片URL数组，没有图片就 []
- 坐标找不到就不写 lng/lat 字段
- sages 的 type：xiangxian=乡贤(在世)，xianxian=先贤(已故)，各最多1条
```

### 6.2 Moonshot API 调用

- 模型 `moonshot-v1-auto`（或用户指定），开启联网搜索。
- `response_format` 强制 JSON 输出。
- `kimi_client.py`：限流（按 RPM 令牌桶/时间窗）、超时重试（指数退避，最多 N 次）、记录原始返回。

### 6.3 解析（parser.py）

- 剥离可能的 ```json 代码块包裹再 `json.loads`。
- 解析失败 → 抛异常 → pipeline 捕获 → `task_status=failed`，保留 raw_response。
- 解析成 `models.py` dataclass 交给 writers。
- 容错：单条记录字段缺失/非法 → 跳过该条，其余继续，记 warning。

## 7. 图片管道

```
Kimi 返回 images:["http://..."]
  → 逐张处理：
      1. HTTP 下载到内存（超时+大小上限，防卡死/超大）
      2. 下载失败 → 跳过该图，warning，不影响该条记录
      3. 若 >1MB → Pillow 压缩到 1MB 以内
      4. 上传七牛 key = public/common/{UUID}.jpg
      5. INSERT file 表（file_type,file_name,file_size,file_key,creator,create_time）→ 得 file_key
  → 收集所有 file_key，逗号拼接 → 写入业务表图片 text 字段（如 goods_imgs）
```

**要点**：

- 路径规则 `public/common/{UUID}.jpg`，UUID 生成。
- 幂等：七牛同 key 覆盖；`--overwrite` 模式重跑前按村庄 id 删除旧业务数据。
- 失败隔离：图片失败绝不拖垮数据写入，图片字段留空，文字照常入库。
- 压缩：Pillow，按质量递减直到 <1MB。

## 8. GPS 处理

- Kimi 返回 `lng`/`lat` 则直接用。
- 未返回 → 用源表村庄中心 `lng`/`lat` 兜底（`geo.py`）。
- 基本信息、村贤、土特产不需要坐标，跳过。

## 9. 错误处理与隔离

| 层级               | 失败处理                                |
| ---------------- | ----------------------------------- |
| 单张图片下载/上传失败      | 跳过该图，warning，其余继续                   |
| 单条记录字段缺失/非法      | 跳过该条，其余继续                           |
| Kimi 调用失败（超时/限流） | 指数退避重试 N 次，仍失败→本村 failed            |
| JSON 解析失败        | 本村 failed，保留 raw_response           |
| 某类写入 DB 失败       | 事务回滚该类，本村 failed                    |
| 整个村庄处理           | 成功→done；不可恢复→failed+error_msg，继续下一村 |

原则：能跳过的不整村失败；不可恢复的标记 failed 不阻塞其他村庄。

## 10. 续跑与幂等

- 启动读 `village_ids.txt` → 过滤 `task_status=done` → 得待处理队列。
- `failed` 村庄：`--retry-failed` 重新跑（retry_count+1）。
- `--overwrite` 模式：写前先按村庄 id 删除该村庄旧业务数据再写，保证幂等。验证期建议开启。

## 11. 配置 config.yaml

```yaml
mysql:
  host: ...
  port: 3306
  user: ...
  password: ...
  database: ...
moonshot:
  api_key: ...
  model: moonshot-v1-auto
  rpm: 60
  max_retries: 3
  timeout: 120
qiniu:
  access_key: ...
  secret_key: ...
  bucket: ...
  domain: ...
  image_path_template: "public/common/{uuid}.jpg"
  max_size_bytes: 1048576
run:
  concurrency: 1
  village_ids_file: village_ids.txt
  overwrite: true
```

## 12. 测试与验证

1. **单测**（不依赖真实 API）：
   - `test_parser.py`：Kimi 样例 JSON 测解析、容错（代码块包裹、字段缺失、空数组）。
   - `test_writers.py`：mock DB 测各表+file表写入顺序、逗号拼接、事务。
   - `test_qiniu.py`：测压缩（>1MB 压到 <1MB）和 key 生成。
2. **小批量验证**：跑 10 个精品村，人工抽查入库数据和图片，确认 Kimi 返回质量、字段映射、图片显示。
3. **全量**：验证通过后调 `concurrency`，跑 `village_ids.txt`。

## 13. 依赖

`pymysql`、`moonshot-python`（或 `openai` SDK 兼容 Moonshot）、`qiniu`、`Pillow`、`pyyaml`、`pytest`

## 14. 写代码前需用户提供

- [ ] 9 张业务表 + file 表 + 源村庄表的 DDL（放 `sql/`，子表同文件注释标外键）
- [ ] Moonshot 实际 RPM / 并发上限
- [ ] 七牛 bucket / access_key / secret_key / domain
- [ ] 各业务表的图片 text 字段名（如 goods_imgs）确认
- [ ] file 表 creator 字段取值约定（脚本固定值？）
- [ ] 源村庄表的行政区划字段名 + 村庄中心经纬度字段名
- [ ] 需填默认值的字段清单（表.字段 → 默认值，例如 `minsu.status=1`、`file.creator='system'`）
- [x] 各表统一字段（字段名在所有表相同）及其默认值 — 已提供，见 §5.5
