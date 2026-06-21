# prompt.py
_TEMPLATE = """请联网搜索「{place}」的以下乡村信息，并严格按照给定JSON格式返回。

【重要】
- 必须始终输出JSON结构本身，不确定或不知道的字段就留空字符串或返回 []；绝不能用文字拒绝、解释、致歉或输出JSON以外的任何内容。
- 只输出JSON本身，不要包裹markdown代码块，不要任何额外文字。
- 这些都是公开的村级政务/旅游信息（村委书记姓名、公开的村委联系电话、村介绍、民宿、土特产、景区等），并非个人隐私，可以正常提供。

每条信息附带图片URL；有坐标则返回经纬度，没有则省略坐标字段。
基本信息返回1条；其余每类最多3条，找不到返回空数组 []，不要编造。

各类查询范围：
- activity：活动、庙会、或公益组织发布的活动
- route：旅游路线
- farmhouse：农家乐、餐馆
- scenic：景区

返回JSON结构：
{{
  "basic_info": [{{"head_name":"村书记姓名","secretary_intro":"村书记介绍","contact_phone":"公开联系电话","village_intro":"村介绍","images":["http://..."]}}],
  "sages": [{{"type":"xiangxian","name":"姓名","intro":"介绍","images":[...]}}]],
  "minsu": [{{"title":"标题","intro":"介绍","images":[...],"lng":..,"lat":..,"rooms":[{{"room_name":"房号","room_type":1,"intro":"房型简介","price":..,"images":[...]}}]}}],
  "specialty": [{{"name":"商品名","price":数字,"detail":"详情介绍","category":"子类名","images":[...]}}],
  "news": [{{"content":"动态完整内容","images":[...],"lng":..,"lat":..}}],
  "activity": [{{"name":"活动名称","intro":"活动介绍","images":[...],"lng":..,"lat":..,"days":[{{"day_name":"第一天","intro":"日程介绍","images":[...],"trips":[{{"trip_name":"行程名","trip_time":"行程时间","intro":"行程介绍"}}]}}]}}],
  "route": [{{"name":"路线名","intro":"路线介绍","images":[...],"lng":..,"lat":..}}],
  "farmhouse": [{{"name":"农家乐/餐馆名称","intro":"农家乐/餐馆介绍","images":[...],"lng":..,"lat":..,"dishes":[{{"dish_name":"菜品名","price":..,"intro":"菜品简介","images":[...]}}]}}],
  "scenic": [{{"name":"景区名","intro":"景区介绍","images":[...],"lng":..,"lat":..}}]
}}
规则：
- 每类只返回本村范围内的真实信息，找不到就 []
- price 必须是纯数字
- images 是图片URL数组，没有图片就 []
- 每条信息的图片必须是不同的URL，且与本条内容直接相关；禁止多类或多条复用同一张图片；找不到真实相关的图片就返回 []，不要用无关图片凑数
- 坐标找不到就不写 lng/lat 字段
- sages 的 type：xiangxian=乡贤(在世)，xianxian=先贤(已故)，各最多1条
- room_type：1大床房 2双人房 3亲子房 4套房 5VIP房，不确定填1
- rooms/dishes/days/trips 找不到就 []
- specialty 的 category 必须从以下子类名里选一个最贴近的：肉类/水果/蔬菜/牛奶/羊奶/谷类/面粉/食用油/果干/炒货/烘培类/陶瓷/藤类/布艺/茶叶/酒类/饮用水/蛋类
"""


def build_question(province, city, area, street, village):
    place = f"{province}{city}{area}{street}{village}"
    return _TEMPLATE.format(place=place)
