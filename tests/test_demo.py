from datetime import date, timedelta
import unittest
from unittest.mock import patch
import test_profile  # 加载独立纯 Python 包，不执行 Anki 入口。

from cet_core.demo_data import documents
from cet_core.models import StudentProfile
from cet_core.practice import PracticeRecord
from cet_core.recommendation import generate_study_plan
from cet_core.feedback import update_plan_from_practice


class DemoTests(unittest.TestCase):
    def test_same_total_different_confirmed_focus(self):
        today = date(2026, 9, 27)
        data = documents(today)
        a, b = (StudentProfile(**data[key]["profile"]) for key in ("student-a.json", "student-b.json"))
        self.assertEqual(a.cet4_total, b.cet4_total)
        self.assertEqual(generate_study_plan(a, today).minutes, dict(vocabulary=24, listening=48, reading=24, writing=24))
        self.assertEqual(generate_study_plan(b, today).minutes, dict(vocabulary=24, listening=24, reading=48, writing=24))

    def test_dynamic_scenarios_use_real_feedback(self):
        for today in (date(2026, 9, 27), date(2028, 2, 29), date(2030, 12, 31)):
            class Clock(date):
                @classmethod
                def today(cls):
                    return today
            data = documents(today)
            for key, skill, count in (("feedback-before.json", "listening", 12), ("feedback-after.json", "reading", 24)):
                doc = data[key]
                records = [PracticeRecord(**{k: v for k, v in row.items() if k not in ("id", "record_version")}) for row in doc["practice_history"]]
                self.assertEqual(len(records), count)
                with patch("cet_core.practice.date", Clock):
                    result = update_plan_from_practice(StudentProfile(**doc["profile"]), records, today)
                self.assertEqual(result.focused, (skill,))
                self.assertEqual(result.plan.minutes[skill], 48)
                self.assertEqual(sum(result.plan.minutes.values()), 120)

    def test_fresh_documents_and_relative_dates(self):
        today = date(2026, 12, 31)
        data = documents(today)
        self.assertEqual(data, documents(today))
        for doc in data.values():
            self.assertEqual(doc["profile"]["exam_date"], (today + timedelta(days=90)).isoformat())
        data["student-a.json"]["profile"]["daily_minutes"] = 1
        self.assertEqual(documents(today)["student-a.json"]["profile"]["daily_minutes"], 120)
        self.assertTrue(all("模拟" in row["note"] for row in data["feedback-after.json"]["practice_history"]))
