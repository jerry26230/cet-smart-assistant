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
from cet_core.backup import BackupError, create_backup, inspect_backup, restore_backup


class BackupTests(unittest.TestCase):
    @staticmethod
    def write_backup(path, contents):
        manifest = {
            "format": "cet-smart-assistant-local-backup",
            "version": 1,
            "created_at": "2026-10-26T00:00:00+00:00",
            "files": list(contents),
        }
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in contents.items():
                archive.writestr(name, content)
            archive.writestr("backup_manifest.json", json.dumps(manifest))
            archive.writestr("README.txt", "test backup")

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

    def test_export_refuses_data_larger_than_restore_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            with profile.open("wb") as stream:
                stream.truncate(64 * 1024 * 1024 + 1)
            target = Path(folder) / "large.zip"

            with self.assertRaisesRegex(BackupError, "单文件上限"):
                create_backup(profile, target)
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

    def test_preview_restore_and_preserve_current_file_missing_from_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            guides = data_dir / "word_guides.json"
            original_profile = b'{"schema_version":1,"profile":null,"practice_history":[],"daily_tasks":{}}\n'
            original_guides = b'{"version":1,"guides":{}}\n'
            profile.write_bytes(original_profile)
            guides.write_bytes(original_guides)
            archive_path = Path(folder) / "restore.zip"
            self.write_backup(archive_path, {"word_guides.json": b'{"version":1,"guides":{}}\n'})

            preview = inspect_backup(archive_path, profile)
            self.assertEqual(preview.replace_files, ("word_guides.json",))
            self.assertEqual(preview.preserve_files, ("user_data.json",))
            # A structurally valid guide is required by the runtime validator.
            from cet_core.word_guidance import WordGuide
            from dataclasses import asdict
            guide = WordGuide("reading", "reason", "example", "meaning", "writing", "tip", "alternative", "caution")
            new_guides = json.dumps({"version": 1, "guides": {"abandon": asdict(guide)}}).encode()
            self.write_backup(archive_path, {"word_guides.json": new_guides})
            safety = Path(folder) / "before-restore.zip"

            result = restore_backup(profile, archive_path, safety)

            self.assertEqual(result.files, ("word_guides.json",))
            self.assertEqual(result.safety_backup, safety)
            self.assertEqual(profile.read_bytes(), original_profile)
            self.assertEqual(guides.read_bytes(), new_guides)
            with zipfile.ZipFile(safety) as saved:
                self.assertEqual(saved.read("word_guides.json"), original_guides)

    def test_restore_rejects_invalid_payload_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            previous = b'{"schema_version":1,"profile":null,"practice_history":[],"daily_tasks":{}}\n'
            profile.write_bytes(previous)
            archive_path = Path(folder) / "invalid.zip"
            self.write_backup(archive_path, {"user_data.json": b'{"schema_version":999}'})

            with self.assertRaisesRegex(BackupError, "格式或版本不受支持"):
                inspect_backup(archive_path, profile)
            self.assertEqual(profile.read_bytes(), previous)

    def test_restore_rejects_archive_paths_outside_allowlist(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            previous = b'{"schema_version":1,"profile":null,"practice_history":[],"daily_tasks":{}}\n'
            profile.write_bytes(previous)
            archive_path = Path(folder) / "unexpected.zip"
            self.write_backup(archive_path, {"../user_data.json": previous})

            with self.assertRaisesRegex(BackupError, "不支持的文件路径"):
                inspect_backup(archive_path, profile)
            self.assertEqual(profile.read_bytes(), previous)

    def test_restore_rejects_corrupt_zip_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            previous = b'{"schema_version":1,"profile":null,"practice_history":[],"daily_tasks":{}}\n'
            profile.write_bytes(previous)
            archive_path = Path(folder) / "corrupt.zip"
            self.write_backup(archive_path, {"user_data.json": previous})
            with zipfile.ZipFile(archive_path) as archive:
                info = archive.getinfo("user_data.json")
            damaged = bytearray(archive_path.read_bytes())
            filename_size = int.from_bytes(damaged[info.header_offset + 26:info.header_offset + 28], "little")
            extra_size = int.from_bytes(damaged[info.header_offset + 28:info.header_offset + 30], "little")
            content_offset = info.header_offset + 30 + filename_size + extra_size
            damaged[content_offset] ^= 0xFF
            archive_path.write_bytes(damaged)

            with self.assertRaises(BackupError):
                inspect_backup(archive_path, profile)
            self.assertEqual(profile.read_bytes(), previous)

    def test_restore_requires_new_nonexisting_pre_restore_backup_path(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            profile.write_text('{"schema_version":1,"profile":null,"practice_history":[]}', encoding="utf-8")
            archive_path = Path(folder) / "source.zip"
            self.write_backup(archive_path, {"user_data.json": profile.read_bytes()})
            with self.assertRaisesRegex(BackupError, "指定一个恢复前备份"):
                restore_backup(profile, archive_path)
            safety = Path(folder) / "existing.zip"
            safety.write_bytes(b"keep")
            with self.assertRaisesRegex(BackupError, "已存在"):
                restore_backup(profile, archive_path, safety)
            self.assertEqual(safety.read_bytes(), b"keep")

    def test_partial_restore_failure_rolls_back_already_written_files(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder) / "cet_smart_assistant"
            data_dir.mkdir()
            profile = data_dir / "user_data.json"
            guides = data_dir / "word_guides.json"
            old_profile = b'{"schema_version":1,"profile":null,"practice_history":[],"daily_tasks":{}}\n'
            from cet_core.word_guidance import WordGuide
            from dataclasses import asdict
            old_guide = asdict(WordGuide("reading", "old", "old", "old", "old", "old", "old", "old"))
            new_guide = asdict(WordGuide("writing", "new", "new", "new", "new", "new", "new", "new"))
            old_guides = json.dumps({"version": 1, "guides": {"abandon": old_guide}}).encode()
            new_guides = json.dumps({"version": 1, "guides": {"abandon": new_guide}}).encode()
            profile.write_bytes(old_profile)
            guides.write_bytes(old_guides)
            archive_path = Path(folder) / "source.zip"
            new_profile = b'{"schema_version":1,"profile":null,"practice_history":[],"daily_tasks":{}}'
            self.write_backup(archive_path, {"user_data.json": new_profile, "word_guides.json": new_guides})
            safety = Path(folder) / "before-restore.zip"
            from cet_core import backup as backup_module
            actual_write = backup_module._atomic_write
            calls = {"count": 0}

            def fail_second_write(target, content):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("simulated disk failure")
                actual_write(target, content)

            with patch("cet_core.backup._atomic_write", side_effect=fail_second_write):
                with self.assertRaisesRegex(BackupError, "原有文件已回滚"):
                    restore_backup(profile, archive_path, safety)
            self.assertEqual(profile.read_bytes(), old_profile)
            self.assertEqual(guides.read_bytes(), old_guides)
            self.assertTrue(safety.exists())


if __name__ == "__main__":
    unittest.main()
