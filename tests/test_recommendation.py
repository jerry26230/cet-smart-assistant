import importlib.util
from pathlib import Path
import sys
import unittest

# 用独立命名空间导入业务逻辑，避免执行 Anki 菜单入口。
if "cet_core" not in sys.modules:
    spec = importlib.util.spec_from_loader("cet_core", loader=None, is_package=True)
    package = importlib.util.module_from_spec(spec)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "cet_smart_assistant")]
    sys.modules["cet_core"] = package

from cet_core.models import StudentProfile
from cet_core.recommendation import calculate_skill_rates, identify_weakness, diagnose_profile, generate_study_plan


class DiagnosisTests(unittest.TestCase):
    def profile(self, listening=115, reading=190, writing=165, total=470):
        return StudentProfile(total, listening, reading, writing, 500, 90, 120)

    def test_normalization_uses_each_section_maximum(self):
        rates = calculate_skill_rates(124.25, 124.25, 106.5)
        self.assertEqual(rates, dict(listening=0.5, reading=0.5, writing=0.5))

    def test_similar_total_different_weakness(self):
        a = diagnose_profile(self.profile())
        b = diagnose_profile(self.profile(listening=190, reading=115))
        self.assertEqual(a.weaknesses, ("listening",))
        self.assertEqual(b.weaknesses, ("reading",))
        self.assertAlmostEqual(a.rates["listening"], 115 / 248.5)

    def test_absolute_score_is_not_used_for_ranking(self):
        # 写作原始分更低，但得分率更高。
        result = diagnose_profile(self.profile(listening=160, reading=200, writing=150, total=510))
        self.assertEqual(result.weaknesses, ("listening",))

    def test_writing_can_be_weakest(self):
        self.assertEqual(identify_weakness(0.8, 0.75, 0.4), ("writing",))

    def test_multiple_weaknesses_and_stable_order(self):
        self.assertEqual(identify_weakness(0.5, 0.54, 0.8), ("listening", "reading"))
        self.assertEqual(identify_weakness(0.5, 0.8, 0.5), ("listening", "writing"))

    def test_threshold_boundary(self):
        self.assertEqual(identify_weakness(0.5, 0.55, 0.8), ("listening", "reading"))
        self.assertEqual(identify_weakness(0.5, 0.550001, 0.8), ("listening",))
        self.assertEqual(identify_weakness(0.5, 0.52, 0.55), ())

    def test_equal_rates_and_full_marks_are_balanced(self):
        for scores in [(124.25, 124.25, 106.5), (248.5, 248.5, 213)]:
            result = diagnose_profile(self.profile(*scores, total=sum(scores)))
            self.assertEqual(result.weaknesses, ())
            self.assertIn("得分率接近", result.summary)

    def test_zero_scores_do_not_claim_success(self):
        result = diagnose_profile(self.profile(0, 0, 0, total=0))
        self.assertEqual(result.weaknesses, ())
        self.assertIn("暂无法", result.summary)

    def test_invalid_scores_and_rates_rejected(self):
        for value in [-1, 249, float("nan"), float("inf"), True, "115"]:
            with self.subTest(score=value), self.assertRaises(ValueError):
                calculate_skill_rates(value, 190, 165)
        for value in [-0.1, 1.1, float("nan"), False, "0.5"]:
            with self.subTest(rate=value), self.assertRaises(ValueError):
                identify_weakness(0.6, value, 0.8)

    def test_total_mismatch_does_not_change_rates(self):
        regular = diagnose_profile(self.profile())
        mismatch = diagnose_profile(self.profile(total=500))
        self.assertEqual(regular.rates, mismatch.rates)
        self.assertEqual(regular.weaknesses, mismatch.weaknesses)
        self.assertIn("相差 30.0", mismatch.explanation)

    def test_deterministic(self):
        self.assertEqual(diagnose_profile(self.profile()), diagnose_profile(self.profile()))

    def test_balanced_default_does_not_rank_abilities(self):
        self.assertEqual(generate_study_plan(self.profile()).minutes,
                         dict(vocabulary=24, listening=32, reading=32, writing=32))
        self.assertIn("不可直接", diagnose_profile(self.profile()).explanation)

    def test_confirmed_focus_overrides_score_hint(self):
        profile = self.profile()
        profile.study_focus = "writing"
        self.assertEqual(generate_study_plan(profile).minutes,
                         dict(vocabulary=24, listening=24, reading=24, writing=48))

    def test_optional_initial_hint_is_limited(self):
        profile = self.profile()
        profile.study_focus = "initial"
        self.assertEqual(generate_study_plan(profile).minutes,
                         dict(vocabulary=24, listening=36, reading=30, writing=30))

    def test_all_minutes_and_focus_modes_conserve_time(self):
        profile = self.profile()
        for focus in ("balanced", "initial", "listening", "reading", "writing"):
            profile.study_focus = focus
            for total in range(1, 1441):
                profile.daily_minutes = total
                plan = generate_study_plan(profile)
                self.assertEqual(sum(plan.minutes.values()), total)
                self.assertTrue(all(type(value) is int and value >= 0 for value in plan.minutes.values()))
                self.assertEqual(plan, generate_study_plan(profile))

    def test_target_and_days_change_guidance_not_ability_claim(self):
        profile = self.profile()
        before = generate_study_plan(profile)
        profile.days_remaining = 14
        profile.cet6_target = 600
        after = generate_study_plan(profile)
        self.assertEqual(before.minutes, after.minutes)
        self.assertIn("考前整合", after.guidance)
        self.assertIn("目标较高", after.guidance)

    def test_initial_without_hint_falls_back_to_balance(self):
        profile = self.profile(0, 0, 0, total=0)
        profile.study_focus = "initial"
        self.assertEqual(generate_study_plan(profile).minutes,
                         dict(vocabulary=24, listening=32, reading=32, writing=32))

    def test_invalid_focus_rejected(self):
        profile = self.profile()
        profile.study_focus = "unknown"
        with self.assertRaises(ValueError):
            generate_study_plan(profile)


if __name__ == "__main__":
    unittest.main()
