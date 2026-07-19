# 书童 ShuTong — ShuTong Protocol Verification Demo

> **Version**: V0.1
>
> 书童是书童协议（ShuTong Protocol）的第一个验证实现。不是生产级产品，是协议可行性的证明。
>
> ShuTong is the first verification implementation of the ShuTong Protocol. Not a production product — a proof of protocol feasibility.

---

## 一句话 / TL;DR

**把模型的语义判断能力嵌入代码的功能节点，替代关键词匹配和硬编码规则。**

**Embed LLM semantic understanding into code's decision nodes, replacing keyword matching and hardcoded rules.**

> 书童协议是认知层的人机协作协议，与 CHAP（协作层协议）解决完全不同的问题。
> ShuTong Protocol is a cognitive-layer human-AI collaboration protocol; CHAP is a collaboration-layer protocol. They solve completely different problems.

---

## 为什么做这件事 / Why

AI 系统里到处都是判断节点：用户说"就这样"是想停止还是随口一说？传统方案只有硬编码——关键词列表永远膨胀，规则永远有漏洞。

书童验证了第二种选择：让本地小模型（7B）理解语义，让代码做确定性校验。模型不做规则的事，规则不做模型的事。

AI systems are full of decision nodes: when a user says "that's enough", do they mean stop or just casual talk? The traditional answer is hardcoded keyword lists — they always expand, always have gaps.

ShuTong verifies a second option: let a local small model (7B) understand semantics, let code do deterministic validation. The model doesn't do the rules' job; the rules don't do the model's job.

---

## 协议定位 / Protocol Positioning

### CHAP 已经存在 / CHAP Already Exists

2026 年 5 月，arXiv 发布了 CHAP（Collaborative Human-Agent Protocol）——一个正式的人机协作协议，定义了任务分配、审批、覆盖、升级、交接等协作事件的标准化。CHAP 有完整的规范、参考实现和测试套件。

In May 2026, arXiv published CHAP (Collaborative Human-Agent Protocol) — a formal human-AI collaboration protocol defining task assignment, approval, override, escalation, and handoff. CHAP has a complete specification, reference implementation, and test suite.

### 书童协议与 CHAP 的关系 / Relationship

CHAP 和书童协议解决完全不同的问题：

CHAP and ShuTong Protocol solve completely different problems:

| 维度 | CHAP | 书童协议 |
|------|------|---------|
| **关注点** | 协作层：谁做了什么决定，怎么审计 | 认知层：AI 不确定时怎么办，信息怎么不丢 |
| **核心问题** | 任务生命周期、审批流程、证据链 | 追问机制、上下文编排、记忆域、概率确定 |
| **模型角色** | 不讨论（留给应用层） | **核心主张**：模型应该嵌入判断节点 |
| **追问机制** | "whisper"模式（任务执行中的窄问题） | **认知层基础设施**：追问-校准-确认是核心功能 |

**简单说：CHAP 管"协作流程"，书童协议管"认知对齐"。**

**In short: CHAP manages "collaboration process"; ShuTong Protocol manages "cognitive alignment".**

CHAP 不覆盖认知层，书童协议不覆盖协作层。两者可以在同一个系统中共存，但不存在谁填补谁的关系。书童协议的核心贡献是提出"模型嵌入判断节点"和"概率确定"作为认知对齐的基础设施。

CHAP doesn't cover the cognitive layer; ShuTong Protocol doesn't cover the collaboration layer. They can coexist in the same system. ShuTong Protocol's core contribution is proposing "model-embedded decision nodes" and "probabilistic certainty" as cognitive alignment infrastructure.

书童不是 CHAP 的替代，而是书童协议的第一个验证 Demo。

ShuTong is not a replacement for CHAP — it is the first verification demo of the ShuTong Protocol.

---

## 核心特点 / Key Features

### 1. 意图识别：模型语义判断替代关键词匹配 / Intent Recognition: Model Semantics Replace Keywords

```python
# 传统 / Traditional: keyword list, always expanding, always triggering falsely
STOP_KEYWORDS = ["就这样", "先这样", "够了", "别问了", ...]
if any(kw in user_input for kw in STOP_KEYWORDS):
    stop()

# 书童 / ShuTong: let the local model judge
intent = await _recognize_intent(user_input)  # → "stop" / "continue" / ...
```

| 输入 / Input | 关键词匹配 / Keywords | 模型判断 / Model |
|------|-----------|---------|
| "就这样" | ✅ 触发 | ✅ stop |
| "我不想就这样结束" | ❌ 误触发 | ✅ continue（否定词反转） |
| "赶紧给我出方案别墨迹了" | ❌ 漏掉 | ✅ stop（语义推断） |

### 2. 追问触发：模型暴露不确定性 + 规则引擎校验 / Questioning: Model Exposes Uncertainty + Rule Engine Validates

LLM 生成认知显化（假设清单 + 盲区清单），规则引擎只做文本模式扫描：

The LLM generates cognitive externalization (assumption list + gap list). The rule engine only scans text patterns:

- 有"来源：纯猜测" → 强制追问 / Has "source: pure guess" → force questioning
- 有"是否阻断：是" → 强制追问 / Has "blocking: yes" → force questioning
- 没有假设清单结构 → 强制重新输出 / Missing structure → force re-output

### 3. 信息传递：选择可概率，传递必确定 / Information Transfer: Selection Probabilistic, Transfer Deterministic

- 选择阶段：模型可以概率性地决定选哪条记忆、是否触发追问——这是它的认知自由。
  **概率采样对模型而言就是确定性选择，不需要 confidence score 二次确认。**
- 传递阶段：用户确认的事实必须原文完整注入，零压缩、零失真

Selection phase: the model can probabilistically decide which memory to use, whether to trigger questioning.
Transfer phase: user-confirmed facts must be injected verbatim, zero compression, zero distortion.

---

## 优势与局限 / Strengths & Limitations

### 优势 / Strengths

| 维度 | 说明 |
|------|------|
| 语义理解 / Semantic Understanding | 本地模型能理解"就这样"和"我不想就这样结束"的区别 |
| 零维护 / Zero Maintenance | 不需要维护膨胀的关键词列表 |
| 可审计 / Auditable | 规则引擎只做文本扫描，结果确定性、可解释 |
| 低成本 / Low Cost | 意图识别用本地 7B 模型，不调用云端 API |
| 隐私安全 / Privacy | 意图判断在本地完成，用户数据不出本机 |

### 局限 / Limitations

| 维度 | 说明 |
|------|------|
| 延迟 / Latency | 每次对话 2 次 LLM 调用（意图识别 + 认知显化），响应 2-10 秒 |
| 本地模型能力 / Local Model | 7B 模型对复杂语义的理解不如云端大模型 |
| 不稳定性 / Instability | 模型输出有概率性，同一输入可能返回不同意图 |
| 资源占用 / Resources | 本地模型需要 GPU 显存（约 4-8GB） |

---

## 未来方向 / Roadmap

| 方向 | 说明 |
|------|------|
| 合并调用 | 将意图识别与认知显化合并为单次 LLM 调用，降低延迟 |
| 更小模型 | 用 0.5B-1B 专用意图分类模型替代通用 7B 模型 |
| 上下文编排 | 四层注意力位阶（系统/前置/中置/近因） |
| 记忆域 | 热/温/冷三层记忆，标签精确匹配，梦境整合 |
| 编程 AI 对接 | 产品包驱动 Cursor / Claude 直接产出代码 |

---

## 协议适用性 / Applicability

书童协议是一种人机协作协议，不是特定产品的技术方案。

ShuTong Protocol is a human-AI collaboration protocol, not a product-specific technical solution.

**适用 / Applicable:**
- 需求对齐：在动手之前确保 AI 和用户理解一致
- 知识沉淀：将对话中的确认事实结构化持久化
- 决策审计：每条决策都有来源标注和用户原话对照

**不适用 / Not Applicable:**
- 简单问答（不需要追问确认）
- 实时交互（延迟太高）
- 纯自动化流程（需要人工参与）

---

## 理论基础 / Theoretical Foundation

**1. 概率确定 / Probabilistic Certainty**

不是"选择行为可概率，传递必确定"这么简单的二分。

核心认识论立场：**概率性不是认知的缺陷，是认知的固有属性。**

人脑决策也是概率性的——神经元随机放电，突触权重波动。
你选择喝可乐而不是雪碧时，不会说"我的 confidence 只有 0.73，请你校准一下"。
你的选择就是你当前认知状态的确定性表达。

模型同理。它的概率采样不是"不确定的信号"，而是它在当前权重和上下文下的确定性认知结果。

因此书童协议拒绝置信度：
- 让模型输出 {"intent": "stop", "confidence": 0.85} = 让模型做元认知
- 但模型的 confidence 和实际准确率经常脱钩
- 置信度本身也是概率性输出——用不确定性的不确定性来降低不确定性，这是无限回归

书童协议终止这个回归：
- 模型选择 intent="stop" → 这就是它的判断
- 规则层校验条件 → 确定性执行
- 错了？审计日志记录 → 下次迭代修正 prompt

**不是"因为模型不可靠所以不用置信度"，是"因为概率性本身就是认知的固有属性，所以不需要置信度"。**

选择阶段：模型概率采样——这是它的认知自由。
传递阶段：原文完整注入——一旦选中，零压缩、零失真。

**2. 禁止性描述优于正向描述 / Prohibitive Descriptions Beat Positive Ones**
不说"你要诚实"，说"禁止把猜测当事实"。
Don't say "be honest"; say "prohibit presenting guesses as facts".

**3. 对齐是目的，不是手段 / Alignment Is the Goal, Not the Means**
追问本身就是核心功能，产品包是终极交付物。
Questioning itself is the core feature; the product package is the final deliverable.

详见 / See [PROTOCOL.md](PROTOCOL.md)

---

## 快速开始 / Quick Start

```bash
# 1. 克隆 / Clone
git clone https://github.com/VZIQAQ/shutong.git
cd shutong

# 2. 启动后端 / Start Backend
cd backend
cp .env.example .env
# 编辑 .env，填入 API Key / Edit .env, fill in your API Key
pip install -r requirements.txt
python run.py

# 3. 启动前端 / Start Frontend
cd frontend
cp .env.example .env
npm install
npm run dev

# 4. 访问 / Open
# 浏览器访问 http://localhost:5173

# 5. 测试 / Test
cd backend
pytest tests/ -v
```

75 tests, all passing.

---

## 技术栈 / Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, WebSocket |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| LLM (local) | Ollama + qwen2.5-fixed |
| LLM (cloud) | OpenAI-compatible API |

---

## 项目结构 / Project Structure

```
shutong/
├── PROTOCOL.md                # 协议总览 / Protocol overview
├── docs/
│   ├── protocol/
│   │   ├── probabilistic-determinism.md  # 概率确定 / Probabilistic determinism
│   │   ├── query-mechanism.md            # 追问机制 / Query mechanism
│   │   └── attention-hierarchy.md        # 上下文编排 / Context orchestrator
│   └── ARCHITECTURE.md                   # 架构实现 / Architecture
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI + WebSocket
│   │   └── core/
│   │       ├── session.py          # 对话引擎 / Dialog engine
│   │       ├── rule_engine.py      # 规则引擎 / Rule engine
│   │       ├── llm_client.py       # 双模型客户端 / Dual-model client
│   │       ├── shutong_state.py    # 文件状态机 / File state machine
│   │       ├── file_bridge.py      # 文件桥接 / File bridge
│   │       └── shutong_init.py     # 目录初始化 / Init
│   └── tests/                # 75 个测试 / 75 tests
└── frontend/
    └── src/                  # React + TypeScript
```

---

## 欢迎加入 / Contributing

书童是一个实验性项目，验证"模型判断嵌入代码"这条路是否走得通。

ShuTong is an experimental project verifying whether "embedding model judgment into code" is viable.

如果你对以下方向感兴趣，欢迎提 Issue、PR 或讨论：

If you're interested in the following, welcome to open Issues, PRs, or discussions:

- **协议扩展**：上下文编排器、记忆域、梦境整合
- **意图识别优化**：更小模型、更低延迟、更高准确率
- **新场景验证**：把书童协议应用到需求对齐之外的场景
- **批评与反驳**：如果这个方向有问题，我们想知道

---

## 许可证 / License

Apache-2.0
