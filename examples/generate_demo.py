"""生成独立答辩资料，不访问个人账户。python examples/generate_demo.py --output 路径"""

import argparse
from dataclasses import asdict
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_loader("cet_demo", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "cet_smart_assistant")]
sys.modules["cet_demo"] = package
from cet_demo.models import StudentProfile
from cet_demo.practice import PracticeRecord


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    target = parser.parse_args().output
    target.mkdir(parents=True, exist_ok=True)
    docs = documents()
    if any((target/name).exists() for name in docs):
        raise SystemExit("输出目录中已有同名文件，请选择新目录。")
    for name, data in docs.items():
        with (target/name).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    print(f"已生成 {len(docs)} 份模拟资料：{target.resolve()}")
