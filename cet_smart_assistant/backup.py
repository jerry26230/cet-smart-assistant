"""Back up and restore local assistant records without touching the Anki collection."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
import zipfile
import zlib


class BackupError(Exception):
    """A readable backup error for the Anki dialog."""


BACKUP_FILES = ("user_data.json", "word_guides.json")
MANIFEST_FILE = "backup_manifest.json"
README_FILE = "README.txt"
BACKUP_FORMAT = "cet-smart-assistant-local-backup"
MAX_BACKUP_FILE_SIZE = 64 * 1024 * 1024
MAX_BACKUP_TOTAL_SIZE = 72 * 1024 * 1024


@dataclass(frozen=True)
class BackupPreview:
    created_at: str
    files: tuple[str, ...]
    sizes: tuple[tuple[str, int], ...]
    replace_files: tuple[str, ...]
    add_files: tuple[str, ...]
    preserve_files: tuple[str, ...]

    @property
    def current_files(self) -> tuple[str, ...]:
        return tuple(name for name in (*self.replace_files, *self.preserve_files))


@dataclass(frozen=True)
class RestoreResult:
    files: tuple[str, ...]
    safety_backup: Path | None


def create_backup(profile_path: Path, destination: Path) -> tuple[str, ...]:
    """Write an atomic ZIP backup of the plugin's local learning files.

    Anki cards and scheduling data are deliberately excluded; Anki manages
    those in its own collection and profile backup.
    """
    profile_path = Path(profile_path)
    destination = Path(destination)
    selected = []
    total_size = 0
    for name in BACKUP_FILES:
        source = profile_path.parent / name
        try:
            if source.is_file():
                size = source.stat().st_size
                if size > MAX_BACKUP_FILE_SIZE:
                    raise BackupError(f"{name} 超过 {MAX_BACKUP_FILE_SIZE // (1024 * 1024)} MB 的单文件上限，未创建备份。")
                content = source.read_bytes()
                if len(content) > MAX_BACKUP_FILE_SIZE:
                    raise BackupError(f"{name} 超过单文件上限，未创建备份。")
                total_size += len(content)
                if total_size > MAX_BACKUP_TOTAL_SIZE - 65536:
                    raise BackupError("本机学习资料达到 72 MB 的备份上限，未创建备份。")
                selected.append((name, content))
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
                "format": BACKUP_FORMAT,
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
                    "恢复时请在 Anki 助手中选择此 ZIP；程序会先校验内容并提示将修改的文件，\n"
                    "恢复前会要求另存当前资料。ZIP 中没有的文件会保留。\n",
                )
            os.replace(temporary, destination)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (OSError, zipfile.BadZipFile) as error:
        raise BackupError(f"创建备份失败：{error}") from error
    return tuple(name for name, _ in selected)


def _validated_targets(profile_path: Path) -> tuple[Path, ...]:
    directory = Path(profile_path).parent
    targets = []
    for name in BACKUP_FILES:
        target = directory / name
        _is_regular_target(name, target)
        targets.append(target)
    return tuple(targets)


def _is_regular_target(name: str, target: Path) -> bool:
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        return False
    except OSError as error:
        raise BackupError(f"无法检查当前账户文件 {name}：{error}") from error
    if not stat.S_ISREG(mode):
        raise BackupError(f"目标文件 {name} 不是普通文件；为保护现有资料，已停止恢复。")
    return True


def _read_restore_archive(archive_path: Path) -> tuple[dict, dict[str, bytes]]:
    archive_path = Path(archive_path)
    if not archive_path.is_file():
        raise BackupError("找不到所选 ZIP 备份文件。")
    allowed = set(BACKUP_FILES) | {MANIFEST_FILE, README_FILE}
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            entries = archive.infolist()
            if len(entries) > len(allowed):
                raise BackupError("备份包含过多文件，已停止读取。")
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise BackupError("备份中存在重名文件；为避免内容歧义，已停止恢复。")
            if any(entry.is_dir() or entry.filename not in allowed or "/" in entry.filename or "\\" in entry.filename
                   for entry in entries):
                raise BackupError("备份包含不支持的文件路径或内容。")
            if any(entry.flag_bits & 0x1 for entry in entries):
                raise BackupError("当前不支持加密 ZIP；请使用未加密的插件备份文件。")
            if sum(entry.file_size for entry in entries) > MAX_BACKUP_TOTAL_SIZE:
                raise BackupError("备份文件超过 72 MB 的恢复上限。")
            for entry in entries:
                if entry.file_size > MAX_BACKUP_FILE_SIZE:
                    raise BackupError(f"备份中的 {entry.filename} 超过 64 MB 的恢复上限。")
            damaged = archive.testzip()
            if damaged:
                raise BackupError(f"备份校验失败：{damaged} 内容损坏。")
            if MANIFEST_FILE not in names or README_FILE not in names:
                raise BackupError("备份缺少清单或说明文件；请使用 CET 助手生成的完整 ZIP。")
            manifest = json.loads(archive.read(MANIFEST_FILE).decode("utf-8"))
            if (not isinstance(manifest, dict) or manifest.get("format") != BACKUP_FORMAT
                    or type(manifest.get("version")) is not int or manifest["version"] != 1):
                raise BackupError("备份格式或版本不受支持。")
            listed = manifest.get("files")
            contents = {name: archive.read(name) for name in BACKUP_FILES if name in names}
            expected = list(contents)
            if not isinstance(listed, list) or listed != expected or not contents:
                raise BackupError("备份清单与实际文件不一致，已停止恢复。")
            created_at = manifest.get("created_at")
            if not isinstance(created_at, str):
                raise BackupError("备份清单缺少有效的生成时间。")
            try:
                datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                raise BackupError("备份清单中的生成时间无效。") from None
    except BackupError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, KeyError, UnicodeDecodeError,
            json.JSONDecodeError, ValueError, NotImplementedError, EOFError, zlib.error) as error:
        raise BackupError(f"无法读取备份文件：{error}") from error
    _validate_restorable_contents(contents)
    return manifest, contents


def _validate_restorable_contents(contents: dict[str, bytes]) -> None:
    """Validate the JSON with the same readers that the add-on uses at runtime."""
    try:
        with tempfile.TemporaryDirectory(prefix="cet-restore-check-") as folder:
            staged = {}
            for name, content in contents.items():
                path = Path(folder) / name
                path.write_bytes(content)
                staged[name] = path
            if "user_data.json" in staged:
                from .data_service import load_document
                from .daily import load_days
                load_document(staged["user_data.json"])
                load_days(staged["user_data.json"])
            if "word_guides.json" in staged:
                from .word_guidance import load_guides
                load_guides(staged["word_guides.json"])
    except Exception as error:
        if isinstance(error, BackupError):
            raise
        raise BackupError(f"备份中的学习资料无法通过格式校验：{error}") from error


def inspect_backup(archive_path: Path, profile_path: Path) -> BackupPreview:
    """Validate a backup and summarize exactly which local files it would change."""
    manifest, contents = _read_restore_archive(archive_path)
    targets = _validated_targets(Path(profile_path))
    existing = tuple(name for name, target in zip(BACKUP_FILES, targets) if _is_regular_target(name, target))
    files = tuple(name for name in BACKUP_FILES if name in contents)
    return BackupPreview(
        created_at=manifest["created_at"],
        files=files,
        sizes=tuple((name, len(contents[name])) for name in files),
        replace_files=tuple(name for name in files if name in existing),
        add_files=tuple(name for name in files if name not in existing),
        preserve_files=tuple(name for name in existing if name not in contents),
    )


def _atomic_write(target: Path, content: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=target.name + "-", suffix=".tmp", dir=target.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def restore_backup(profile_path: Path, archive_path: Path, safety_backup_path: Path | None = None) -> RestoreResult:
    """Restore selected local JSON files, preserving a user-selected pre-restore backup.

    Files absent from the archive are left untouched. If a write fails after another
    file has been replaced, the original files are restored from memory; the safety
    ZIP remains available as a second recovery path.
    """
    profile_path = Path(profile_path)
    archive_path = Path(archive_path)
    manifest, contents = _read_restore_archive(archive_path)
    targets = _validated_targets(profile_path)
    try:
        original = {name: target.read_bytes() if _is_regular_target(name, target) else None
                    for name, target in zip(BACKUP_FILES, targets)}
    except OSError as error:
        raise BackupError(f"无法安全读取当前资料，尚未进行恢复：{error}") from error
    safety_destination = None
    if any(content is not None for content in original.values()):
        if safety_backup_path is None:
            raise BackupError("恢复会替换当前资料；请先指定一个恢复前备份文件。")
        safety_destination = Path(safety_backup_path)
        resolved_archive = os.path.normcase(os.path.abspath(archive_path))
        resolved_safety = os.path.normcase(os.path.abspath(safety_destination))
        if resolved_archive == resolved_safety or any(
            os.path.normcase(os.path.abspath(target)) == resolved_safety for target in targets
        ):
            raise BackupError("恢复前备份不能覆盖所选 ZIP 或账户资料文件。")
        if safety_destination.exists():
            raise BackupError("恢复前备份文件已存在，请另选文件名以免覆盖旧备份。")
        try:
            create_backup(profile_path, safety_destination)
        except BackupError as error:
            raise BackupError(f"无法创建恢复前备份，尚未恢复任何资料：{error}") from error

    try:
        profile_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise BackupError(f"无法准备账户资料目录，尚未进行恢复：{error}") from error
    changed = []
    try:
        for name, target in zip(BACKUP_FILES, targets):
            if name not in contents:
                continue
            _atomic_write(target, contents[name])
            changed.append(name)
    except OSError as error:
        rollback_errors = []
        for name in reversed(changed):
            target = profile_path.parent / name
            try:
                previous = original[name]
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    _atomic_write(target, previous)
            except OSError as rollback_error:
                rollback_errors.append(f"{name}: {rollback_error}")
        if rollback_errors:
            detail = "；".join(rollback_errors)
            backup_note = f"恢复前备份保存在：{safety_destination}" if safety_destination else ""
            raise BackupError(f"恢复写入失败且自动回滚未完全成功：{detail}。{backup_note}") from error
        raise BackupError(f"恢复写入失败，原有文件已回滚：{error}") from error
    return RestoreResult(tuple(name for name in BACKUP_FILES if name in contents), safety_destination)
