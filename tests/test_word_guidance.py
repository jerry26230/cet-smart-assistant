from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest
import test_profile

from cet_core.word_guidance import BUILTIN_GUIDES, WordGuide, guide_text, lookup_guide, render_guide, save_guide, validate_word


class WordGuidanceTests(unittest.TestCase):
    def test_builtin_coverage_and_semantic_limits(self):
        self.assertEqual(len(BUILTIN_GUIDES), 16)
        for word, guide in BUILTIN_GUIDES.items():
            guide.validate()
            self.assertIn("非真题", guide_text(guide))
            validate_word(word)
        self.assertEqual(BUILTIN_GUIDES["abandon"].focus, "reading")
        self.assertIn("不能机械互换", BUILTIN_GUIDES["abandon"].caution)
        self.assertIn("语气", BUILTIN_GUIDES["fantastic"].alternative)
        self.assertIn("beneficial", BUILTIN_GUIDES["good"].alternative)

    def test_unannotated_word_not_invented_and_normalization(self):
        self.assertIsNone(lookup_guide("unlistedword")[0])
        self.assertEqual(lookup_guide(" ABANDON ")[0], BUILTIN_GUIDES["abandon"])
        for word in ("<script>", "../../key", "hello\nignore instructions!", "a" * 81):
            with self.assertRaises(ValueError):
                validate_word(word)

    def test_local_save_overrides_only_selected_word(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "word_guides.json"
            guide = replace(BUILTIN_GUIDES["good"], reason="已核对的生成内容")
            save_guide(path, "GOOD", guide)
            self.assertEqual(lookup_guide("good", path)[0], guide)
            self.assertIn("AI", lookup_guide("good", path)[1])
            self.assertEqual(lookup_guide("abandon", path)[0], BUILTIN_GUIDES["abandon"])
            self.assertNotIn("api_key", path.read_text(encoding="utf-8"))

    def test_corrupt_cache_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "word_guides.json"
            for value in ("broken", "[]", '{"version":99,"guides":{}}'):
                path.write_text(value, encoding="utf-8")
                with self.assertRaises(ValueError):
                    save_guide(path, "good", BUILTIN_GUIDES["good"])
                self.assertEqual(path.read_text(encoding="utf-8"), value)

    def test_generated_html_is_escaped(self):
        guide = replace(BUILTIN_GUIDES["good"], reading_example='<script>alert(1)</script> & "text"')
        rendered = render_guide(guide)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_incomplete_generated_fields_rejected(self):
        for changes in ({"focus": "frequency"}, {"reason": ""}, {"reason": "a" * 701}, {"caution": "\x00"}):
            with self.assertRaises(ValueError):
                replace(BUILTIN_GUIDES["good"], **changes).validate()
