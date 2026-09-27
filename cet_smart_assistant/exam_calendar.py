"""已公布笔试日期；离线使用，不按月份猜测未来官方日期。"""

from datetime import date

# 教育部教育考试院，核对日期：2026-09-27。
EXAMS = (
    ("2026 年上半年四六级笔试", "2026-06-13", "https://cet.neea.cn/html1/report/2603/2-1.htm"),
    ("2026 年下半年四六级笔试", "2026-12-12", "https://cet.neea.cn/xhtml1/report/2609/1-1.htm"),
)


def upcoming_exams(today=None):
    today = today or date.today()
    return tuple(item for item in EXAMS if date.fromisoformat(item[1]) >= today)


def countdown_text(exam_date, today=None):
    days = (date.fromisoformat(exam_date) - (today or date.today())).days
    if days > 0:
        return f"距离考试还有 {days} 天（每天自动更新）"
    if days == 0:
        return "今天是目标考试日，请按准考证安排应试。"
    return f"目标考试已过 {-days} 天，请选择下一场考试日期。"
