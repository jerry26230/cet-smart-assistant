"""Daily task snapshots and independent, self-assessed practice tracks."""
from datetime import date

from .data_service import DataError, load_document, save_document
from .training import EXAMPLES, MODES
from .practice_variants import VARIANTS, CAUSES, HINTS

WORDS = {row[0]: row for row in EXAMPLES}
RATINGS = {"again": "还不会", "unsure": "不熟练", "good": "本次独立完成"}
LABELS = {"vocabulary": "Anki 词汇复习", "listening": "听力与复盘", **MODES}


def load_days(path):
    document = load_document(path)
    days = document.get("daily_tasks", {})
    try:
        if not isinstance(days, dict):
            raise ValueError()
        for day, tasks in days.items():
            date.fromisoformat(day)
            if not isinstance(tasks, dict) or not set(tasks) <= set(LABELS):
                raise ValueError()
            for skill, task in tasks.items():
                if type(task["minutes"]) is not int or not 1 <= task["minutes"] <= 1440 or type(task["done"]) is not bool:
                    raise ValueError()
                if not isinstance(task["items"], list) or len(task["items"]) > 3:
                    raise ValueError()
                seen = set()
                for item in task["items"]:
                    if (skill not in MODES or item["word"] not in WORDS or item["word"] in seen
                            or item["rating"] not in (None, *RATINGS) or not isinstance(item["reason"], str)):
                        raise ValueError()
                    seen.add(item["word"])
                    if item.get("cause", "") not in CAUSES or item.get("hint", "") not in ("", *HINTS.values()):
                        raise ValueError()
                    if type(item.get("variant", 0)) is not int or item.get("variant", 0) not in (0, 1):
                        raise ValueError()
                    if not isinstance(item.get("draft", ""), str) or len(item.get("draft", "")) > 5000:
                        raise ValueError()
                if skill in MODES and (not task["items"] or task["done"] != all(i["rating"] is not None for i in task["items"])):
                    raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise DataError("每日任务记录无效，原文件保持不变，请先备份并检查。") from None
    return document, days


def select_words(days, skill, today, count):
    latest = {}
    previous_items = {}
    for day, tasks in sorted(days.items()):
        if day >= today.isoformat():
            continue
        for item in tasks.get(skill, {}).get("items", []):
            if item["rating"]:
                latest[item["word"]] = (day, item["rating"])
                previous_items[item["word"]] = item
    def rank(word):
        day, rating = latest.get(word, ("", None))
        return ({"again": 0, None: 1, "unsure": 2, "good": 3}[rating], day, list(WORDS).index(word))
    selected = []
    for word in sorted(WORDS, key=rank)[:count]:
        previous = latest.get(word)
        reason = "这个方向尚无练习记录" if not previous else f"{previous[0]} · {RATINGS[previous[1]]}"
        last = previous_items.get(word, {})
        cause = last.get("cause", "") if last.get("rating") != "good" else ""
        if cause:
            reason += "；上次错因：" + CAUSES[cause]
        selected.append(dict(word=word, reason=reason, rating=None,
                             variant=1 - last.get("variant", 0) if last else 0,
                             hint=HINTS.get(cause, "")))
    return selected


def ensure_day(path, plan, today=None):
    today = today or date.today()
    document, days = load_days(path)
    key = today.isoformat()
    if key in days:
        return days[key]
    if not plan.minutes:
        return {}
    tasks = {}
    for skill, minutes in plan.minutes.items():
        if minutes <= 0:
            continue
        items = select_words(days, skill, today, min(3, max(1, minutes // 5))) if skill in MODES else []
        tasks[skill] = dict(minutes=minutes, done=False, items=items)
    days[key] = tasks
    document["daily_tasks"] = days
    save_document(path, document)
    return tasks


def record_result(path, day, skill, word=None, rating=None, today=None, cause=""):
    if day != (today or date.today()).isoformat():
        raise DataError("日期已变化，请关闭并重新打开今日任务。")
    document, days = load_days(path)
    try:
        task = days[day][skill]
        if skill in MODES:
            if rating not in RATINGS or cause not in CAUSES:
                raise ValueError()
            item = next(item for item in task["items"] if item["word"] == word)
            # One result per task item; reopening or double-clicking cannot inflate history.
            if item["rating"] is not None:
                return
            item["rating"] = rating
            item["cause"] = cause if rating != "good" else ""
            task["done"] = all(i["rating"] is not None for i in task["items"])
        else:
            task["done"] = True
    except (KeyError, ValueError, StopIteration):
        raise DataError("任务不存在或练习结果无效，请重新打开今日任务。") from None
    save_document(path, document)


def exercise(word, skill, variant=0):
    sentence, meaning, prompt, answer, completed, usage = VARIANTS[word] if variant == 1 else WORDS[word][1:]
    if skill == "reading":
        return f"{sentence}\n\n{word} 在这句话中是什么意思？", f"{meaning}\n\n{usage}"
    return prompt, f"参考：{answer}\n{completed}\n\n{usage}\n其他符合语境、语法正确的表达也可能成立。"


def save_draft(path, day, skill, word, draft):
    """Drafts may be flushed after midnight to their original task, never as results."""
    if not isinstance(draft, str) or len(draft) > 5000:
        raise DataError("作答草稿最多 5000 字，请缩短后保存。")
    document, days = load_days(path)
    try:
        item = next(i for i in days[day][skill]["items"] if i["word"] == word)
    except (KeyError, StopIteration):
        raise DataError("原任务不存在，无法保存草稿。") from None
    if item.get("draft", "") != draft:
        item["draft"] = draft
        save_document(path, document)


def undo_result(path, day, skill, word=None, today=None):
    if day != (today or date.today()).isoformat():
        raise DataError("只能撤销今天的评价，请重新打开今日任务。")
    document, days = load_days(path)
    try:
        task = days[day][skill]
        if skill in MODES:
            item = next(i for i in task["items"] if i["word"] == word)
            item["rating"] = None
            item.pop("cause", None)
        task["done"] = False
    except (KeyError, StopIteration):
        raise DataError("任务不存在，请重新打开今日任务。") from None
    save_document(path, document)
