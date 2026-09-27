from dataclasses import replace
from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest

import test_anki_service
from cet_core.models import StudentProfile
from cet_core.practice import PracticeRecord, append_record, read_records
from cet_core.data_service import save_profile, load_profile
from cet_core.feedback import update_plan_from_practice


class FeedbackTests(unittest.TestCase):
    def profile(self, minutes=120):
        return StudentProfile(470, 115, 190, 165, 500, 90, minutes, "feedback")

    def records(self, skill="reading", scores=(80, 80, 80, 60, 60, 60), group="同难度练习"):
        return [PracticeRecord((date.today()-timedelta(days=5-i)).isoformat(), skill, 20,
                               f"练习{i}", score, 100, comparison_group=group, comparable=True,
                               questions=20) for i, score in enumerate(scores)]

    def test_decline_changes_plan_and_improvement_releases_focus(self):
        result = update_plan_from_practice(self.profile(), self.records())
        self.assertEqual(result.focused, ("reading",))
        self.assertEqual(result.plan.minutes, dict(vocabulary=24, listening=24, reading=48, writing=24))
        result = update_plan_from_practice(self.profile(), self.records(scores=(50, 50, 50, 70, 70, 70)))
        self.assertEqual(result.focused, ())
        self.assertEqual(result.plan.minutes["reading"], 32)

    def test_listening_improves_reading_declines(self):
        records = self.records("listening", (55, 58, 60, 72, 75, 78)) + self.records("reading", (75, 75, 75, 60, 60, 60))
        result = update_plan_from_practice(self.profile(), records)
        self.assertEqual(result.focused, ("reading",))
        self.assertTrue(any("改善" in line for line in result.trends))

    def test_unconfirmed_unscored_old_and_insufficient_records_do_not_adjust(self):
        variants = [[], self.records()[:5], [replace(r, comparable=False) for r in self.records()],
                    [replace(r, comparable=False, score=None, maximum=None) for r in self.records()],
                    [replace(r, day=(date.today()-timedelta(days=40+i)).isoformat()) for i, r in enumerate(self.records())]]
        for records in variants:
            self.assertEqual(update_plan_from_practice(self.profile(), records).focused, ())

    def test_distinct_days_and_group_scale_question_isolation(self):
        self.assertFalse(update_plan_from_practice(self.profile(), [replace(r, day=date.today().isoformat()) for r in self.records()]).focused)
        for field, value in (("comparison_group", "另一组"), ("maximum", 200), ("questions", 10)):
            rows = self.records()
            rows[-1] = replace(rows[-1], **{field: value})
            self.assertFalse(update_plan_from_practice(self.profile(), rows).focused)

    def test_conflicting_groups_do_not_select_direction(self):
        rows = self.records(group="A") + self.records(scores=(60, 60, 60, 80, 80, 80), group="B")
        result = update_plan_from_practice(self.profile(), rows)
        self.assertFalse(result.focused)
        self.assertTrue(any("不一致" in line for line in result.trends))

    def test_threshold_and_time_conservation(self):
        rows = self.records(scores=(70, 70, 70, 65, 65, 65))
        self.assertEqual(update_plan_from_practice(self.profile(), rows).focused, ("reading",))
        rows += self.records("listening")
        for minutes in range(1, 1441):
            result = update_plan_from_practice(self.profile(minutes), rows)
            self.assertEqual(sum(result.plan.minutes.values()), minutes)
            self.assertTrue(all(type(v) is int and v >= 0 for v in result.plan.minutes.values()))

    def test_same_day_weight_and_input_order_independence(self):
        rows = self.records()
        result = update_plan_from_practice(self.profile(), rows)
        self.assertEqual(result, update_plan_from_practice(self.profile(), list(reversed(rows))))
        self.assertEqual(result, update_plan_from_practice(self.profile(), rows + [rows[-1]] * 20))

    def test_legacy_records_and_feedback_profile_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"user_data.json"
            save_profile(path, self.profile())
            append_record(path, self.records()[0])
            data = json.loads(path.read_text(encoding="utf-8"))
            for key in ("comparison_group", "comparable", "questions"):
                del data["practice_history"][0][key]
            path.write_text(json.dumps(data), encoding="utf-8")
            rows, skipped = read_records(path)
            self.assertEqual(skipped, 0)
            self.assertFalse(rows[0].comparable)
            self.assertEqual(load_profile(path).study_focus, "feedback")

    def test_comparability_requires_named_scored_group(self):
        for record in (replace(self.records()[0], comparison_group=" "),
                       replace(self.records()[0], score=None, maximum=None),
                       replace(self.records()[0], questions=0)):
            with self.assertRaises(ValueError):
                record.validate()
