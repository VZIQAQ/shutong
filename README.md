# 书童 ShuTong — HACP 协议验证 Demo

> **Version**: V0.1
>
> 书童是《人工智能协作规范》(HACP) 的第一个验证实现。
> 不是生产级产品，是协议可行性的证明。
>
> ShuTong is the first verification implementation of the Human-AI Collaboration Protocol (HACP).
> Not a production product — a proof of protocol feasibility.

---

## 核心验证 / What It Verifies

书童 V0.1 验证了 HACP 的第一步：**追问机制**。

ShuTong V0.1 verifies the first step of HACP: the **questioning mechanism**.

- ✅ 意图识别：模型语义判断替代关键词匹配 / Intent recognition: model semantics replace keyword matching
- ✅ 追问触发：模型暴露不确定性 + 规则引擎结构校验 / Questioning: model exposes uncertainty + rule engine validates structure
- ✅ 停止信号："就这样" → 强制出预览 / Stop signal: "就这样" → force preview
- ✅ 确认写入：用户确认的事实原文持久化 / Confirmation: user-confirmed facts persisted verbatim

## 快速开始 / Quick Start

### 1. 克隆仓库 / Clone

```bash
git clone https://github.com/yourusername/shutong.git
cd shutong
```

### 2. 启动后端 / Start Backend

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API Key
pip install -r requirements.txt
python run.py
```

### 3. 启动前端 / Start Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 4. 访问 / Open

浏览器访问 http://localhost:5173

## 协议设计 / Protocol Design

HACP（Human-AI Collaboration Protocol）包含四个组件 / contains four components:

| 组件 / Component | 状态 / Status |
|------|------|
| 追问机制 / Questioning Mechanism | ✅ 已验证 / Verified |
| 上下文编排器 / Context Orchestrator | 📝 协议设计 / Designed |
| 记忆域数据库 / Memory Domain | 📝 协议设计 / Designed |
| 概率确定 / Probabilistic Certainty | ⚠️ 部分验证 / Partial |

详见 / See [docs/HACP_PROTOCOL.md](docs/HACP_PROTOCOL.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 测试 / Tests

```bash
cd backend
pytest src/tests/ -v
```

75 tests, all passing.

## 技术栈 / Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, WebSocket |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| LLM (local) | Ollama + qwen2.5-fixed |
| LLM (cloud) | OpenAI-compatible API |

## 许可证 / License

MIT
