"""与 Anki 和 Qt 无关的输入校验。"""

from dataclasses import dataclass
from math import isfinite


@dataclass
class StudentProfile:
    cet4_total: float
    listening: float
    reading: float
    writing: float
    cet6_target: float
    days_remaining: int
    daily_minutes: int
    study_focus: str = "balanced"

    def validate(self) -> None:
        if self.study_focus not in ("balanced", "initial", "listening", "reading", "writing", "feedback"):
            raise ValueError("请选择有效的学习重点。")
        limits = {
            "cet4_total": ("四级总分", 0, 710),
            "listening": ("听力", 0, 248.5),
            "reading": ("阅读", 0, 248.5),
            "writing": ("写作翻译", 0, 213),
            "cet6_target": ("六级目标", 1, 710),
            "days_remaining": ("考试剩余天数", 1, 3650),
            "daily_minutes": ("每日学习分钟数", 1, 1440),
        }
        for name, (label, minimum, maximum) in limits.items():
            value = getattr(self, name)
            if type(value) not in (int, float) or not isfinite(value):
                raise ValueError(f"{label}必须是有限数字。")
            if not minimum <= value <= maximum:
                raise ValueError(f"{label}应在 {minimum}～{maximum} 之间。")
            if name in ("days_remaining", "daily_minutes") and int(value) != value:
                raise ValueError(f"{label}必须是整数。")

    def score_warning(self) -> str:
        difference = abs(self.listening + self.reading + self.writing - self.cet4_total)
        if difference > 10:
            return f"分项合计与总分相差 {difference:.1f} 分，请核对；仍可保存。"
        return ""
