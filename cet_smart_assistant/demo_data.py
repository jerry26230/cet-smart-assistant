"""共享的离线模拟资料；不读取或写入个人账户。"""

from dataclasses import asdict
from datetime import date, timedelta

from .models import StudentProfile
from .practice import PracticeRecord


def documents(today=None):
    today = today or date.today()
    student_a = StudentProfile(470, 115, 190, 165, 500, 90, 120, "listening")
    student_b = StudentProfile(470, 190, 115, 165, 500, 90, 120, "reading")
    history = []
    scores = {"listening": [75, 75, 75, 55, 58, 60, 55, 58, 60, 72, 75, 78],
              "reading": [70, 70, 70, 70, 70, 70, 75, 75, 75, 60, 60, 60]}
    for skill, values in scores.items():
        for index, score in enumerate(values):
            record = PracticeRecord((today-timedelta(days=11-index)).isoformat(), skill, 20,
                                    f"模拟练习 {index+1}", score, 100, "答辩模拟数据，不代表实测效果",
                                    "模拟同难度练习", True, 20)
            history.append({"record_version": 1, "id": f"demo-{skill}-{index}", **asdict(record)})
    def document(profile, rows):
        # 演示日期为生成当天后 90 天，仅为模拟目标，不冒充官方场次。
        profile.exam_date = (today + timedelta(days=90)).isoformat()
        return {"schema_version": 1, "profile": asdict(profile), "practice_history": rows}
    dynamic = StudentProfile(470, 115, 190, 165, 500, 90, 120, "feedback")
    before = [row for row in history if date.fromisoformat(row["day"]) <= today-timedelta(days=6)]
    return {"student-a.json": document(student_a, []), "student-b.json": document(student_b, []),
            "feedback-before.json": document(dynamic, before), "feedback-after.json": document(dynamic, history)}

