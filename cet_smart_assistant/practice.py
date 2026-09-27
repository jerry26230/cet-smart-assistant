"""专项练习记录：保留原始分数，不跨专项比较能力。"""

from dataclasses import asdict, dataclass, fields
from datetime import date
from math import isfinite
from uuid import uuid4

from .data_service import load_document, save_document

SKILLS = {"vocabulary": "词汇", "listening": "听力", "reading": "阅读", "writing": "写作翻译"}


@dataclass
class PracticeRecord:
    day: str
    skill: str
    minutes: int
    title: str
    score: float | None = None
    maximum: float | None = None
    note: str = ""
    comparison_group: str = ""
    comparable: bool = False
    questions: int | None = None

    def validate(self):
        try:
            parsed = date.fromisoformat(self.day)
        except (TypeError, ValueError):
            raise ValueError("练习日期应为 YYYY-MM-DD。") from None
        if parsed.isoformat() != self.day or parsed > date.today():
            raise ValueError("请选择有效日期，不能记录未来练习。")
        if self.skill not in SKILLS:
            raise ValueError("请选择有效专项。")
        if type(self.minutes) is not int or not 1 <= self.minutes <= 1440:
            raise ValueError("练习时长应为 1～1440 的整数分钟。")
        if not isinstance(self.title, str) or not self.title.strip() or len(self.title) > 200:
            raise ValueError("请填写练习名称，最多 200 字符。")
        if not isinstance(self.note, str) or len(self.note) > 2000:
            raise ValueError("备注最多 2000 字符。")
        if not isinstance(self.comparison_group, str) or len(self.comparison_group) > 100:
            raise ValueError("可比组名称最多 100 字符。")
        if type(self.comparable) is not bool:
            raise ValueError("可比确认值无效。")
        if self.questions is not None and (type(self.questions) is not int or not 1 <= self.questions <= 10000):
            raise ValueError("题量应为 1～10000 的整数，或留空。")
        if self.comparable and (not self.comparison_group.strip() or self.score is None):
            raise ValueError("纳入趋势前，请填写可比组名称、得分和满分。")
        if (self.score is None) != (self.maximum is None):
            raise ValueError("得分与满分须同时填写，或同时留空。")
        if self.score is not None:
            if any(type(x) not in (int, float) or not isfinite(x) for x in (self.score, self.maximum)):
                raise ValueError("得分和满分必须是有限数字。")
            if not 0 <= self.score <= self.maximum <= 10000 or self.maximum == 0:
                raise ValueError("应满足 0 ≤ 得分 ≤ 满分，满分在 0～10000 之间且大于 0。")


def append_record(path, record, record_id=None):
    record.validate()
    data = load_document(path)
    record_id = record_id or str(uuid4())
    if any(isinstance(row, dict) and row.get("id") == record_id for row in data["practice_history"]):
        return False
    data["practice_history"].append({"record_version": 1, "id": record_id, **asdict(record)})
    save_document(path, data)
    return True


def read_records(path):
    records, unrecognized = [], 0
    for row in load_document(path)["practice_history"]:
        try:
            if not isinstance(row, dict) or row.get("record_version") != 1:
                raise ValueError("旧记录")
            record = PracticeRecord(**{field.name: row[field.name] for field in fields(PracticeRecord) if field.name in row})
            record.validate()
            records.append(record)
        except (KeyError, TypeError, ValueError):
            unrecognized += 1
    records.reverse()
    records.sort(key=lambda record: record.day, reverse=True)
    return records, unrecognized


def summarize(records):
    return {skill: {"count": sum(r.skill == skill for r in records),
                    "minutes": sum(r.minutes for r in records if r.skill == skill)} for skill in SKILLS}
