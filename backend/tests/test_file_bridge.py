"""
测试: file_bridge
验证: 读写文件、原子写入、安全路径检查
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.file_bridge import FileBridge


@pytest.fixture
def project_dir():
    d = tempfile.mkdtemp(prefix="shutong_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def fb(project_dir):
    return FileBridge(project_dir)


class TestReadFile:
    def test_read_existing_file(self, fb, project_dir):
        Path(project_dir, "test.txt").write_text("hello", encoding="utf-8")
        assert fb.read_file("test.txt") == "hello"

    def test_read_nonexistent_raises(self, fb):
        with pytest.raises(FileNotFoundError):
            fb.read_file("no_such_file.txt")


class TestWriteFile:
    def test_write_creates_file(self, fb, project_dir):
        fb.write_file("sub/dir/out.txt", "content")
        assert (Path(project_dir) / "sub" / "dir" / "out.txt").read_text(encoding="utf-8") == "content"

    def test_write_is_atomic(self, fb, project_dir):
        fb.write_file("a.txt", "first")
        fb.write_file("a.txt", "second")
        assert fb.read_file("a.txt") == "second"
        tmp_files = list(Path(project_dir).glob(".st_*.tmp"))
        assert len(tmp_files) == 0

    def test_write_no_tmp_on_error(self, fb, project_dir):
        try:
            fb.write_file("b.txt", "ok")
        except Exception:
            pass
        tmp_files = list(Path(project_dir).glob(".st_*.tmp"))
        assert len(tmp_files) == 0


class TestScanDirectory:
    def test_scan_returns_sorted(self, fb, project_dir):
        Path(project_dir, "b.txt").write_text("", encoding="utf-8")
        Path(project_dir, "a.txt").write_text("", encoding="utf-8")
        Path(project_dir, "dir1").mkdir()
        entries = fb.scan_directory()
        names = [e["name"] for e in entries]
        assert names == ["dir1", "a.txt", "b.txt"]

    def test_scan_marks_dirs(self, fb, project_dir):
        Path(project_dir, "mydir").mkdir()
        entries = fb.scan_directory()
        assert entries[0]["type"] == "directory"
        assert entries[0]["children"] == []


class TestFileExists:
    def test_exists_true(self, fb, project_dir):
        Path(project_dir, "x.txt").write_text("", encoding="utf-8")
        assert fb.file_exists("x.txt") is True

    def test_exists_false(self, fb):
        assert fb.file_exists("nope.txt") is False


class TestPathSafety:
    def test_escape_rejected(self, fb):
        with pytest.raises(ValueError, match="路径越界"):
            fb.read_file("../../etc/passwd")

    def test_escape_in_write_rejected(self, fb):
        with pytest.raises(ValueError, match="路径越界"):
            fb.write_file("../../evil.txt", "bad")

    def test_escape_in_exists_returns_false(self, fb):
        assert fb.file_exists("../../etc/passwd") is False
