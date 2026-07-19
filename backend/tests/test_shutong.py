"""测试: shutong_init + shutong_state (新API)"""
import sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.file_bridge import FileBridge
from core.shutong_init import init_shutong_dir, TEMPLATES
from core.shutong_state import ShutongStateManager, FileStatus


def test_init_creates_all_files():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        created = init_shutong_dir(fb)
        assert len(created) == len(TEMPLATES) + 2
        for name in TEMPLATES:
            assert fb.file_exists(f".shutong/{name}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_init_idempotent():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        first = init_shutong_dir(fb)
        second = init_shutong_dir(fb)
        assert len(first) > 0
        assert len(second) == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_init_does_not_overwrite():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        fb.write_file(".shutong/01-vision.md", "# My Custom Vision")
        init_shutong_dir(fb)
        content = fb.read_file(".shutong/01-vision.md")
        assert "My Custom Vision" in content
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_state_empty_for_new_files():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        init_shutong_dir(fb)
        state = ShutongStateManager(fb)
        for name in ["01-vision.md", "02-persona.md", "05-domain.md"]:
            status = state.get_status(f".shutong/{name}")
            assert status == FileStatus.EMPTY, f"{name} should be EMPTY, got {status}"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_state_confirmed_for_spec():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        init_shutong_dir(fb)
        fb.write_file(".shutong/specs/round-001-test.md", "---\nstatus: LOCKED\n---\n# Test")
        state = ShutongStateManager(fb)
        status = state.get_status(".shutong/specs/round-001-test.md")
        assert status == FileStatus.LOCKED
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_state_pending_confirm():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        init_shutong_dir(fb)
        state = ShutongStateManager(fb)
        state.set_pending_confirm(".shutong/05-domain.md", "# Domain\n实体: Order")
        status = state.get_status(".shutong/05-domain.md")
        assert status == FileStatus.PENDING_CONFIRM
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_confirm_file():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        init_shutong_dir(fb)
        state = ShutongStateManager(fb)
        state.set_pending_confirm(".shutong/01-vision.md", "# Vision\nConfirmed")
        state.confirm_file(".shutong/01-vision.md")
        assert state.get_status(".shutong/01-vision.md") == FileStatus.CONFIRMED
        assert fb.file_exists(".shutong/01-vision.md")
        assert "Confirmed" in fb.read_file(".shutong/01-vision.md")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_get_all_statuses():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        init_shutong_dir(fb)
        state = ShutongStateManager(fb)
        files = state.get_all_statuses()
        names = [f["name"] for f in files]
        assert "README.md" in names
        assert "01-vision.md" in names
        assert all("status" in f for f in files)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_get_confirmed_files():
    d = tempfile.mkdtemp()
    try:
        fb = FileBridge(d)
        init_shutong_dir(fb)
        state = ShutongStateManager(fb)
        state.set_pending_confirm(".shutong/01-vision.md", "# Vision\nContent")
        state.confirm_file(".shutong/01-vision.md")
        confirmed = state.get_confirmed_files()
        assert ".shutong/01-vision.md" in confirmed
        assert "Content" in confirmed[".shutong/01-vision.md"]
    finally:
        shutil.rmtree(d, ignore_errors=True)
