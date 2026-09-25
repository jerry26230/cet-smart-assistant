import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# 独立加载纯 Python 模块，不执行仅属于 Anki 的插件入口。
root = Path(__file__).resolve().parents[1] / "cet_smart_assistant"
spec = importlib.util.spec_from_loader("cet_core", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(root)]
sys.modules["cet_core"] = package
from cet_core.models import StudentProfile
from cet_core.data_service import DataError, load_profile, save_profile


class ProfileTests(unittest.TestCase):
    def profile(self, **changes):
        data = dict(cet4_total=470, listening=115, reading=190, writing=165,
                    cet6_target=500, days_remaining=90, daily_minutes=120)
        data.update(changes)
        return StudentProfile(**data)

    def test_valid_boundaries(self):
        self.profile(cet4_total=710, listening=248.5, reading=248.5, writing=213).validate()
        self.profile(cet4_total=0, listening=0, reading=0, writing=0,
                     days_remaining=1, daily_minutes=1).validate()

    def test_invalid_inputs(self):
        for name, value in [("listening", 249), ("reading", -1), ("writing", 214),
                            ("cet4_total", 711), ("cet6_target", 0),
                            ("days_remaining", 0), ("daily_minutes", 1441),
                            ("days_remaining", 1.5), ("daily_minutes", True),
                            ("reading", float("nan")), ("writing", float("inf"))]:
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                self.profile(**{name: value}).validate()

    def test_mismatch_warns_but_is_valid(self):
        profile = self.profile(cet4_total=500)
        profile.validate()
        self.assertIn("30.0", profile.score_warning())
        self.assertEqual(self.profile().score_warning(), "")

    def test_storage_roundtrip_and_preserve_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested" / "user_data.json"
            self.assertIsNone(load_profile(path))
            save_profile(path, self.profile())
            self.assertEqual(load_profile(path), self.profile())
            data = json.loads(path.read_text(encoding="utf-8"))
            data["practice_history"] = [{"category": "listening", "accuracy": 0.6}]
            path.write_text(json.dumps(data), encoding="utf-8")
            save_profile(path, self.profile(cet6_target=550))
            self.assertEqual(json.loads(path.read_text())["practice_history"], data["practice_history"])

    def test_corrupt_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "user_data.json"
            for raw in ['{broken', '[]', '{"schema_version": 99}',
                        '{"schema_version":1,"profile":{"listening":-1},"practice_history":[]}']:
                path.write_text(raw, encoding="utf-8")
                with self.assertRaises(DataError):
                    save_profile(path, self.profile())
                self.assertEqual(path.read_text(), raw)

    def test_failed_replace_preserves_saved_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "user_data.json"
            save_profile(path, self.profile())
            with patch("cet_core.data_service.os.replace", side_effect=PermissionError("denied")):
                with self.assertRaises(DataError):
                    save_profile(path, self.profile(cet6_target=550))
            self.assertEqual(load_profile(path), self.profile())
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_legacy_profile_defaults_to_balanced_and_focus_persists(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "user_data.json"
            save_profile(path, self.profile())
            document = json.loads(path.read_text())
            del document["profile"]["study_focus"]
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(load_profile(path).study_focus, "balanced")
            profile = load_profile(path)
            profile.study_focus = "writing"
            save_profile(path, profile)
            self.assertEqual(load_profile(path).study_focus, "writing")


if __name__ == "__main__":
    unittest.main()
