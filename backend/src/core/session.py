"""
模块: session
职责: 书童V1核心会话逻辑 —— 模型动态判断动作 + 文件级追问 + 草案确认
创建: 2026-07-18
"""

from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from core.file_bridge import FileBridge
from core.llm_client import LLMClient
from core.shutong_state import ShutongStateManager, FileStatus
from core.rule_engine import RuleEngine

logger = logging.getLogger("shutong.session")

JUDGE_SYSTEM_PROMPT = """\
# 角色：书童V1 文件完善助手

你是书童V1，负责通过对话帮助用户完善项目规范文件。

## 当前任务
根据用户对话，判断需要完善哪个.shutong/文件，或直接回答问题。

## 可完善的文件清单
1. 01-vision.md - 项目愿景（用户描述"做什么""给谁用"时）
2. 02-persona.md - 用户角色（用户提及权限/角色时）
3. 03-techstack.md - 技术栈（用户提及技术选型时）
4. 04-codestyle.md - 代码风格（用户提及规范时）
5. 05-domain.md - 领域模型（用户描述业务实体/流程时）
6. 06-architecture.md - 架构决策（用户提及性能/安全时）
7. 07-patterns.md - 模式约定（用户提及可复用设计时）
8. 08-lessons.md - 经验教训（开发中发现问题时）
9. backlog.md - 需求池（用户提及"以后做"时）
10. specs/round-xxx.md - Spec文档（用户要求生成Spec时）

## 判断规则
1. 用户首次描述项目 → draft_file, target: 01-vision.md
2. 用户提及技术 → draft_file, target: 03-techstack.md
3. 用户描述业务规则/实体 → draft_file, target: 05-domain.md
4. 用户说"写个Spec"或"生成Spec" → generate_spec
5. 用户纯提问 → answer_question
6. 用户闲聊 → chat
7. 用户明确说要改某个文件 → draft_file, target: 对应文件

## 认知显化输出格式（必须严格遵守）

每次分析用户需求时，你必须输出以下结构：

1. 先用JSON告知意图（action/target_file等）
2. 在reasoning字段中，必须包含完整的认知显化结构

JSON格式：
{
  "action": "draft_file|update_file|answer_question|generate_spec|chat",
  "target_file": "01-vision.md",
  "reasoning": "包含以下结构的完整认知显化文本",
  "has_uncertainty": true/false,
  "next_question": "自然语言的追问问题（1-2句话，仅当has_uncertainty=true时填写）",
  "understanding_summary": "基于已有信息，我理解的需求是...",
  "draft_content": "当has_uncertainty=false时，这里放生成的完整Markdown文件内容"
}

reasoning字段中的认知显化结构（当action=draft_file时必须包含）：

【认知显化】
理解复述：[用你自己的话复述需求]

假设清单：
1. [假设内容] | 来源：[用户说过/上下文推断/行业惯例/纯猜测] | 猜错后果：[描述]

盲区清单：
1. [缺失信息] | 为什么重要：[描述] | 是否阻断：[是/否]

[如果存在纯猜测或阻断盲区，has_uncertainty=true，填写next_question]
[如果信息充分，has_uncertainty=false，填写draft_content]

## 追问规则
- 只问业务规则，不问技术实现
- 一次只问一个问题，用自然语言表达
- 追问要基于已确认的文件内容，不要重复问已知信息
- 发现矛盾时追问澄清

## 约束
1. 只输出JSON
2. next_question是自然语言字符串，不是选项列表
3. 不追问技术实现
4. draft_content必须是完整的Markdown文件内容
5. 理解摘要整合所有已确认信息
"""

INTENT_SYSTEM_PROMPT = """\
你是意图识别器。

你必须基于完整对话上下文做语义判断，不能局部匹配关键词。
用户的否定词（"不想""不要""别"）会反转意图。
用户的犹豫表达（"先看看""再说吧"）不属于任何明确意图。

禁止：
- 禁止因为用户输入包含某个词就判定对应意图
- 禁止对模糊输入做强行归类
- 禁止输出解释、推理过程、或任何JSON之外的文本
"""

INTENT_USER_PROMPT_TEMPLATE = """\
对话历史：
{conversation_history}

用户最后输入："{user_input}"

可选意图：
- stop：用户明确要求停止追问、直接出方案
- show：用户明确要求查看当前草案
- skip：用户明确拒绝当前草案
- direct_write：用户明确要求直接写入
- continue：正常对话、回答问题、表达模糊态度、或含否定词

边界案例（必须遵守）：
- "就这样" → stop（用户不想继续回答了，要求直接出方案）
- "就这样吧" → stop
- "先这样吧" → stop
- "别问了" → stop
- "确认" → direct_write（用户确认当前草案，要求写入文件）
- "好的" → direct_write（用户确认当前草案）
- "可以" → direct_write（用户确认当前草案）
- "就这样写" → direct_write（用户要求写入）
- "我不想就这样结束" → continue（"不想"否定了停止意图）
- "先看看再说" → continue（犹豫，无明确意图）
- "赶紧给我出方案别墨迹了" → stop（语义是要求停止追问）

只输出JSON：{{"intent": "xxx"}}"""


@dataclass
class Message:
    type: str
    payload: dict


class Session:
    """书童V1会话核心"""

    def __init__(self, project_root: str):
        self.fb = FileBridge(project_root)
        self.llm = LLMClient()
        self.state_manager = ShutongStateManager(self.fb)
        self.rule_engine = RuleEngine()
        self.clarify_counter: dict[str, int] = {}
        self.is_processing = False
        self.conversation_history: list[dict] = []
        self.current_focus: Optional[str] = None
        self._pending_draft: Optional[dict] = None  # 待展示的草案

    async def process(self, msg_type: str, payload: dict) -> list[Message]:
        if self.is_processing:
            return [Message("error", {"content": "正在处理中，请稍候..."})]

        self.is_processing = True
        try:
            return await self._process_inner(msg_type, payload)
        except Exception as e:
            return [Message("error", {"content": f"处理失败: {str(e)[:100]}"})]
        finally:
            self.is_processing = False

    async def _process_inner(self, msg_type: str, payload: dict) -> list[Message]:
        if msg_type == "init_project":
            return self._handle_init()

        if msg_type == "confirm_file":
            return self._handle_confirm(payload)

        if msg_type == "revise_file":
            return await self._handle_revise(payload)

        user_input = payload.get("text", "").strip()
        if not user_input:
            return []

        self._add_history("user", user_input)

        # 意图识别：模型语义判断
        intent = await self._recognize_intent(user_input)
        logger.info("[DEBUG] intent=%s pending_draft=%s", intent, self._pending_draft is not None)

        # 规则层：确定性执行校验
        if intent == "stop":
            if self._pending_draft:
                logger.info("[DEBUG] stop: confirming pending draft %s", self._pending_draft["path"])
                draft = self._pending_draft
                self._pending_draft = None
                self.state_manager.confirm_file(draft["path"])
                name = draft["path"].split("/")[-1]
                return self._build_post_confirm(draft["path"], name)
            else:
                logger.info("[DEBUG] stop: no pending_draft, force preview")
                return await self._force_preview(user_input)

        if intent == "show" and self._pending_draft:
            draft = self._pending_draft
            self._pending_draft = None
            return [
                Message("file_draft", {"path": draft["path"], "content": draft["content"]}),
                Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
            ]

        if intent == "skip":
            self._pending_draft = None
            return [Message("system", {"content": "已跳过草案，请继续描述需求。"})]

        if intent == "direct_write" and self._pending_draft:
            draft = self._pending_draft
            self._pending_draft = None
            content = draft.get("content", "")
            logger.info("[DEBUG] direct_write: path=%s content_len=%d", draft["path"], len(content))
            if content:
                self.fb.write_file(draft["path"], content)
            self.state_manager.confirm_file(draft["path"])
            name = draft["path"].split("/")[-1]
            return self._build_post_confirm(draft["path"], name)

        # 默认：continue → 进入LLM正常流程
        return await self._llm_cognition_flow(user_input)

    async def _llm_cognition_flow(self, user_input: str) -> list[Message]:
        """LLM认知显化流程（抽取为独立方法，供意图识别后调用）"""
        context = self._build_context(user_input)

        try:
            judgment = await self.llm.judge_json(JUDGE_SYSTEM_PROMPT, context)
        except Exception:
            judgment = {"action": "chat", "reasoning": "LLM调用失败", "has_uncertainty": False}

        action = judgment.get("action", "chat")
        messages = []

        if action == "draft_file":
            rule_result = self.rule_engine.check(judgment.get("reasoning", ""))
            if rule_result.should_clarify and not judgment.get("has_uncertainty"):
                judgment["has_uncertainty"] = True
                if not judgment.get("next_question"):
                    parts = []
                    if rule_result.pure_guess_count:
                        parts.append(f"我发现有{rule_result.pure_guess_count}个信息是纯猜测的")
                    if rule_result.blocking_gap_count:
                        parts.append(f"有{rule_result.blocking_gap_count}个关键信息缺失")
                    judgment["next_question"] = "、".join(parts) + "，能补充一下吗？"
                topic = judgment.get("target_file", "unknown")
                self.clarify_counter[topic] = self.clarify_counter.get(topic, 0) + 1
                if self.clarify_counter[topic] >= 3:
                    judgment["next_question"] += "\n\n你也可以随时说「就这样」让我先出预览。"
            messages = await self._handle_draft(judgment, user_input)
        elif action == "generate_spec":
            messages = await self._handle_spec(judgment, user_input)
        elif action == "answer_question":
            messages = [Message("ai", {"content": judgment.get("reasoning", user_input)})]
        else:
            messages = [Message("ai", {"content": judgment.get("reasoning", "你好！我是书童，帮你完善项目规范。请描述你要做什么项目？")})]

        for m in messages:
            if m.type in ("ai", "system"):
                self._add_history("assistant", m.payload.get("content", ""))

        return messages

    # ============================================================
    # 意图识别（模型语义判断）
    # ============================================================

    async def _recognize_intent(self, user_input: str) -> str:
        """调用本地模型做语义意图识别，返回意图标签"""
        history_text = ""
        for msg in self.conversation_history[-10:]:
            role = "用户" if msg["role"] == "user" else "书童"
            history_text += f"{role}：{msg['content'][:100]}\n"

        prompt = INTENT_USER_PROMPT_TEMPLATE.format(
            conversation_history=history_text,
            user_input=user_input,
        )

        logger.info("[DEBUG] _recognize_intent: history_len=%d prompt_len=%d", len(history_text), len(prompt))

        try:
            result = await self.llm.judge_json(INTENT_SYSTEM_PROMPT, prompt)
            intent = result.get("intent", "continue")

            logger.info("[INTENT] input=%s intent=%s raw=%s", user_input[:50], intent, str(result)[:100])

            valid_intents = {"stop", "show", "skip", "direct_write", "continue"}
            if intent not in valid_intents:
                intent = "continue"

            return intent

        except Exception as e:
            logger.error("[INTENT] failed: %s", e)
            return "continue"

    async def _force_preview(self, user_input: str) -> list[Message]:
        """用户喊停时，基于已有信息强制生成预览"""
        target = self.current_focus or ".shutong/01-vision.md"
        name = target.split("/")[-1]

        context = self._build_context(user_input)
        prompt = (
            f"基于以下上下文，分析用户需求并输出结构化JSON。\n"
            f"用户明确表示不想继续追问，用已有信息尽可能完善。\n\n"
            f"{context}\n\n"
            f"输出格式（严格JSON）：\n"
            f'{{"understanding_summary": "用1-2句话复述需求",'
            f'"assumptions": [{{"content": "假设内容", "source": "用户描述/行业惯例/推断", "user_original": "用户原话（如有）"}}],'
            f'"gains": [{{"content": "缺失信息"}}]}}\n'
            f"只输出JSON。"
        )

        try:
            result = await self.llm.judge_json(
                "你是需求分析器。根据上下文输出结构化JSON，不要追问。", prompt
            )
        except Exception:
            result = {
                "understanding_summary": f"基于已有信息理解的需求（用户主动停止追问）",
                "assumptions": [],
                "gaps": [],
            }

        preview_text = self._format_force_preview(result)

        self.state_manager.set_pending_confirm(target, preview_text)
        self._pending_draft = {"path": target, "content": preview_text}

        return [
            Message("understanding", {"content": preview_text}),
            Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
        ]

    def _format_force_preview(self, result: dict) -> str:
        """将预览 JSON 格式化为自然语言"""
        understanding = result.get("understanding_summary", "基于已有信息整理的需求理解。")
        assumptions = result.get("assumptions", [])
        gaps = result.get("gaps", [])

        lines = ["好的，基于已确认信息，我先出预览：", "", "【理解复述】", understanding, ""]

        confirmed = [a for a in assumptions if a.get("source") in ("用户描述", "用户说过", "用户确认")]
        if confirmed:
            lines.append("✅ 已确认：")
            for a in confirmed:
                lines.append(f"· {a.get('content', '')}")
                if a.get("user_original"):
                    lines.append(f"  → 用户原话：{a['user_original']}")
            lines.append("")

        guessed = [a for a in assumptions if a.get("source") not in ("用户描述", "用户说过", "用户确认")]
        if guessed:
            lines.append("⚠️ 默认假设（未确认，你可以改）：")
            for a in guessed:
                lines.append(f"· {a.get('content', '')} | 来源：{a.get('source', '推断')}")
            lines.append("")

        if gaps:
            lines.append("❓ 尚未明确（用户主动停止追问）：")
            for g in gaps:
                lines.append(f"· {g.get('content', '')}")
            lines.append("")

        lines.append("如果没问题，说「确认」我就整理成项目规范文件。")
        lines.append("如果有要改的，直接告诉我。")

        return "\n".join(lines)

    # ============================================================
    # 文件草案流程
    # ============================================================

    async def _handle_draft(self, judgment: dict, user_input: str) -> list[Message]:
        target = self._normalize_path(judgment.get("target_file", ""))
        self.current_focus = target
        name = target.split("/")[-1]

        if judgment.get("has_uncertainty") and judgment.get("next_question"):
            self.state_manager.set_draft(target, "")
            return [
                Message("understanding", {"content": judgment.get("reasoning", "")}),
                Message("question", {"content": judgment["next_question"]}),
                Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
            ]

        # 信息足够，生成草案但不直接展示卡片
        draft_content = judgment.get("draft_content", "")
        if not draft_content:
            draft_content = f"# {name}\n\n（模型未生成内容，请补充说明）"

        self.state_manager.set_pending_confirm(target, draft_content)
        self._pending_draft = {"path": target, "content": draft_content}

        summary = judgment.get("understanding_summary", judgment.get("reasoning", ""))
        return [
            Message("understanding", {"content": summary}),
            Message("ai", {"content": f"我已经根据你的描述整理了一份 **{name}** 草案，你想看看吗？"}),
            Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
        ]

    # ============================================================
    # 确认写入 + 主动引导下一步
    # ============================================================

    def _handle_confirm(self, payload: dict) -> list[Message]:
        path = self._normalize_path(payload.get("path", ""))
        if not path:
            return [Message("error", {"content": "缺少文件路径"})]

        self.state_manager.confirm_file(path)
        name = path.split("/")[-1]
        self._pending_draft = None
        return self._build_post_confirm(path, name)

    def _build_post_confirm(self, path: str, name: str) -> list[Message]:
        """构建确认后的消息（写入确认 + 引导下一步）"""
        messages = [
            Message("file_confirmed", {"path": path}),
            Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
        ]

        # 判断哪些文件未完善，引导下一步
        guide = self._suggest_next_step(path)
        if guide:
            messages.append(Message("ai", {"content": guide}))

        return messages

    def _suggest_next_step(self, just_confirmed: str) -> str:
        """根据已确认的文件，推荐下一步"""
        confirmed = set()
        for p, f in self.state_manager.files.items():
            if f.status == FileStatus.CONFIRMED:
                confirmed.add(p)

        name = just_confirmed.split("/")[-1]
        suggestions = []

        if ".shutong/01-vision.md" not in confirmed:
            suggestions.append("完善 01-vision.md（项目愿景，明确目标用户和核心价值）")
        if ".shutong/03-techstack.md" not in confirmed:
            suggestions.append("完善 03-techstack.md（技术栈选择）")
        if ".shutong/05-domain.md" not in confirmed:
            suggestions.append("完善 05-domain.md（领域模型，实体和业务规则）")
        if ".shutong/02-persona.md" not in confirmed:
            suggestions.append("完善 02-persona.md（用户角色和权限）")

        # 如果核心文件已足够，建议生成Spec
        core_files = {".shutong/01-vision.md", ".shutong/03-techstack.md", ".shutong/05-domain.md"}
        if core_files.issubset(confirmed):
            suggestions.append("生成 Spec 文档（核心规范已就绪）")

        if not suggestions:
            return f"✅ **{name}** 已确认写入。\n\n所有核心文件已完善，你可以：\n1. 输入「写个Spec」生成规格文档\n2. 继续描述其他需求完善更多文件\n3. 提出问题，我来解答"

        lines = [f"✅ **{name}** 已确认写入。\n\n接下来我们可以："]
        for i, s in enumerate(suggestions[:4], 1):
            lines.append(f"{i}. {s}")
        lines.append(f"\n你想先做什么？或者继续描述其他需求也行。")
        return "\n".join(lines)

    # ============================================================
    # 修改草案
    # ============================================================

    async def _handle_revise(self, payload: dict) -> list[Message]:
        path = self._normalize_path(payload.get("path", ""))
        feedback = payload.get("feedback", "")
        if not path or not feedback:
            return [Message("error", {"content": "缺少参数"})]

        current_draft = self.state_manager.files.get(path, None)
        current_content = current_draft.draft_content if current_draft else ""

        prompt = (
            f"当前文件草案:\n{current_content}\n\n"
            f"用户修改意见: {feedback}\n\n"
            f"请根据修改意见更新内容，保留未提及的部分。只输出完整Markdown。"
        )
        try:
            new_content = await self.llm.generate("你是文档编辑器。根据意见更新内容。", prompt)
        except Exception:
            new_content = current_content

        self.state_manager.set_pending_confirm(path, new_content)
        name = path.split("/")[-1]
        self._pending_draft = {"path": path, "content": new_content}

        return [
            Message("ai", {"content": f"已根据你的意见更新了 **{name}** 草案，你想看看吗？"}),
            Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
        ]

    # ============================================================
    # Spec生成
    # ============================================================

    async def _handle_spec(self, judgment: dict, user_input: str) -> list[Message]:
        confirmed = self.state_manager.get_confirmed_files()
        if not confirmed:
            return [Message("system", {"content": "还没有已确认的文件，请先完善项目规范。"})]

        context_parts = []
        for path, content in confirmed.items():
            context_parts.append(f"## {path}\n{content}")

        prompt = (
            f"基于以下已确认的项目规范文件，生成Spec文档。\n\n"
            f"{''.join(context_parts)}\n\n"
            f"用户需求: {user_input}\n\n"
            f"请生成Spec，包含：功能概述、验收标准、数据模型、状态机、异常处理。"
            f"输出Markdown含frontmatter。"
        )

        try:
            from core.spec_manager import SPEC_SYSTEM_PROMPT
            spec_content = await self.llm.generate(SPEC_SYSTEM_PROMPT, prompt)
        except Exception:
            spec_content = f"# Spec\n\n{user_input}"

        if not spec_content.startswith("---"):
            round_num = len([f for f in self.state_manager.files if f.startswith(".shutong/specs/round-")]) + 1
            spec_content = (
                f"---\nstatus: DRAFT\nround: {round_num}\n"
                f"created_at: {time.strftime('%Y-%m-%dT%H:%M:%S')}\nlocked_at: null\n---\n\n{spec_content}"
            )

        self.state_manager.set_pending_confirm(".shutong/specs/draft.md", spec_content)
        self._pending_draft = {"path": ".shutong/specs/draft.md", "content": spec_content}

        return [
            Message("ai", {"content": "Spec草案已生成，你想看看吗？"}),
            Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
        ]

    # ============================================================
    # 工具方法
    # ============================================================

    def _handle_init(self) -> list[Message]:
        from core.shutong_init import init_shutong_dir
        created = init_shutong_dir(self.fb)
        self.state_manager = ShutongStateManager(self.fb)
        return [
            Message("system", {"content": "项目已加载", "created_files": created}),
            Message("file_tree", {"files": self.state_manager.get_all_statuses()}),
        ]

    def _normalize_path(self, path: str) -> str:
        if not path.startswith(".shutong/") and not path.startswith("specs/"):
            return f".shutong/{path}"
        return path

    def _build_context(self, user_input: str) -> str:
        parts = []

        confirmed = self.state_manager.get_confirmed_files()
        if confirmed:
            parts.append("【已确认的项目规范】")
            for path, content in confirmed.items():
                parts.append(f"--- {path} ---\n{content[:500]}")
            parts.append("")

        if self.current_focus:
            f = self.state_manager.files.get(self.current_focus)
            if f and f.status == FileStatus.DRAFTING:
                parts.append(f"【当前正在完善】{self.current_focus}\n")

        if self.conversation_history:
            recent = self.conversation_history[-10:]
            parts.append("【最近对话】")
            for msg in recent:
                role = "用户" if msg["role"] == "user" else "AI"
                parts.append(f"{role}: {msg['content'][:200]}")
            parts.append("")

        parts.append(f"【用户最新输入】\n{user_input}")

        return "\n".join(parts)

    def _add_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content, "timestamp": time.time()})
        if len(self.conversation_history) > 30:
            self.conversation_history = self.conversation_history[-30:]
