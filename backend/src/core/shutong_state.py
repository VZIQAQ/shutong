"""
模块: shutong_state
职责: 每个.shutong/文件的独立状态管理
创建: 2026-07-18
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from core.file_bridge import FileBridge

logger = logging.getLogger("shutong.state")


class FileStatus(str, Enum):
    EMPTY = "empty"
    DRAFTING = "drafting"
    PENDING_CONFIRM = "pending_confirm"
    CONFIRMED = "confirmed"
    LOCKED = "locked"


SHUTONG_FILES = [
    "README.md",
    "01-vision.md",
    "02-persona.md",
    "03-techstack.md",
    "04-codestyle.md",
    "05-domain.md",
    "06-architecture.md",
    "07-patterns.md",
    "08-lessons.md",
    "backlog.md",
]


@dataclass
class ShutongFileState:
    path: str
    name: str
    status: FileStatus = FileStatus.EMPTY
    draft_content: Optional[str] = None
    confirmed_content: Optional[str] = None
    last_updated: float = field(default_factory=time.time)


class ShutongStateManager:
    def __init__(self, fb: FileBridge):
        self.fb = fb
        self.files: dict[str, ShutongFileState] = {}
        self._init_from_disk()

    def _init_from_disk(self):
        for name in SHUTONG_FILES:
            path = f".shutong/{name}"
            content = self.fb.read_file(path) if self.fb.file_exists(path) else ""
            has_content = content.strip() and "[待填写]" not in content
            self.files[path] = ShutongFileState(
                path=path,
                name=name,
                status=FileStatus.CONFIRMED if has_content else FileStatus.EMPTY,
                confirmed_content=content if has_content else None,
            )

        if self.fb.file_exists(".shutong/specs"):
            specs_dir = self.fb.project_root / ".shutong" / "specs"
            for f in sorted(specs_dir.glob("round-*.md")):
                content = f.read_text(encoding="utf-8")
                meta = self._parse_frontmatter(content)
                path = f".shutong/specs/{f.name}"
                status = FileStatus.LOCKED if meta.get("status") == "LOCKED" else FileStatus.PENDING_CONFIRM
                self.files[path] = ShutongFileState(
                    path=path,
                    name=f.name,
                    status=status,
                )

    @staticmethod
    def _parse_frontmatter(content: str) -> dict:
        import re
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return {}
        result = {}
        for line in match.group(1).split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip().strip('"').strip("'")
        return result

    def get_status(self, path: str) -> FileStatus:
        if path in self.files:
            return self.files[path].status
        return FileStatus.EMPTY

    def set_draft(self, path: str, content: str):
        if path not in self.files:
            name = path.split("/")[-1]
            self.files[path] = ShutongFileState(path=path, name=name)
        self.files[path].status = FileStatus.DRAFTING
        self.files[path].draft_content = content
        self.files[path].last_updated = time.time()

    def set_pending_confirm(self, path: str, content: str):
        if path not in self.files:
            name = path.split("/")[-1]
            self.files[path] = ShutongFileState(path=path, name=name)
        self.files[path].status = FileStatus.PENDING_CONFIRM
        self.files[path].draft_content = content
        self.files[path].last_updated = time.time()

    def confirm_file(self, path: str) -> str:
        if path not in self.files:
            logger.warning("[CONFIRM] path not found: %s", path)
            return ""
        f = self.files[path]
        content = f.draft_content or ""
        logger.info("[CONFIRM] path=%s content_len=%d draft_content=%s", path, len(content), type(f.draft_content).__name__)
        self.fb.write_file(path, content)
        f.status = FileStatus.CONFIRMED
        f.confirmed_content = content
        f.draft_content = None
        f.last_updated = time.time()
        return content

    def get_confirmed_files(self) -> dict[str, str]:
        return {
            p: f.confirmed_content
            for p, f in self.files.items()
            if f.status == FileStatus.CONFIRMED and f.confirmed_content
        }

    def get_all_statuses(self) -> list[dict]:
        return [
            {"path": f.path, "name": f.name, "status": f.status.value}
            for f in self.files.values()
        ]
