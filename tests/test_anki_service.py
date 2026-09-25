"""服务契约测试使用内存替身；真实 Anki 兼容性另作实机验收。"""

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

if "cet_core" not in sys.modules:
    spec = importlib.util.spec_from_loader("cet_core", loader=None, is_package=True)
    package = importlib.util.module_from_spec(spec)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "cet_smart_assistant")]
    sys.modules["cet_core"] = package

from cet_core.anki_service import DECK_NAME, add_vocabulary, create_deck, normalize_word, validate_card


class Note(dict):
    id = 0


class MemoryCollection:
    def __init__(self):
        self.deck = None
        self.model = None
        self.notes = {}
        self.undo_entries = []
        self.decks = SimpleNamespace(by_name=lambda name: self.deck, add_normal_deck_with_name=self.add_deck)
        self.models = SimpleNamespace(
            by_name=lambda name: self.model,
            new=lambda name: dict(name=name, type=0, flds=[], tmpls=[]),
            new_field=lambda name: dict(name=name),
            add_field=lambda model, field: model["flds"].append(field),
            new_template=lambda name: dict(name=name),
            add_template=lambda model, template: model["tmpls"].append(template),
            add_dict=self.add_model, get=lambda model_id: self.model,
            nids=lambda model_id: list(self.notes),
        )

    def add_deck(self, name):
        if not self.deck:
            self.deck = dict(id=1, name=name, dyn=0)
        return SimpleNamespace(id=1, changes=object())

    def add_model(self, model):
        model["id"] = 2
        self.model = model
        return SimpleNamespace(id=2)

    def new_note(self, model):
        return Note()

    def add_note(self, note, deck_id):
        note.id = len(self.notes) + 1
        note.deck_id = deck_id
        self.notes[note.id] = note

    def get_note(self, note_id):
        return self.notes[note_id]

    def add_custom_undo_entry(self, label):
        self.undo_entries.append(label)
        return len(self.undo_entries)

    def merge_undo_entries(self, undo_id):
        return object()


class AnkiServiceTests(unittest.TestCase):
    def setUp(self):
        self.col = MemoryCollection()
        # 只模拟变更类型，不把替身误当成真正的 Anki 数据库。
        self.patch = patch.dict(sys.modules, {"anki.collection": SimpleNamespace(OpChanges=object)})
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_deck_creation_is_idempotent(self):
        self.assertIn("已创建", create_deck(self.col).message)
        first = self.col.deck
        self.assertIn("已存在", create_deck(self.col).message)
        self.assertIs(self.col.deck, first)
        self.assertEqual(first["name"], DECK_NAME)

    def test_add_word_and_keep_existing_meaning(self):
        first = add_vocabulary(self.col, "abandon", "v. 放弃；抛弃")
        second = add_vocabulary(self.col, "  ABANDON  ", "另一释义")
        self.assertTrue(first.added)
        self.assertFalse(second.added)
        self.assertEqual(first.note_id, second.note_id)
        self.assertEqual(len(self.col.notes), 1)
        self.assertEqual(self.col.get_note(first.note_id)["Back"], "v. 放弃；抛弃")
        self.assertEqual(len(self.col.undo_entries), 1)

    def test_duplicate_after_moving_card(self):
        first = add_vocabulary(self.col, "take  off", "起飞")
        self.col.get_note(first.note_id).deck_id = 99
        result = add_vocabulary(self.col, "take\noff", "脱下")
        self.assertFalse(result.added)
        self.assertEqual(self.col.get_note(first.note_id).deck_id, 99)

    def test_html_and_quotes_are_literal(self):
        result = add_vocabulary(self.col, '<word "x">', '<script>alert(1)</script>\nA & B')
        note = self.col.get_note(result.note_id)
        self.assertEqual(note["Front"], '&lt;word &quot;x&quot;&gt;')
        self.assertEqual(note["Back"], '&lt;script&gt;alert(1)&lt;/script&gt;<br>A &amp; B')
        self.assertFalse(add_vocabulary(self.col, '<word "x">', "new").added)

    def test_invalid_inputs_do_not_create_decks_or_models(self):
        for word, meaning in [("", "x"), ("word", " \n"), ("a" * 201, "x"),
                              ("word", "a" * 5001), ("a\x00", "x"), (None, "x")]:
            with self.subTest(word=word), self.assertRaises(ValueError):
                add_vocabulary(self.col, word, meaning)
        self.assertIsNone(self.col.deck)
        self.assertIsNone(self.col.model)

    def test_filtered_deck_conflict_is_not_modified(self):
        self.col.deck = dict(name=DECK_NAME, dyn=1)
        with self.assertRaises(ValueError):
            add_vocabulary(self.col, "abandon", "放弃")
        self.assertIsNone(self.col.model)
        self.assertEqual(self.col.deck["dyn"], 1)

    def test_modified_template_is_not_overwritten(self):
        add_vocabulary(self.col, "abandon", "放弃")
        self.col.model["tmpls"][0]["qfmt"] = "用户模板"
        with self.assertRaises(ValueError):
            add_vocabulary(self.col, "ability", "能力")
        self.assertEqual(self.col.model["tmpls"][0]["qfmt"], "用户模板")
        self.assertEqual(len(self.col.notes), 1)

    def test_unicode_normalization_and_validation(self):
        self.assertEqual(normalize_word(" ＡＢＡＮＤＯＮ "), "abandon")
        self.assertEqual(validate_card("take\t off", "  起飞  "), ("take off", "起飞"))


if __name__ == "__main__":
    unittest.main()
