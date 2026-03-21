# AI应用开发学习规划 (前端转型版)

## 背景

### 优势和不足

- 前端/Flutter开发者，具备丰富的 Web 前端、跨端开发和工程化经验
- 当前目标：转向 AI 应用开发，重点不是算法研究，而是构建可落地的 AI 产品
- 优势

- 产品与交互设计思维强
- 工程化能力成熟
- 跨端开发经验丰富

- 短板

- Python经验不足
- 对模型边界理解不足
- RAG / Agent 工程经验不足

### 当前目标

- 掌握 Python 作为 AI 应用开发语言
- 掌握 LLM API 调用与 Prompt 设计
- 掌握 RAG（检索增强生成）基础能力
- 掌握 Agent / Workflow 基础能力
- 能完成前后端结合的 AI 应用开发
- 能实现可观测、可调试、可复用的 AI 应用工程

## 前端思维转变和理解

### 过去关注点

- 页面 / 组件 / 状态 / 接口 / 工程化
- 用户交互和性能优化
- 可视化布局和跨端适配

### AI应用新增关注点

- 模型能力边界与输出概率性
- Prompt设计
- 输出结构化与上下文管理
- 知识注入（RAG）
- 工具调用（Function/Tools）
- 任务编排（Agent）
- 评测与观测（Evaluation & Observability）

### 核心迁移思维

| 大前端经验   | AI应用开发对应能力 |
| ------------ | ------------------ |
| API调用      | 模型调用 (LLM API) |
| 状态管理     | 上下文 / 会话管理  |
| 搜索/列表    | RAG 检索与重排     |
| 自动化流程   | Agent / 工作流     |
| 组件复用     | Prompt模板复用     |
| 异步数据处理 | 异步调用模型与工具 |

## Python学习定位

### 学习目标

- 快速构建 AI 应用后端与工作流
- 不追求算法工程师深度

### 重点掌握

- 基础语法
- 函数与类
- 异步 (async/await)
- 文件与 JSON 处理
- HTTP请求 (requests / httpx)
- FastAPI
- 日志与异常处理
- 虚拟环境与依赖管理

### 暂不优先

- 复杂数据结构算法
- 深度底层解释器原理
- 纯算法刷题

## AI应用开发核心技术栈优先级

### P0（必须掌握）

- Python
- LLM API 调用 (OpenAI / Anthropic / Claude / Gemini)
- Prompt Engineering
- FastAPI / Flask 基础
- JSON / HTTP 数据交互

### P1（项目实践阶段掌握）

- RAG 基础：文档切分、Embedding、向量数据库
- LangChain / LangGraph
- Agent基础
- 会话记忆管理
- Function Calling / Tool Calling
- 输出校验与容错

### P2（复杂产品阶段）

- 多Agent协作
- 模型路由与多模型调用
- 重排/混合检索
- Guardrails
- 在线评测与观测
- 私有化部署

## 项目驱动学习路线

### 项目1：AI聊天助手

- 目标：学会模型API调用、多轮会话、Prompt拼接
- 技术：Python、FastAPI、LLM API、Prompt模板
- 输出：简易聊天Demo

### 项目2：文档问答RAG

- 目标：学会文档切分、Embedding、向量数据库、检索增强生成
- 技术：Python、LangChain、Vector DB、Prompt
- 输出：可查询PDF/文档的问答助手

### 项目3：工具调用型Agent

- 目标：学会Function Calling、工具注册、多步骤任务执行
- 技术：LangChain/Agent、LLM API、Python工具函数
- 输出：能执行多步任务的智能Agent Demo

### 项目4：完整AI应用

- 目标：前端/Flutter + Python后端 + 模型 + RAG + Agent
- 技术：React/Vue/Flutter + FastAPI + LLM API + LangChain/Agent
- 输出：完整可演示、可部署、可复用产品

## 阶段学习计划

### 阶段1：Python + LLM API

- 内容：Python基础、API调用、环境管理、多轮聊天

### 阶段2：Prompt + Structured Output

- 内容：Prompt模板、few-shot、JSON输出、校验、重试

### 阶段3：RAG

- 内容：文档切分、Embedding、向量数据库、检索增强、上下文拼接、rerank基础

### 阶段4：Agent / Workflow

- 内容：Function Calling、工具调用、多步骤任务、状态流转、工作流编排

### 阶段5：完整应用落地

- 内容：前端/Flutter结合Python后端、SSE/流式输出、文件上传、知识库管理、部署与监控

## 项目与文档结构

### 项目实施原则

- 配置与密钥分离
- Prompt模板化
- 输出结构化
- 错误兜底与重试机制
- 日志记录
- 可观测性
- 数据集与评测集分离
- 开发/测试/生产环境区分
- 低成本迭代

### 项目目录

```plain
/ (根目录)
├── docs/                   # 文档集合
│   ├── 01_python/          # Python学习文档
│   ├── 02_llm/             # LLM学习文档
│   ├── 03_rag/             # RAG学习文档
│   ├── 04_agent/           # Agent学习文档
│   ├── 05_application/     # 完整应用落地文档
├── source/                 # 学习资源集合
│   ├── 01_python/          # Python学习资源
│   ├── 02_llm/             # LLM学习资源
│   ├── 03_rag/             # RAG学习资源
│   ├── 04_agent/           # Agent学习资源
│   ├── 05_application/     # 完整应用落地资源
```

### 目录说明

- docs/: 存放学习过程中的文档，随着每个阶段的学习，文档内容将逐步丰富。

- 每个学习阶段对应一个子目录（如 `/docs/01_python`、`/docs/02_llm` 等），用于记录详细的学习笔记、示例代码、最佳实践和知识点总结。

- source/: 存放学习资源的集合。

- 每个学习阶段的资源，如教程、项目代码、参考资料等，将存放在对应的子目录下。

### 总结：

- **项目与文档结构**：已经明确了**文档目录**和**资源目录**的结构，其中每个学习阶段（如 Python、LLM、RAG、Agent）都对应一个子目录。
- **学习阶段与文档对应**：每个阶段的学习内容和实践会对应到 `docs/` 和 `source/` 目录下，形成结构化的学习路径。