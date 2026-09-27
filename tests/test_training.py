import unittest
from unittest.mock import patch
from types import SimpleNamespace
import sys

from test_anki_service import MemoryCollection
from cet_core.training import EXAMPLES, build_cards, import_training, recommend


class TrainingTests(unittest.TestCase):
    def test_recommendation_is_explicit_and_allows_non_vocabulary_causes(self):
        self.assertEqual(recommend("reading_words")[0], "reading")
        self.assertEqual(recommend("writing_expression")[0], "writing")
        for reason in ("unknown", "reading_structure", "writing_structure"):
            self.assertIsNone(recommend(reason)[0])
        with self.assertRaises(ValueError):
            recommend("low_score")

    def test_complete_distinct_examples_and_no_answer_in_writing_blank(self):
        reading, writing = build_cards("reading"), build_cards("writing")
        self.assertEqual(len(reading), 12)
        self.assertEqual(len(writing), 12)
        self.assertEqual(len(set(front for front, _ in reading + writing)), 24)
        for example, (front, back) in zip(EXAMPLES, writing):
            self.assertIn("___", front)
            self.assertNotIn(example[4], front)
            self.assertIn(example[5], back)
            self.assertIn("非真题", back)
        self.assertIn("促成", reading[0][1])
        self.assertIn("第三人称单数", writing[0][1])

    def test_import_and_repeat_keep_original_content(self):
        col = MemoryCollection()
        with patch.dict(sys.modules, {"anki.collection": SimpleNamespace(OpChanges=object, AddNoteRequest=SimpleNamespace)}):
            self.assertTrue(import_training(col, "writing").added)
            self.assertEqual(len(col.notes), 12)
            self.assertFalse(import_training(col, "writing").added)
            self.assertEqual(len(col.notes), 12)
            self.assertIn("cet_training_writing", col.notes[1].tags)
            self.assertIn("写作表达", col.deck["name"])

    def test_invalid_mode_does_not_write(self):
        col = MemoryCollection()
        with self.assertRaises(ValueError):
            import_training(col, "unknown")
        self.assertEqual(col.notes, {})
