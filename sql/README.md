# 表结构 SQL

把各目标表的 `CREATE TABLE` 语句放在这里，文件命名建议：

- `vill_village.sql` — 源村庄表结构（含村名、行政区划、村庄中心经纬度）
- `task_status.sql` — 处理状态表（本脚本自建）
- `vill_homestay.sql` — 民宿（子表：`vill_homestay_room.sql`）
- `vill_goods.sql` — 土特产
- `vill_dynamics.sql` — 动态
- `vill_village_activity.sql` — 活动（子表：活动日程`vill_village_activity_day.sql`，每日行程 `vill_village_activity_trip.sql`）
- `vill_village_travel.sql` — 旅游路线（子表：旅游日程`vill_village_activity_day.sql`，每日行程 `vill_village_activity_trip.sql`）
- `vill_restaurant.sql` — 农庄（农家乐）（子表：菜单 `vill_restaurant_dish.sql`）
- `vill_attraction.sql` — 景区
- `vill_village_sages.sql` — 乡贤和先贤
- `t_file.sql` — 文件表

## 说明

- 有子表的表，主表和子表 DDL 放同一个文件，用注释标明关系（外键字段）。
- 写代码前会先按这些 DDL 梳理字段映射，再实现各 `writers/*.py`。
