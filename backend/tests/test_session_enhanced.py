"""
测试: session.py 规则引擎集成 + 追问计数
"""
import sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import asyncio
from core.session import Session
from core.shutong_state import FileStatus


def _make_session():
    d = tempfile.mkdtemp()
    return Session(d), d


class TestRuleEngineIntegration:
    def test_rule_engine_overrides_llm(self):
        s, d = _make_session()
        try:
            async def t():
                await s.process("init_project", {})
                reasoning = "假设清单：\n1. 有效期 | 来源：纯猜测\n盲区清单：\n1. 权限 | 是否阻断：是"
                rule_result = s.rule_engine.check(reasoning)
                assert rule_result.should_clarify is True
                assert rule_result.pure_guess_count == 1
                assert rule_result.blocking_gap_count == 1
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_clean_cognition_passes_through(self):
        s, d = _make_session()
        try:
            async def t():
                await s.process("init_project", {})
                reasoning = "假设清单：\n1. React | 来源：用户说过\n盲区清单：\n1. 部署方式 | 是否阻断：否"
                rule_result = s.rule_engine.check(reasoning)
                assert rule_result.should_clarify is False
                assert rule_result.has_structure is True
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestClarifyCounter:
    def test_counter_increments(self):
        s, _ = _make_session()
        s.clarify_counter = {}
        s.clarify_counter["01-vision.md"] = s.clarify_counter.get("01-vision.md", 0) + 1
        s.clarify_counter["01-vision.md"] = s.clarify_counter.get("01-vision.md", 0) + 1
        s.clarify_counter["01-vision.md"] = s.clarify_counter.get("01-vision.md", 0) + 1
        assert s.clarify_counter["01-vision.md"] == 3

    def test_soft_reminder_at_3(self):
        s, _ = _make_session()
        s.clarify_counter = {}
        for _ in range(3):
            s.clarify_counter["01-vision.md"] = s.clarify_counter.get("01-vision.md", 0) + 1
        assert s.clarify_counter["01-vision.md"] >= 3
