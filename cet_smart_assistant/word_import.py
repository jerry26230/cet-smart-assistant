"""离线词表解析：CSV 或制表符分隔的两列文本。"""

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from .anki_service import normalize_word, validate_card

MAX_BYTES = 5 * 1024 * 1024


@dataclass
class ImportPreview:
    entries: list[tuple[str, str]]
    errors: list[str]
    duplicates: int


def read_word_file(path: str) -> str:
    with Path(path).open("rb") as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("文件不能超过 5 MB，请分批导入。")
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("无法识别文件编码，请另存为 UTF-8 CSV 或 TSV。")


def parse_words(text: str) -> ImportPreview:
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("文本不能超过 5 MB，请分批导入。")
    text = text.lstrip("\ufeff")
    first = next((line for line in text.splitlines() if line.strip()), "")
    delimiter = "\t" if "\t" in first else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter, strict=True)
    entries, errors, seen = [], [], set()
    duplicates = 0
    first_record = True
    try:
        for index, row in enumerate(reader, 1):
            if index > 10001:
                raise ValueError("每批最多 10000 条，请拆分文件。")
            if not row or not any(value.strip() for value in row):
                continue
            if first_record:
                first_record = False
                if [v.strip().casefold() for v in row] in (["word", "meaning"], ["单词", "释义"], ["词汇", "释义"]):
                    continue
            try:
                if len(row) != 2:
                    raise ValueError("需要两列：单词、释义；含逗号的 CSV 释义需用双引号包围。")
                word, meaning = validate_card(*row)
                key = normalize_word(word)
                if key in seen:
                    duplicates += 1
                else:
                    entries.append((word, meaning))
                    seen.add(key)
            except ValueError as error:
                errors.append(f"第 {reader.line_num} 行：{error}")
    except csv.Error as error:
        errors.append(f"第 {reader.line_num} 行：CSV 格式错误（{error}）")
    if len(entries) + duplicates > 10000:
        raise ValueError("每批最多 10000 条，请拆分文件。")
    return ImportPreview(entries, errors, duplicates)
