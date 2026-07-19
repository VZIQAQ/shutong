"""
模块: rule_engine
职责: 文本模式规则引擎 —— 扫描LLM输出中的结构化认知显化
创建: 2026-07-19
"""

import re
from dataclasses import dataclass, field


@dataclass
class RuleResult:
    should_clarify: bool
    reasons: list[str] = field(default_factory=list)
    pure_guess_count: int = 0
    blocking_gap_count: int = 0
    has_structure: bool = False
    assumption_sources: dict[str, int] = field(default_factory=dict)


class RuleEngine:
    """规则引擎：只做文本模式扫描，不调用LLM，零成本、确定性"""

    def check(self, llm_output: str) -> RuleResult:
        reasons: list[str] = []

        has_assumptions = "假设清单" in llm_output
        has_gaps = "盲区清单" in llm_output
        has_structure = has_assumptions and has_gaps

        if not has_structure:
            reasons.append("缺少假设清单或盲区清单结构")

        pure_guesses = re.findall(r"来源：纯猜测", llm_output)
        if pure_guesses:
            reasons.append(f"发现{len(pure_guesses)}个D级假设（纯猜测）")

        blocking_gaps = re.findall(r"是否阻断：是", llm_output)
        if blocking_gaps:
            reasons.append(f"发现{len(blocking_gaps)}个阻断盲区")

        sources: dict[str, int] = {}
        for line in llm_output.split("\n"):
            m = re.search(r"来源：(.+?)(?:\s*\||\s*$)", line)
            if m:
                src = m.group(1).strip()
                if src:
                    sources[src] = sources.get(src, 0) + 1

        should_clarify = bool(pure_guesses or blocking_gaps or not has_structure)

        return RuleResult(
            should_clarify=should_clarify,
            reasons=reasons,
            pure_guess_count=len(pure_guesses),
            blocking_gap_count=len(blocking_gaps),
            has_structure=has_structure,
            assumption_sources=sources,
        )
