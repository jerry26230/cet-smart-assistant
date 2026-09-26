"""随插件分发的离线词库及来源校验。"""

import hashlib
import json
from pathlib import Path

from .anki_service import import_vocabulary, normalize_word, validate_card

BOOKS = {
    "cet4": ("四级词汇", "CET 备考::四级词汇"),
    "cet6": ("六级词汇", "CET 备考::六级词汇"),
    "ielts_core": ("雅思词汇", "CET 备考::雅思词汇"),
}
DATA_DIR = Path(__file__).parent / "vocabularies"


def load_book(key):
    if key not in BOOKS:
        raise ValueError("未知词库。")
    manifest = json.loads((DATA_DIR / "provenance.json").read_text(encoding="utf-8"))
    raw = (DATA_DIR / f"{key}.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["files"][key]["sha256"]:
        raise ValueError("内置词库文件不完整，请重新安装插件。")
    source = json.loads(raw)
    entries, seen = [], set()
    for item in source["words"]:
        word, meaning = validate_card(item["word"], "\n".join(item["translations"]))
        normalized = normalize_word(word)
        if normalized not in seen:
            entries.append((word, meaning))
            seen.add(normalized)
    if len(source["words"]) != manifest["files"][key]["count"]:
        raise ValueError("内置词库条目数不匹配。")
    return entries


def import_book(col, key):
    entries = load_book(key)
    return import_vocabulary(col, entries, deck_name=BOOKS[key][1],
                             model_name=f"CET Smart Assistant Vocabulary {key}")
