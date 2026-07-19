"""
测试: rule_engine
验证: 结构检测、D级假设检测、阻断盲区检测
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.rule_engine import RuleEngine, RuleResult


def _make_engine():
    return RuleEngine()


class TestStructureDetection:
    def test_missing_both(self):
        e = _make_engine()
        r = e.check("just some text")
        assert r.should_clarify is True
        assert r.has_structure is False
        assert "缺少" in r.reasons[0]

    def test_has_both(self):
        e = _make_engine()
        text = "假设清单：\n1. X | 来源：用户说过\n盲区清单：\n1. Y | 是否阻断：否"
        r = e.check(text)
        assert r.has_structure is True

    def test_missing_assumptions_only(self):
        e = _make_engine()
        r = e.check("盲区清单：\n1. X")
        assert r.has_structure is False

    def test_missing_gaps_only(self):
        e = _make_engine()
        r = e.check("假设清单：\n1. X")
        assert r.has_structure is False


class TestPureGuessDetection:
    def test_no_guesses(self):
        e = _make_engine()
        text = "假设清单：\n1. X | 来源：用户说过\n盲区清单：\n1. Y | 是否阻断：否"
        r = e.check(text)
        assert r.pure_guess_count == 0
        assert r.should_clarify is False

    def test_one_guess(self):
        e = _make_engine()
        text = "假设清单：\n1. 有效期默认30天 | 来源：纯猜测 | 猜错后果：用户不满意\n盲区清单：\n1. Y | 是否阻断：否"
        r = e.check(text)
        assert r.pure_guess_count == 1
        assert r.should_clarify is True
        assert any("D级假设" in x for x in r.reasons)

    def test_multiple_guesses(self):
        e = _make_engine()
        text = "假设清单：\n1. A | 来源：纯猜测\n2. B | 来源：纯猜测\n盲区清单：\n1. Y | 是否阻断：否"
        r = e.check(text)
        assert r.pure_guess_count == 2


class TestBlockingGapDetection:
    def test_no_blocking(self):
        e = _make_engine()
        text = "假设清单：\n1. X | 来源：用户说过\n盲区清单：\n1. Y | 是否阻断：否"
        r = e.check(text)
        assert r.blocking_gap_count == 0

    def test_one_blocking(self):
        e = _make_engine()
        text = "假设清单：\n1. X | 来源：用户说过\n盲区清单：\n1. 缺少权限模型 | 是否阻断：是"
        r = e.check(text)
        assert r.blocking_gap_count == 1
        assert r.should_clarify is True
        assert any("阻断盲区" in x for x in r.reasons)

    def test_multiple_blocking(self):
        e = _make_engine()
        text = "假设清单：\n1. X | 来源：用户说过\n盲区清单：\n1. A | 是否阻断：是\n2. B | 是否阻断：是"
        r = e.check(text)
        assert r.blocking_gap_count == 2


class TestSourceExtraction:
    def test_extracts_sources(self):
        e = _make_engine()
        text = "假设清单：\n1. A | 来源：用户说过\n2. B | 来源：行业惯例\n3. C | 来源：纯猜测"
        r = e.check(text)
        assert r.assumption_sources.get("用户说过") == 1
        assert r.assumption_sources.get("行业惯例") == 1
        assert r.assumption_sources.get("纯猜测") == 1


class TestCombinedScenarios:
    def test_clean_cognition(self):
        e = _make_engine()
        text = (
            "【认知显化】\n"
            "理解复述：用户要做优惠券系统\n\n"
            "假设清单：\n"
            "1. 面向电商 | 来源：用户说过 | 猜错后果：方向错误\n\n"
            "盲区清单：\n"
            "1. 数据库选型 | 为什么重要：影响性能 | 是否阻断：否"
        )
        r = e.check(text)
        assert r.should_clarify is False
        assert r.has_structure is True
        assert r.pure_guess_count == 0
        assert r.blocking_gap_count == 0

    def test_messy_cognition(self):
        e = _make_engine()
        text = (
            "【认知显化】\n"
            "假设清单：\n"
            "1. 有效期30天 | 来源：纯猜测\n"
            "2. 面向电商 | 来源：用户说过\n\n"
            "盲区清单：\n"
            "1. 权限模型 | 是否阻断：是"
        )
        r = e.check(text)
        assert r.should_clarify is True
        assert r.pure_guess_count == 1
        assert r.blocking_gap_count == 1
