from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_anki_service
from cet_core.data_service import DataError, load_document, load_profile, save_profile
from cet_core.models import StudentProfile
from cet_core.practice import PracticeRecord, append_record, read_records, summarize


class PracticeTests(unittest.TestCase):
    def record(self, **changes):
        values = dict(day=date.today().isoformat(), skill="reading", minutes=25, title="阅读练习", score=8, maximum=10)
        return PracticeRecord(**{**values, **changes})

    def test_validation(self):
        for changes in ({"day": "invalid"}, {"day": (date.today()+timedelta(days=1)).isoformat()},
                        {"skill": "other"}, {"minutes": True}, {"minutes": 0}, {"minutes": 1.5},
                        {"title": " "}, {"score": 11}, {"maximum": 0}, {"score": float("nan")},
                        {"score": None}, {"note": "x"*2001}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.record(**changes).validate()
        self.record(score=None, maximum=None).validate()
        self.record(score=0).validate()

    def test_roundtrip_profile_and_repeated_submit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"user_data.json"
            profile = StudentProfile(470, 115, 190, 165, 500, 90, 120)
            save_profile(path, profile)
            self.assertTrue(append_record(path, self.record(), "same-submit"))
            self.assertFalse(append_record(path, self.record(), "same-submit"))
            self.assertEqual(read_records(path), ([self.record()], 0))
            self.assertEqual(load_profile(path), profile)
            profile.cet6_target = 550
            save_profile(path, profile)
            self.assertEqual(len(read_records(path)[0]), 1)

    def test_legacy_preserved_and_excluded_from_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"user_data.json"
            old = {"category": "listening", "accuracy": 0.6}
            path.write_text(json.dumps(dict(schema_version=1, profile=None, practice_history=[old])), encoding="utf-8")
            append_record(path, self.record())
            records, skipped = read_records(path)
            self.assertEqual(skipped, 1)
            self.assertEqual(load_document(path)["practice_history"][0], old)
            self.assertEqual(summarize(records)["reading"], {"count": 1, "minutes": 25})

    def test_corruption_and_failed_replace_preserve_original(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"user_data.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(DataError):
                append_record(path, self.record())
            self.assertEqual(path.read_text(), "{broken")
            path.write_text(json.dumps(dict(schema_version=1, profile=None, practice_history=[])))
            before = path.read_bytes()
            with patch("cet_core.data_service.os.replace", side_effect=PermissionError("test")):
                with self.assertRaises(DataError):
                    append_record(path, self.record())
            self.assertEqual(path.read_bytes(), before)

    def test_no_profile_required_and_latest_first(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"nested"/"user_data.json"
            append_record(path, self.record(title="第一次"))
            append_record(path, self.record(title="第二次", score=None, maximum=None))
            records, skipped = read_records(path)
            self.assertEqual([r.title for r in records], ["第二次", "第一次"])
            self.assertEqual(summarize(records)["reading"]["minutes"], 50)
            self.assertIsNone(load_profile(path))
