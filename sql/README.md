# 表结构 SQL

把各目标表的 `CREATE TABLE` 语句放在这里，文件命名建议：

- `source_villages.sql` — 源村庄表结构（含村名、行政区划、村庄中心经纬度）
- `task_status.sql` — 处理状态表（本脚本自建）
- `target_minsu.sql` — 民宿（含子表）
- `target_specialty.sql` — 土特产
- `target_news.sql` — 动态
- `target_activity.sql` — 活动
- `target_route.sql` — 旅游路线
- `target_farmhouse.sql` — 农庄（农家乐）
- `target_scenic.sql` — 景区

## 说明

- 有子表的表，主表和子表 DDL 放同一个文件，用注释标明关系（外键字段）。
- 写代码前会先按这些 DDL 梳理字段映射，再实现各 `writers/*.py`。
