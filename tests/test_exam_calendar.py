from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

import test_profile
from cet_core.data_service import load_profile, save_profile
from cet_core.exam_calendar import upcoming_exams, countdown_text
from cet_core.recommendation import generate_study_plan
from cet_core.feedback import update_plan_from_practice


class ExamCalendarTests(unittest.TestCase):
    def profile(self, **changes):
        return test_profile.ProfileTests().profile(**changes)

    def test_daily_countdown_and_stage_change(self):
        p = self.profile(exam_date="2026-12-12", days_remaining=999)
        self.assertEqual(p.remaining_days(date(2026, 9, 27)), 76)
        self.assertEqual(p.remaining_days(date(2026, 9, 28)), 75)
        self.assertIn("基础积累", generate_study_plan(p, date(2026, 9, 27)).guidance)
        self.assertIn("专项训练", generate_study_plan(p, date(2026, 10, 13)).guidance)
        self.assertIn("考前整合", generate_study_plan(p, date(2026, 11, 28)).guidance)

    def test_leap_day_and_year_boundary(self):
        p = self.profile(exam_date="2028-03-01")
        self.assertEqual(p.remaining_days(date(2028, 2, 28)), 2)
        p.exam_date = "2027-01-01"
        self.assertEqual(p.remaining_days(date(2026, 12, 31)), 1)

    def test_exam_day_and_expired_do_not_roll_forward(self):
        p = self.profile(exam_date="2026-12-12", study_focus="feedback")
        for day in (date(2026, 12, 12), date(2026, 12, 13)):
            self.assertEqual(generate_study_plan(p, day).minutes, {})
            self.assertEqual(update_plan_from_practice(p, [], day).plan.minutes, {})
        self.assertIn("今天", countdown_text(p.exam_date, date(2026, 12, 12)))
        self.assertIn("已过 1 天", countdown_text(p.exam_date, date(2026, 12, 13)))
        self.assertEqual(p.exam_date, "2026-12-12")

    def test_published_calendar_does_not_guess_future(self):
        self.assertEqual(upcoming_exams(date(2026, 9, 27))[0][1], "2026-12-12")
        self.assertEqual(len(upcoming_exams(date(2026, 12, 12))), 1)
        self.assertEqual(upcoming_exams(date(2026, 12, 13)), ())

    def test_invalid_dates(self):
        for value in ("2026-02-29", "20261212", "2026-1-2", "bad", 123, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.profile(exam_date=value).validate()

    def test_storage_and_legacy_history_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "user_data.json"
            save_profile(path, self.profile())
            data = json.loads(path.read_text(encoding="utf-8"))
            del data["profile"]["exam_date"]
            data["practice_history"] = [{"legacy": "preserve"}]
            path.write_text(json.dumps(data), encoding="utf-8")
            old = load_profile(path)
            self.assertIsNone(old.exam_date)
            self.assertEqual(old.remaining_days(date(2030, 1, 1)), 90)
            old.exam_date = "2026-12-12"
            save_profile(path, old)
            loaded = load_profile(path)
            self.assertEqual(loaded.remaining_days(date(2026, 9, 28)), 75)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["practice_history"], data["practice_history"])
