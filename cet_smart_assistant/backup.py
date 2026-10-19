"""Export local assistant records without touching the Anki collection."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import zipfile


class BackupError(Exception):
    """A readable backup error for the Anki dialog."""


BACKUP_FILES = ("user_data.json", "word_guides.json")


def create_backup(profile_path: Path, destination: Path) -> tuple[str, ...]:
    """Write an atomic ZIP backup of the plugin's local learning files.

    Anki cards and scheduling data are deliberately excluded; Anki manages
    those in its own collection and profile backup.
    """
    profile_path = Path(profile_path)
    destination = Path(destination)
    selected = []
    for name in BACKUP_FILES:
        source = profile_path.parent / name
        try:
            if source.is_file():
                selected.append((name, source.read_bytes()))
        except OSError as error:
            raise BackupError(f"无法读取 {name}：{error}") from error
    if not selected:
        raise BackupError("当前账户还没有可备份的学习资料。")

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=destination.stem + "-", suffix=".tmp",
                dir=destination.parent, delete=False,
            ) as stream:
                temporary = Path(stream.name)
            manifest = {
                "format": "cet-smart-assistant-local-backup",
                "version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "files": [name for name, _ in selected],
            }
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, content in selected:
                    archive.writestr(name, content)
                archive.writestr(
                    "backup_manifest.json",
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                )
                archive.writestr(
                    "README.txt",
                    "CET 智能备考助手本机资料备份\n\n"
                    "包含本机学习资料及已保存的词语用法（若文件存在）。\n"
                    "不包含 Anki 卡片、牌组、复习进度或任何 API 密钥。\n"
                    "恢复前请关闭 Anki，将需要恢复的 JSON 文件复制到对应账户的\n"
                    "cet_smart_assistant 目录。建议先复制一份当前文件再覆盖。\n",
                )
            os.replace(temporary, destination)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (OSError, zipfile.BadZipFile) as error:
        raise BackupError(f"创建备份失败：{error}") from error
    return tuple(name for name, _ in selected)
