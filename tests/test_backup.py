import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

root = Path(__file__).resolve().parents[1] / "cet_smart_assistant"
spec = importlib.util.spec_from_loader("cet_core", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(root)]
sys.modules["cet_core"] = package
from cet_core.backup import BackupError, create_backup


class BackupTests(unittest.TestCase):
    def test_archives_local_learning_files_and_explains_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            guides = data_dir / "word_guides.json"
            profile.write_text('{"profile":{"cet6_target":500},"daily_tasks":[]}', encoding="utf-8")
            guides.write_text('{"version":1,"guides":{}}', encoding="utf-8")
            (data_dir / "unrelated.tmp").write_text("skip", encoding="utf-8")
            target = Path(folder) / "CET-backup.zip"

            included = create_backup(profile, target)

            self.assertEqual(included, ("user_data.json", "word_guides.json"))
            with zipfile.ZipFile(target) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), {
                    "user_data.json", "word_guides.json", "backup_manifest.json", "README.txt"
                })
                self.assertEqual(archive.read("user_data.json"), profile.read_bytes())
                self.assertEqual(archive.read("word_guides.json"), guides.read_bytes())
                manifest = json.loads(archive.read("backup_manifest.json"))
                self.assertEqual(manifest["format"], "cet-smart-assistant-local-backup")
                self.assertEqual(manifest["files"], list(included))
                note = archive.read("README.txt").decode("utf-8")
                self.assertIn("不包含 Anki 卡片", note)
                self.assertIn("API 密钥", note)

    def test_exports_available_file_even_when_other_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            guides = data_dir / "word_guides.json"
            guides.write_text("{broken-but-preserved", encoding="utf-8")
            target = Path(folder) / "only-guides.zip"

            included = create_backup(data_dir / "user_data.json", target)

            self.assertEqual(included, ("word_guides.json",))
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(archive.read("word_guides.json"), guides.read_bytes())

    def test_no_data_fails_without_creating_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "empty.zip"
            with self.assertRaisesRegex(BackupError, "没有可备份"):
                create_backup(Path(folder) / "user_data.json", target)
            self.assertFalse(target.exists())

    def test_replace_failure_preserves_existing_backup_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            profile.write_text("{}", encoding="utf-8")
            target = Path(folder) / "backup.zip"
            target.write_bytes(b"previous backup")
            with patch("cet_core.backup.os.replace", side_effect=PermissionError("denied")):
                with self.assertRaisesRegex(BackupError, "创建备份失败"):
                    create_backup(profile, target)
            self.assertEqual(target.read_bytes(), b"previous backup")
            self.assertEqual(list(Path(folder).glob("backup-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
