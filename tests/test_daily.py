from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest
import test_profile
from cet_core.daily import ensure_day, load_days, record_result, select_words
from cet_core.data_service import DataError
from cet_core.recommendation import StudyPlan


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'user_data.json'
        self.day = date(2026, 9, 29)
        self.plan = StudyPlan(dict(vocabulary=4, listening=5, reading=10, writing=11), '', '')

    def test_snapshot_budget_and_reopen(self):
        tasks = ensure_day(self.path, self.plan, self.day)
        self.assertEqual(sum(t['minutes'] for t in tasks.values()), 30)
        self.assertEqual(len(tasks['reading']['items']), 2)
        other = StudyPlan(dict(reading=1), '', '')
        self.assertEqual(ensure_day(self.path, other, self.day), tasks)
        tomorrow = ensure_day(self.path, other, self.day + timedelta(days=1))
        self.assertEqual(sum(t['minutes'] for t in tomorrow.values()), 1)

    def test_tracks_independent_and_failure_priority(self):
        tasks = ensure_day(self.path, self.plan, self.day)
        word = tasks['reading']['items'][1]['word']
        record_result(self.path, self.day.isoformat(), 'reading', word, 'good', self.day)
        record_result(self.path, self.day.isoformat(), 'writing', word, 'again', self.day)
        _, days = load_days(self.path)
        tomorrow = self.day + timedelta(days=1)
        self.assertEqual(select_words(days, 'writing', tomorrow, 1)[0]['word'], word)
        self.assertNotEqual(select_words(days, 'reading', tomorrow, 1)[0]['word'], word)

    def test_completion_idempotent_and_partial(self):
        tasks = ensure_day(self.path, self.plan, self.day)
        word = tasks['reading']['items'][0]['word']
        record_result(self.path, self.day.isoformat(), 'reading', word, 'again', self.day)
        original = self.path.read_bytes()
        record_result(self.path, self.day.isoformat(), 'reading', word, 'good', self.day)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(load_days(self.path)[1][self.day.isoformat()]['reading']['done'])
        record_result(self.path, self.day.isoformat(), 'reading', tasks['reading']['items'][1]['word'], 'unsure', self.day)
        self.assertTrue(load_days(self.path)[1][self.day.isoformat()]['reading']['done'])

    def test_midnight_and_invalid_result_no_write(self):
        ensure_day(self.path, self.plan, self.day)
        before = self.path.read_bytes()
        for skill, word, rating, today in [('reading','contribute','good',self.day + timedelta(days=1)),
                                          ('reading','invalid','good',self.day), ('reading','contribute','wrong',self.day)]:
            with self.assertRaises(DataError):
                record_result(self.path, self.day.isoformat(), skill, word, rating, today)
            self.assertEqual(self.path.read_bytes(), before)

    def test_corrupt_records_preserved(self):
        ensure_day(self.path, self.plan, self.day)
        data = json.loads(self.path.read_text(encoding='utf-8'))
        data['daily_tasks'][self.day.isoformat()]['reading']['items'][0]['rating'] = 'invalid'
        self.path.write_text(json.dumps(data), encoding='utf-8')
        before = self.path.read_bytes()
        with self.assertRaises(DataError):
            ensure_day(self.path, self.plan, self.day)
        self.assertEqual(self.path.read_bytes(), before)

    def test_empty_plan_and_existing_data(self):
        self.assertEqual(ensure_day(self.path, StudyPlan({}, '', ''), self.day), {})
        self.assertFalse(self.path.exists())
        self.path.write_text(json.dumps(dict(schema_version=1, profile=None, practice_history=[], custom='keep')), encoding='utf-8')
        ensure_day(self.path, self.plan, self.day)
        self.assertEqual(load_days(self.path)[0]['custom'], 'keep')
