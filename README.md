# 书童 (ShuTong) — HACP 协议验证 Demo

> 这是《人工智能协作规范》(HACP) 的第一个验证实现。
> 不是生产级产品，是协议可行性的证明。

## 核心验证

书童 V0.2 验证了 HACP 的第一步：**追问机制**。

- ✅ 意图识别：模型语义判断替代关键词匹配
- ✅ 追问触发：模型暴露不确定性 + 规则引擎结构校验
- ✅ 停止信号："就这样" → 强制出预览
- ✅ 确认写入：用户确认的事实原文持久化

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/shutong.git
cd shutong
```

### 2. 启动后端

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API Key
pip install -r requirements.txt
python run.py
```

### 3. 启动前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 4. 访问

打开浏览器访问 http://localhost:5173

## 协议设计

HACP（Human-AI Collaboration Protocol）包含四个组件：

| 组件 | 状态 |
|------|------|
| 追问机制 | ✅ 已验证 |
| 上下文编排器 | 📝 协议设计 |
| 记忆域数据库 | 📝 协议设计 |
| 概率确定 | ⚠️ 部分验证 |

详见 [docs/HACP_PROTOCOL.md](docs/HACP_PROTOCOL.md)

## 测试

```bash
cd backend
pytest src/tests/ -v
```

## 许可证

MIT
