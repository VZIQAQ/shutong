"""
模块: spec_manager
职责: Spec管理器 —— Spec的生成、格式化、锁定和文件持久化
创建: 2026-07-18
状态: 已完成

设计原则:
- 所有Spec存储在 specs/ 目录下
- 锁定通过修改frontmatter实现（status: DRAFT → LOCKED）
- 锁定后同步生成测试用例文件
"""

import re
from datetime import datetime, timezone
from typing import Optional

from .file_bridge import FileBridge

SPEC_SYSTEM_PROMPT = """\
你负责将已确认的项目规范整理成结构化的Spec文档。

输出格式（Markdown，含YAML frontmatter）:

---
status: DRAFT
round: N
feature: 功能名
created_at: 时间
locked_at: null
---

# 功能名 Spec

## 1. 功能概述
（2-3句话描述这个功能是什么、解决什么问题）

## 2. 用户故事
作为[角色]，我想[做什么]，以便[达成什么目的]

## 3. 验收标准
- 给定[条件]，当[操作]时，那么[结果]

## 4. 数据模型
（实体、字段、关系）

## 5. 状态机
| 当前状态 | 触发条件 | 下一状态 | 系统动作 |

## 6. 异常处理
| 异常场景 | 系统反应 | 用户提示 |

## 7. 权限规则
| 角色 | 可访问资源 | 可执行操作 |

## 8. 非功能性需求
（性能、安全等，可选）

## 9. 待确认项（PENDING）
（追问中跳过的项）

约束：
- 基于已确认的项目规范文件生成，不臆造
- 状态机必须完整
- 异常处理至少3个场景
- 金额用整数分存储
- 只输出Markdown
"""


SPEC_TEMPLATE = """\
---
status: {status}
round: {round}
feature: {feature}
created_at: {created_at}
locked_at: {locked_at}
---

# {feature} Spec

## 1. 功能概述
{overview}

## 2. 用户故事
{user_story}

## 3. 验收标准
{acceptance_criteria}

## 4. 数据模型
{data_model}

## 5. 状态机
{state_machine}

## 6. 异常处理
{exception_handling}

## 7. 权限规则
{permission_rules}

## 8. 非功能性需求
{non_functional}

## 9. 待确认项（PENDING）
{pending_items}
"""

TEST_TEMPLATE = """\
---
spec: {spec_path}
generated_at: {generated_at}
---

# 测试用例 —— {feature}

## 正常流程测试
（基于Spec的验收标准生成）

## 异常流程测试
（基于Spec的异常处理章节生成）

## 业务规则验证
（基于Spec的权限规则生成）
"""


class SpecManager:
    """Spec管理器 —— 负责Spec的格式化、锁定和文件持久化"""

    def __init__(self, file_bridge: FileBridge):
        self.file_bridge = file_bridge
        self._current_spec: Optional[str] = None
        self._current_feature: Optional[str] = None
        self._current_round: int = 0

    def get_next_round(self) -> int:
        """获取下一个轮次编号"""
        specs = self.file_bridge.list_specs()
        if not specs:
            return 1
        rounds = [s["round"] for s in specs if isinstance(s["round"], int)]
        return max(rounds, default=0) + 1

    def format_spec(
        self,
        feature_name: str,
        round_num: int,
        llm_output: str,
    ) -> str:
        """将LLM输出格式化为标准Spec文档（含frontmatter）"""
        now = datetime.now(timezone.utc).isoformat()

        if llm_output.startswith("---"):
            content = llm_output
        else:
            content = (
                f"---\n"
                f"status: DRAFT\n"
                f"round: {round_num}\n"
                f"feature: {feature_name}\n"
                f"created_at: {now}\n"
                f"locked_at: null\n"
                f"---\n\n"
                f"{llm_output}"
            )

        self._current_spec = content
        self._current_feature = feature_name
        self._current_round = round_num
        return content

    def lock_spec(self, feature_name: str, round_num: int) -> str:
        """
        锁定Spec：修改frontmatter为LOCKED，写入文件

        Returns:
            写入的文件相对路径
        """
        if not self._current_spec:
            raise ValueError("没有可锁定的Spec草案")

        now = datetime.now(timezone.utc).isoformat()
        content = self._current_spec
        content = re.sub(r"status: DRAFT", "status: LOCKED", content)
        content = re.sub(r"locked_at: null", f"locked_at: {now}", content)

        filename = f"specs/round-{round_num:03d}-{feature_name}.md"
        self.file_bridge.write_file(filename, content)

        self._generate_tests(filename, feature_name)
        self._current_spec = content
        return filename

    def get_current_spec(self) -> Optional[str]:
        """获取当前Spec草案内容"""
        return self._current_spec

    def _generate_tests(self, spec_path: str, feature_name: str) -> None:
        """基于Spec生成测试用例文件"""
        now = datetime.now(timezone.utc).isoformat()
        test_content = TEST_TEMPLATE.format(
            spec_path=spec_path,
            generated_at=now,
            feature=feature_name,
        )
        test_path = spec_path.replace(".md", "-tests.md")
        self.file_bridge.write_file(test_path, test_content)
