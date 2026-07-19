# 书童架构说明

## 目录结构

```
backend/
├── run.py              # 启动脚本
├── requirements.txt    # Python 依赖
├── src/
│   ├── main.py         # FastAPI + WebSocket 入口
│   └── core/
│       ├── session.py          # 对话引擎主流程
│       ├── rule_engine.py      # 规则引擎（文本模式扫描）
│       ├── llm_client.py       # 双模型 LLM 客户端
│       ├── shutong_state.py    # 文件状态机
│       ├── file_bridge.py      # 文件系统桥接层
│       ├── shutong_init.py     # 目录初始化
│       └── spec_manager.py     # Spec 管理器
└── tests/              # 单元测试

frontend/
├── src/
│   ├── App.tsx         # 主组件
│   ├── hooks/          # WebSocket + 状态管理
│   └── components/     # UI 组件
└── package.json
```

## 核心流程

```
用户输入
  → _recognize_intent()（本地模型语义判断）
  → stop → 强制出预览
  → direct_write → 写入文件
  → show/skip → 展示/跳过草案
  → continue → LLM 认知显化流程
    → rule_engine.check()（规则校验）
    → 追问 / 生成草案 / 确认写入
```

## 双模型架构

- **本地模型**（Ollama）：意图识别、追问生成，快速、免费
- **云端模型**（OpenAI 兼容 API）：Spec 生成、文档输出，质量高
