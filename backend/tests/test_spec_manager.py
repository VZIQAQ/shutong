"""
测试: spec_manager
验证: 轮次计算、格式化、锁定后状态为LOCKED
"""

import shutil
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.file_bridge import FileBridge
from core.spec_manager import SpecManager


def _make_fb():
    d = tempfile.mkdtemp(prefix="shutong_spec_")
    return FileBridge(d), d


class TestNextRound:
    def test_first_round(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            assert sm.get_next_round() == 1
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_increments_round(self):
        fb, d = _make_fb()
        try:
            specs_dir = Path(d) / ".shutong" / "specs"
            specs_dir.mkdir(parents=True)
            (specs_dir / "round-001-foo.md").write_text(
                "---\nstatus: LOCKED\nround: 1\nfeature: foo\n---\n# foo",
                encoding="utf-8",
            )
            sm = SpecManager(fb)
            assert sm.get_next_round() == 2
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestFormatSpec:
    def test_adds_frontmatter(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            result = sm.format_spec("coupon", 3, "# 优惠券功能")
            assert "status: DRAFT" in result
            assert "round: 3" in result
            assert "feature: coupon" in result
            assert "# 优惠券功能" in result
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_preserves_existing_frontmatter(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            llm_out = "---\nstatus: DRAFT\nround: 1\nfeature: x\n---\n# Content"
            result = sm.format_spec("x", 1, llm_out)
            assert result.startswith("---")
            assert "# Content" in result
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestLockSpec:
    def test_lock_changes_status(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            sm.format_spec("coupon", 1, "# Coupon Spec")
            path = sm.lock_spec("coupon", 1)

            assert path == "specs/round-001-coupon.md"
            content = fb.read_file(path)
            assert "status: LOCKED" in content
            assert "locked_at:" in content
            assert "null" not in content.split("locked_at:")[1].split("\n")[0]
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_lock_generates_tests(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            sm.format_spec("coupon", 1, "# Coupon Spec")
            sm.lock_spec("coupon", 1)

            test_path = "specs/round-001-coupon-tests.md"
            assert fb.file_exists(test_path)
            test_content = fb.read_file(test_path)
            assert "coupon" in test_content
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_lock_without_spec_raises(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            try:
                sm.lock_spec("x", 1)
                assert False, "应该抛出异常"
            except ValueError as e:
                assert "没有可锁定的Spec草案" in str(e)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestGetCurrentSpec:
    def test_returns_none_initially(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            assert sm.get_current_spec() is None
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_returns_spec_after_format(self):
        fb, d = _make_fb()
        try:
            sm = SpecManager(fb)
            sm.format_spec("test", 1, "content")
            assert sm.get_current_spec() is not None
        finally:
            shutil.rmtree(d, ignore_errors=True)
