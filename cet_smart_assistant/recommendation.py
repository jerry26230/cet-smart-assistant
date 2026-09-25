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
        summary = "暂无法提供初始关注项"
        explanation = "三项输入均为 0，请确认是否为真实成绩；仅凭这些输入无法区分优先项。"
    elif not weaknesses:
        summary = "得分率接近，暂不提示初始关注项"
        explanation = "三项得分率差距不超过 5 个百分点，不代表能力均衡或已达到六级目标。"
    else:
        summary = "初始关注项（待确认）：" + "、".join(SKILL_LABELS[skill] for skill in weaknesses)
        explanation = "仅提示距最低得分率不超过 5 个百分点的项目，不认定为能力弱项。"
    explanation += "\n缺少分项成绩分布与题目难度参照，得分率不可直接等同于可比能力；写作翻译也不作主观加分。"
    warning = profile.score_warning()
    if warning:
        explanation += "\n" + warning
    return Diagnosis(rates, weaknesses, summary, explanation)


@dataclass(frozen=True)
class StudyPlan:
    minutes: dict[str, int]
    explanation: str
    guidance: str


def generate_study_plan(profile: StudentProfile) -> StudyPlan:
    """基础覆盖 + 有限机动时间；目标与天数用于练习建议，不预测分数。"""
    diagnosis = diagnose_profile(profile)
    # 词汇 20%，各专项至少 20%（舍入前），其余 20%为机动时间。
    shares = dict(vocabulary=0.2, listening=0.2, reading=0.2, writing=0.2)
    focused = ()
    extra = 0.0
    if profile.study_focus in SKILL_LABELS:
        focused = (profile.study_focus,)
        extra = 0.2
        reason = "按你确认的重点，将 20% 机动时间分给" + SKILL_LABELS[profile.study_focus] + "。"
    elif profile.study_focus == "initial" and diagnosis.weaknesses:
        focused = diagnosis.weaknesses
        extra = 0.05
        reason = "你选择参考初始关注项；仅将总时间的 5% 倾斜给关注项，余下 15% 平分。"
    else:
        reason = "未确认专项重点或没有可用关注项，20% 机动时间由三个专项平分。"
    for skill in SKILL_LABELS:
        shares[skill] += (0.2 - extra) / 3
        if skill in focused:
            shares[skill] += extra / len(focused)
    # 最大余数法：固定顺序打破平局，确保整数分钟总和精确相等。
    total = int(profile.daily_minutes)
    raw = {skill: total * share for skill, share in shares.items()}
    minutes = {skill: int(value) for skill, value in raw.items()}
    order = sorted(raw, key=lambda skill: round(raw[skill] - minutes[skill], 12), reverse=True)
    for skill in order[:total - sum(minutes.values())]:
        minutes[skill] += 1
    stage = "考前整合" if profile.days_remaining <= 14 else "专项训练" if profile.days_remaining <= 60 else "基础积累"
    tasks = {
        "考前整合": "在专项时间内安排限时套题片段与错题回顾。",
        "专项训练": "在专项时间内交替安排限时练习和复盘。",
        "基础积累": "先积累词汇与基础题型，再逐步加入限时练习。",
    }
    target_note = "目标较高，建议增加难题复盘与表达质量检查。" if profile.cet6_target >= 550 else "优先巩固常见题型与基础表达，再检查目标差距。"
    guidance = f"目标 {profile.cet6_target:g} 分；剩余 {profile.days_remaining:g} 天，阶段：{stage}。{tasks[stage]}{target_note}"
    explanation = "词汇 20%，听力/阅读/写作翻译各保留 20% 基础时间。" + reason
    explanation += "整数分钟按最大余数法分配；比例是可调整的项目规则，不保证达到目标分。"
    if total < 5:
        explanation += "每日时间很短，舍入后部分项目为 0 分钟，可隔日轮换覆盖。"
    return StudyPlan(minutes, explanation, guidance)
