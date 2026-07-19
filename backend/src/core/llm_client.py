"""
模块: llm_client
职责: 双模型LLM调用封装（本地判断 + 云端生成）
创建: 2026-07-18
"""

import json
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger("shutong.llm")


class LLMClient:
    """双模型LLM客户端

    - 本地模型（Ollama）：判断/意图识别/追问生成，快速、免费
    - 云端模型（OpenAI兼容API）：Spec生成/文档输出，质量高、容量大
    """

    def __init__(
        self,
        # 本地模型（Ollama）
        local_url: str = "http://localhost:11452",
        local_model: str = "qwen2.5-fixed",
        # 云端模型（OpenAI兼容API）
        cloud_url: str = "https://token-plan-cn.xiaomimimo.com/v1",
        cloud_model: str = "mimo-v2.5",
        cloud_api_key: str = "",
        timeout: float = 120.0,
    ):
        self.local_url = local_url.rstrip("/")
        self.local_model = local_model
        self.cloud_url = cloud_url.rstrip("/")
        self.cloud_model = cloud_model
        self.cloud_api_key = cloud_api_key or os.getenv("CLOUD_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=timeout)

    # ============================================================
    # 本地模型调用（判断/意图/追问）
    # ============================================================

    async def _call_local(self, system_prompt: str, user_prompt: str) -> str:
        """调用本地Ollama模型"""
        payload = {
            "model": self.local_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 1024,
            },
        }
        resp = await self._client.post(f"{self.local_url}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    # ============================================================
    # 云端模型调用（Spec生成/文档输出）
    # ============================================================

    async def _call_cloud(self, system_prompt: str, user_prompt: str) -> str:
        """调用云端OpenAI兼容API"""
        payload = {
            "model": self.cloud_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        headers = {
            "Authorization": f"Bearer {self.cloud_api_key}",
            "Content-Type": "application/json",
        }
        resp = await self._client.post(
            f"{self.cloud_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ============================================================
    # 公开接口
    # ============================================================

    async def judge(self, system_prompt: str, user_prompt: str) -> str:
        """判断类调用（本地模型）：意图识别、追问生成"""
        logger.debug("[LOCAL] system: %s", system_prompt[:200])
        logger.debug("[LOCAL] user: %s", user_prompt[:200])
        result = await self._call_local(system_prompt, user_prompt)
        logger.debug("[LOCAL] result: %s", result[:200])
        return result

    async def judge_json(self, system_prompt: str, user_prompt: str) -> dict:
        """判断类调用，返回JSON"""
        raw = await self.judge(system_prompt, user_prompt)
        return _parse_json(raw)

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """生成类调用（云端模型）：Spec文档、执行计划"""
        logger.debug("[CLOUD] system: %s", system_prompt[:200])
        logger.debug("[CLOUD] user: %s", user_prompt[:200])
        result = await self._call_cloud(system_prompt, user_prompt)
        logger.debug("[CLOUD] result: %s", result[:200])
        return result

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """生成类调用，返回JSON"""
        raw = await self.generate(system_prompt, user_prompt)
        return _parse_json(raw)

    async def close(self):
        await self._client.aclose()


def _parse_json(raw: str) -> dict:
    """解析LLM返回的JSON，容忍markdown代码块包裹"""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1
        if lines[end].strip() == "```":
            end -= 1
        text = "\n".join(lines[1 : end + 1])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"action": "chat", "reasoning": text, "has_uncertainty": False}
