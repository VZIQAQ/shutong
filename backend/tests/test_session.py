"""测试: session.py 核心流程"""
import sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.session import Session
from core.shutong_state import FileStatus


def _make_session():
    d = tempfile.mkdtemp()
    return Session(d), d


class TestInit:
    def test_init_creates_files(self):
        s, d = _make_session()
        try:
            msgs = s.process.__wrapped__(s, "init_project", {}) if hasattr(s.process, '__wrapped__') else None
            import asyncio
            msgs = asyncio.get_event_loop().run_until_complete(s.process("init_project", {}))
            types = [m.type for m in msgs]
            assert "system" in types
            assert "file_tree" in types
            ft = [m for m in msgs if m.type == "file_tree"][0]
            assert len(ft.payload["files"]) >= 10
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestHandleDraft:
    def test_draft_file_with_uncertainty(self):
        s, d = _make_session()
        try:
            import asyncio

            async def t():
                msgs = await s.process("init_project", {})
                judgment = {
                    "action": "draft_file",
                    "target_file": "01-vision.md",
                    "reasoning": "需要完善愿景",
                    "has_uncertainty": True,
                    "next_question": "用户面向哪个行业？",
                }
                result = await s._handle_draft(judgment, "test")
                types = [m.type for m in result]
                assert "question" in types
                assert ".shutong/01-vision.md" in s.state_manager.files

            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_draft_file_without_uncertainty(self):
        s, d = _make_session()
        try:
            import asyncio

            async def t():
                msgs = await s.process("init_project", {})
                judgment = {
                    "action": "draft_file",
                    "target_file": "03-techstack.md",
                    "reasoning": "技术栈已明确",
                    "has_uncertainty": False,
                    "draft_content": "# Tech\nReact 18",
                }
                result = await s._handle_draft(judgment, "用React")
                types = [m.type for m in result]
                # 新逻辑：无追问时返回ai消息（"你想看看吗？"），不直接展示file_draft
                assert "ai" in types
                assert s.state_manager.get_status(".shutong/03-techstack.md").value == "pending_confirm"
                # 验证pending_draft被设置
                assert s._pending_draft is not None
                assert s._pending_draft["path"] == ".shutong/03-techstack.md"

            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestHandleConfirm:
    def test_confirm_writes_file(self):
        s, d = _make_session()
        try:
            import asyncio

            async def t():
                msgs = await s.process("init_project", {})
                s.state_manager.set_pending_confirm(".shutong/01-vision.md", "# Vision\nTest")
                result = s._handle_confirm({"path": ".shutong/01-vision.md"})
                assert s.state_manager.get_status(".shutong/01-vision.md") == FileStatus.CONFIRMED
                assert s.fb.file_exists(".shutong/01-vision.md")

            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_confirm_normalizes_path(self):
        s, d = _make_session()
        try:
            import asyncio

            async def t():
                msgs = await s.process("init_project", {})
                s.state_manager.set_pending_confirm(".shutong/01-vision.md", "# Vision\nTest")
                result = s._handle_confirm({"path": "01-vision.md"})
                assert s.state_manager.get_status(".shutong/01-vision.md") == FileStatus.CONFIRMED

            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestPathNormalization:
    def test_normalize_path(self):
        s, d = _make_session()
        try:
            assert s._normalize_path("01-vision.md") == ".shutong/01-vision.md"
            assert s._normalize_path(".shutong/01-vision.md") == ".shutong/01-vision.md"
            assert s._normalize_path("specs/round-001.md") == "specs/round-001.md"
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestProcessingLock:
    def test_is_processing_blocks(self):
        s, d = _make_session()
        try:
            import asyncio

            async def t():
                s.is_processing = True
                msgs = await s.process("chat", {"text": "test"})
                assert len(msgs) == 1
                assert msgs[0].type == "error"
                assert "处理中" in msgs[0].payload["content"]

            asyncio.get_event_loop().run_until_complete(t())
        finally:
            shutil.rmtree(d, ignore_errors=True)
