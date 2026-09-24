"""四级初始能力诊断：纯 Python 规则，不依赖 Anki 或 Qt。"""

from dataclasses import dataclass
from math import isfinite

from .models import StudentProfile


SKILL_LABELS = {"listening": "听力", "reading": "阅读", "writing": "写作翻译"}
MAX_SCORES = {"listening": 248.5, "reading": 248.5, "writing": 213.0}
WEAKNESS_GAP = 0.05  # 5 个百分点为项目启发式阈值，不是考试官方标准。
EPSILON = 1e-12  # 只用于消除浮点运算在阈值处的误差。


@dataclass(frozen=True)
class Diagnosis:
    rates: dict[str, float]
    weaknesses: tuple[str, ...]
    summary: str
    explanation: str


def calculate_skill_rates(listening, reading, writing) -> dict[str, float]:
    scores = dict(listening=listening, reading=reading, writing=writing)
    for skill, score in scores.items():
        if type(score) not in (int, float) or not isfinite(score):
            raise ValueError(f"{SKILL_LABELS[skill]}成绩必须是有限数字。")
        if not 0 <= score <= MAX_SCORES[skill]:
            raise ValueError(f"{SKILL_LABELS[skill]}成绩超出允许范围。")
    return {skill: score / MAX_SCORES[skill] for skill, score in scores.items()}


def identify_weakness(listening_rate, reading_rate, writing_rate) -> tuple[str, ...]:
    rates = dict(listening=listening_rate, reading=reading_rate, writing=writing_rate)
    for rate in rates.values():
        if type(rate) not in (int, float) or not isfinite(rate) or not 0 <= rate <= 1:
            raise ValueError("得分率必须是 0～1 之间的有限数字。")
    lowest, highest = min(rates.values()), max(rates.values())
    if highest - lowest <= WEAKNESS_GAP + EPSILON:
        return ()
    # 固定按听力、阅读、写作顺序输出，结果可重复。
    return tuple(skill for skill, rate in rates.items()
                 if rate - lowest <= WEAKNESS_GAP + EPSILON)


def diagnose_profile(profile: StudentProfile) -> Diagnosis:
    profile.validate()
    rates = calculate_skill_rates(profile.listening, profile.reading, profile.writing)
    weaknesses = identify_weakness(rates["listening"], rates["reading"], rates["writing"])
    if max(rates.values()) == 0:
        summary = "暂无法区分相对薄弱项"
        explanation = "三项输入均为 0，请确认是否为真实成绩；仅凭这些输入无法区分优先项。"
    elif not weaknesses:
        summary = "较均衡，无明显相对薄弱项"
        explanation = "三项得分率最大差距不超过 5 个百分点；相对均衡不代表已达到六级目标。"
    else:
        summary = "相对薄弱项：" + "、".join(SKILL_LABELS[skill] for skill in weaknesses)
        explanation = "按分项满分归一化；距最低得分率不超过 5 个百分点的项目列为相对薄弱项。"
    warning = profile.score_warning()
    if warning:
        explanation += "\n" + warning
    return Diagnosis(rates, weaknesses, summary, explanation)
