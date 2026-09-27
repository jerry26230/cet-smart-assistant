"""最近 28 天同类练习趋势；不比较不同专项的绝对得分率。"""

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta

from .recommendation import SKILL_LABELS, StudyPlan, generate_study_plan


@dataclass(frozen=True)
class Feedback:
    plan: StudyPlan
    trends: tuple[str, ...]
    focused: tuple[str, ...]


def update_plan_from_practice(profile, records, today=None):
    profile.validate()
    today = today or date.today()
    baseline = generate_study_plan(replace(profile, study_focus="balanced"), today=today)
    if profile.remaining_days(today) <= 0:
        return Feedback(baseline, (), ())
    groups = defaultdict(lambda: defaultdict(list))
    for record in records:
        record.validate()
        if (record.skill not in SKILL_LABELS or not record.comparable or record.score is None
                or not today - timedelta(days=27) <= date.fromisoformat(record.day) <= today):
            continue
        # 组名、满分和题量均相同才比较；由用户确认题型、难度、评分方式一致。
        key = (record.skill, record.comparison_group.strip().casefold(), record.maximum, record.questions)
        groups[key][record.day].append(record.score / record.maximum)
    signals = defaultdict(list)
    trends = []
    for (skill, group, maximum, questions), days in sorted(groups.items(), key=lambda item: str(item[0])):
        ordered = sorted(days)
        label = f"{SKILL_LABELS[skill]} / {group} / 满分 {maximum:g} / 题量 {questions or '未填'}"
        if len(ordered) < 6:
            trends.append(f"{label}：仅 {len(ordered)} 个练习日，至少需要 6 天，暂不调整。")
            continue
        # 先按天等权平均，避免一天大量重复记录压倒其他日期。
        daily = [sum(days[day]) / len(days[day]) for day in ordered[-6:]]
        before, after = sum(daily[:3]) / 3, sum(daily[3:]) / 3
        delta = after - before
        signal = -1 if delta <= -0.05 + 1e-12 else 1 if delta >= 0.05 - 1e-12 else 0
        signals[skill].append(signal)
        direction = "下降" if signal < 0 else "改善" if signal > 0 else "变化较小"
        trends.append(f"{label}：前 3 日均值 {before:.1%} → 后 3 日均值 {after:.1%}，{delta * 100:+.1f} 个百分点，{direction}。")
    # 多个组结论冲突（包括稳定与下降）时不作单边推断。
    focused = tuple(skill for skill in SKILL_LABELS if signals[skill] and all(x == -1 for x in signals[skill]))
    for skill in SKILL_LABELS:
        if len(set(signals[skill])) > 1:
            trends.append(f"{SKILL_LABELS[skill]}：不同可比组结论不一致，暂不增加专项比例，请检查记录。")
    if not trends:
        trends.append("最近 28 天没有已确认可比的专项成绩，先按均衡方案学习。旧记录不会自动纳入趋势。")
    if focused:
        shares = dict(vocabulary=0.2, listening=0.2, reading=0.2, writing=0.2)
        for skill in focused:
            shares[skill] += 0.2 / len(focused)
        total = int(profile.daily_minutes)
        raw = {skill: total * share for skill, share in shares.items()}
        minutes = {skill: int(value) for skill, value in raw.items()}
        order = sorted(raw, key=lambda skill: round(raw[skill] - minutes[skill], 12), reverse=True)
        for skill in order[:total - sum(minutes.values())]:
            minutes[skill] += 1
        explanation = "同类练习呈下降趋势，将 20% 机动时间平分给：" + "、".join(SKILL_LABELS[s] for s in focused) + "；词汇和各专项仍各保留 20% 基础比例。"
    else:
        minutes = baseline.minutes
        explanation = "没有足够且一致的下降证据，使用均衡方案；改善不代表已掌握或无需继续练习。"
    explanation += "趋势规则是项目启发式，不证明能力变化或提分效果。数据不足、过期或组间冲突时不强行诊断。"
    return Feedback(StudyPlan(minutes, explanation, baseline.guidance), tuple(trends), focused)
