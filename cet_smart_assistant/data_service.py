"""JSON 读写；损坏文件不自动覆盖，保存使用原子替换。"""

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from .models import StudentProfile


class DataError(Exception):
    """向用户显示的存储错误。"""


def load_document(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return {"schema_version": 1, "profile": None, "practice_history": []}
    except (OSError, ValueError) as error:
        raise DataError(f"无法读取资料，原文件保持不变：{error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise DataError("资料格式或版本不受支持，原文件保持不变。")
    if not isinstance(data.get("practice_history"), list):
        raise DataError("练习历史格式无效，原文件保持不变。")
    try:
        if data.get("profile") is not None:
            StudentProfile(**data["profile"]).validate()
    except (TypeError, ValueError) as error:
        raise DataError(f"已保存的资料无效：{error}") from error
    return data


def load_profile(path: Path) -> StudentProfile | None:
    profile = load_document(path).get("profile")
    return StudentProfile(**profile) if profile is not None else None


def save_profile(path: Path, profile: StudentProfile) -> None:
    profile.validate()
    data = load_document(path)
    data["profile"] = asdict(profile)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # 临时文件放在同一目录，避免写入中断留下半个 JSON 文件。
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        raise DataError(f"保存失败：{error}") from error
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
