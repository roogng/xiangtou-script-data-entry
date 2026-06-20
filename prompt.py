# prompt.py
_TEMPLATE = """请联网搜索「{place}」的以下乡村信息，并严格按照给定JSON格式返回。
每条信息附带图片URL；有坐标则返回经纬度，没有则省略坐标字段。
基本信息返回1条；其余每类最多3条，找不到返回空数组 []，不要编造。

返回JSON结构：
{{
  "basic_info": [{{"head_name":"村书记姓名","secretary_intro":"村书记介绍","contact_phone":"公开联系电话","village_intro":"村介绍","images":["http://..."]}}],
  "sages": [{{"type":"xiangxian","name":"姓名","intro":"介绍","images":[...]}}]],
  "minsu": [{{"title":"标题","intro":"介绍","images":[...],"lng":..,"lat":..,"rooms":[{{"room_name":"房号","room_type":1,"intro":"房型简介","price":..,"images":[...]}}]}}],
  "specialty": [{{"name":"商品名","price":数字,"detail":"详情介绍","category":"子类名","images":[...]}}],
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
- specialty 的 category 必须从以下子类名里选一个最贴近的：肉类/水果/蔬菜/牛奶/羊奶/谷类/面粉/食用油/果干/炒货/烘培类/陶瓷/藤类/布艺/茶叶/酒类/饮用水/蛋类
"""


def build_question(province, city, area, street, village):
    place = f"{province}{city}{area}{street}{village}"
    return _TEMPLATE.format(place=place)
