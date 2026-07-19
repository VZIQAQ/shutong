"""
模块: file_bridge
职责: 文件系统桥接层 —— 所有文件操作的唯一入口
创建: 2026-07-18
状态: 已完成

安全约束:
- 所有路径操作必须在 project_root 内
- 写入使用原子替换（tmp + os.replace）
- 不引入外部依赖
"""

import os
import re
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("shutong.file")


class FileBridge:
    """文件系统桥接层 —— 所有文件操作的唯一入口"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def _validate_path(self, relative_path: str) -> Path:
        """安全路径检查：确保操作不超出项目根目录"""
        target = (self.project_root / relative_path).resolve()
        if not str(target).startswith(str(self.project_root)):
            raise ValueError(f"路径越界: {relative_path}")
        return target

    def read_file(self, relative_path: str) -> str:
        """读取文件内容"""
        path = self._validate_path(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> None:
        """原子写入文件（先写临时文件，再重命名）"""
        path = self._validate_path(relative_path)
        logger.info("[WRITE] path=%s content_len=%d full_path=%s", relative_path, len(content), path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), suffix=".tmp", prefix=".st_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(path))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def scan_directory(self, relative_path: str = ".") -> list[dict]:
        """扫描目录，返回文件树结构"""
        path = self._validate_path(relative_path)
        result = []
        for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name)):
            node = {
                "name": item.name,
                "path": str(item.relative_to(self.project_root)),
                "type": "directory" if item.is_dir() else "file",
            }
            if item.is_dir():
                node["children"] = []
            result.append(node)
        return result

    def file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        try:
            path = self._validate_path(relative_path)
            return path.exists()
        except ValueError:
            return False

    def list_specs(self) -> list[dict]:
        """列出所有specs文件，返回元数据"""
        specs_dir = self.project_root / ".shutong" / "specs"
        if not specs_dir.exists():
            return []

        specs = []
        for f in sorted(specs_dir.glob("round-*.md")):
            content = f.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(content)
            specs.append({
                "fileName": f.name,
                "round": meta.get("round"),
                "feature": meta.get("feature"),
                "status": meta.get("status", "DRAFT"),
                "lockedAt": meta.get("locked_at"),
            })
        return specs

    def _parse_frontmatter(self, content: str) -> dict:
        """解析Markdown文件的YAML frontmatter"""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return {}
        result = {}
        for line in match.group(1).split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == "round":
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        pass
                result[key] = value
        return result
