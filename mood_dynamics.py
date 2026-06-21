# mood_dynamics.py
"""Generate filler "心情动态" records when the LLM returns none for `news`
(vill_dynamics). Content is short mood/diary-style posts mentioning the village;
images are left empty and filled by the pipeline's image fallback chain.
"""
import random

from models import Record

_TEMPLATES = [
    "清晨的{v}被薄雾笼罩，空气里满是泥土和青草的清香，心情也跟着透亮起来。",
    "走在{v}的田埂上，远处炊烟升起，忽然觉得时间慢了下来。",
    "傍晚的{v}格外宁静，蝉鸣鸟叫交替响起，这是城市里听不到的安顿。",
    "在{v}的老树下乘凉，听老人讲过去的故事，满是烟火气。",
    "{v}的梯田层层叠叠，风吹过泛起绿浪，随手一拍就是壁纸。",
    "雨后的{v}空气清冽，山间云雾缭绕，像走进了一幅水墨画。",
    "{v}的清晨特别安静，只有鸡鸣狗吠，让人彻底放松下来。",
    "在{v}吃了一顿地道的农家饭，食材都是自家种的，鲜得掉眉毛。",
    "夜幕下的{v}点点灯火，远处传来虫鸣，这才是生活本来的样子。",
    "漫步在{v}的小路上，看夕阳把田野染成金色，一整天的疲惫都散了。",
]


def generate(village_name: str, n: int = 2):
    """Return n distinct mood-dynamic Records for the village."""
    name = village_name or "乡村"
    picks = random.sample(_TEMPLATES, min(n, len(_TEMPLATES)))
    return [Record(content=t.format(v=name), images=[]) for t in picks]
