"""
测试: 意图识别层重构 —— _recognize_intent() 单元测试
"""
import sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.session import Session, Message


def _make_mock_session():
    d = tempfile.mkdtemp()
    s = Session(d)
    s.llm.judge_json = AsyncMock()
    return s, d


class TestRecognizeIntent:
    def test_intent_stop(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "stop"}
                result = await s._recognize_intent("就这样")
                assert result == "stop"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_show(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "show"}
                result = await s._recognize_intent("看看")
                assert result == "show"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_skip(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "skip"}
                result = await s._recognize_intent("先不看了")
                assert result == "skip"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_direct_write(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "direct_write"}
                result = await s._recognize_intent("直接写入")
                assert result == "direct_write"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_continue(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "continue"}
                result = await s._recognize_intent("我想做个优惠券")
                assert result == "continue"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_continue_negation(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "continue"}
                result = await s._recognize_intent("我不想就这样结束")
                assert result == "continue"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_continue_hesitation(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "continue"}
                result = await s._recognize_intent("先看看再说")
                assert result == "continue"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_intent_stop_implicit(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "stop"}
                result = await s._recognize_intent("赶紧给我出方案别墨迹了")
                assert result == "stop"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_invalid_intent_fallback_to_continue(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"intent": "invalid_value"}
                result = await s._recognize_intent("test")
                assert result == "continue"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_ollama_failure_returns_continue(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.side_effect = Exception("ollama down")
                result = await s._recognize_intent("就这样")
                assert result == "continue"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_missing_intent_key_returns_continue(self):
        s, d = _make_mock_session()
        try:
            async def t():
                s.llm.judge_json.return_value = {"other": "value"}
                result = await s._recognize_intent("test")
                assert result == "continue"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestIntentRouting:
    def test_route_stop_with_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s.state_manager.set_pending_confirm(".shutong/01-vision.md", "# Vision\nTest")
                s._pending_draft = {"path": ".shutong/01-vision.md", "content": "# Vision\nTest"}
                s.llm.judge_json.return_value = {"intent": "stop"}
                msgs = await s.process("chat", {"text": "就这样"})
                types = [m.type for m in msgs]
                assert "file_confirmed" in types
                assert s.state_manager.get_status(".shutong/01-vision.md").value == "confirmed"
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_route_stop_without_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s._pending_draft = None
                # 第1次 judge_json = 意图识别, 第2次 = _force_preview 预览内容
                s.llm.judge_json = AsyncMock(side_effect=[
                    {"intent": "stop"},
                    {
                        "understanding_summary": "用户要做优惠券系统",
                        "assumptions": [
                            {"content": "面向电商", "source": "用户描述", "user_original": "面向电商"},
                        ],
                        "gaps": [{"content": "有效期"}],
                    },
                ])
                msgs = await s.process("chat", {"text": "就这样"})
                types = [m.type for m in msgs]
                assert "understanding" in types
                assert "file_tree" in types
                understanding_msg = [m for m in msgs if m.type == "understanding"][0]
                content = understanding_msg.payload["content"]
                assert "确认" in content
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_route_show_with_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s._pending_draft = {"path": ".shutong/01-vision.md", "content": "# Vision\nTest"}
                s.llm.judge_json.return_value = {"intent": "show"}
                msgs = await s.process("chat", {"text": "看看"})
                types = [m.type for m in msgs]
                assert "file_draft" in types
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_route_show_without_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s._pending_draft = None
                s.llm.judge_json.return_value = {"intent": "show", "action": "chat", "reasoning": "hello", "has_uncertainty": False}
                msgs = await s.process("chat", {"text": "看看"})
                types = [m.type for m in msgs]
                assert "file_draft" not in types
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_route_skip_clears_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s._pending_draft = {"path": ".shutong/01-vision.md", "content": "# Vision\nTest"}
                s.llm.judge_json.return_value = {"intent": "skip"}
                msgs = await s.process("chat", {"text": "先不看了"})
                types = [m.type for m in msgs]
                assert "system" in types
                assert s._pending_draft is None
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_route_direct_write_with_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s.state_manager.set_pending_confirm(".shutong/01-vision.md", "# Vision\nTest")
                s._pending_draft = {"path": ".shutong/01-vision.md", "content": "# Vision\nTest"}
                s.llm.judge_json.return_value = {"intent": "direct_write"}
                msgs = await s.process("chat", {"text": "直接写入"})
                types = [m.type for m in msgs]
                assert "file_confirmed" in types
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_route_continue_goes_to_llm(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s._pending_draft = None
                s.llm.judge_json.return_value = {"intent": "continue", "action": "chat", "reasoning": "你好", "has_uncertainty": False}
                msgs = await s.process("chat", {"text": "你好"})
                types = [m.type for m in msgs]
                assert "ai" in types
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestSemanticConfirm:
    def test_direct_write_writes_file(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s.state_manager.set_pending_confirm(".shutong/01-vision.md", "# Vision\nReal content")
                s._pending_draft = {"path": ".shutong/01-vision.md", "content": "# Vision\nReal content"}
                s.llm.judge_json = AsyncMock(return_value={"intent": "direct_write"})
                msgs = await s.process("chat", {"text": "确认"})
                types = [m.type for m in msgs]
                assert "file_confirmed" in types
                assert s.state_manager.get_status(".shutong/01-vision.md").value == "confirmed"
                assert s._pending_draft is None
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_direct_write_variants(self):
        for keyword in ["确认", "好的", "可以", "就这样写"]:
            s, d = _make_mock_session()
            try:
                async def t():
                    await s.process("init_project", {})
                    s.state_manager.set_pending_confirm(".shutong/01-vision.md", "# Vision\nTest")
                    s._pending_draft = {"path": ".shutong/01-vision.md", "content": "# Vision\nTest"}
                    s.llm.judge_json = AsyncMock(return_value={"intent": "direct_write"})
                    msgs = await s.process("chat", {"text": keyword})
                    types = [m.type for m in msgs]
                    assert "file_confirmed" in types, f"Keyword '{keyword}' should trigger direct_write"
                asyncio.get_event_loop().run_until_complete(t())
            finally:
                shutil.rmtree(d, ignore_errors=True)

    def test_no_write_without_pending_draft(self):
        s, d = _make_mock_session()
        try:
            async def t():
                await s.process("init_project", {})
                s._pending_draft = None
                s.llm.judge_json.return_value = {"intent": "direct_write"}
                msgs = await s.process("chat", {"text": "确认"})
                types = [m.type for m in msgs]
                assert "file_confirmed" not in types
            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)
