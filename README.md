# AI Application Learning Workspace

这是一个面向前端 / Flutter 开发者的 AI 应用开发学习与项目实践仓库。

本仓库的核心目标不是转向纯算法、纯 AI Infra 或纯后端平台方向，而是基于已有前端、跨端客户端和复杂业务交付经验，补齐 LLM、RAG、Agent、FastAPI、评估、观测和前端可视化能力，形成 AI Native 前端与 AI 应用闭环能力。

## 学习方式

当前学习以真实问题和项目闭环为中心：

```text
真实问题
-> 基础原理
-> 最小实现
-> 主流框架实现
-> 失败分析与能力边界
-> 评估观测
-> 小项目实战
-> 项目收敛
```

学习重点不是机械完成每个章节，而是能解释一个 AI 应用为什么这样设计、如何运行、在哪里失败、怎样被评估，以及如何被做成可交付的产品体验。

文档负责沉淀问题、原理、边界和项目入口；代码负责验证关键机制、沉淀可复用 package、完成 demo 和项目闭环。

## 目录结构

```text
.
├── README.md
├── AGENTS.md
├── docs/
├── course/
│   ├── 00_archive/
│   ├── 01_python/
│   ├── 02_llm/
│   ├── 03_rag/
│   ├── 04_agent/
│   ├── 05_eval_observability/
│   ├── 06_ai_native/
│   ├── 07_projects/
│   └── 99_foundation/
└── source/
    ├── 00_archive/
    ├── 01_python/
    ├── 02_llm/
    ├── 03_rag/
    ├── 04_agent/
    ├── 05_eval_observability/
    ├── 06_ai_native/
    ├── 07_projects/
    └── 99_foundation/
```

## 目录职责

- `docs/`：长期有效的战略、学习设计和 AI Agent 协作规范。
- `course/`：课程正文、专题文档、项目规划和阶段性学习内容。
- `source/`：课程配套代码、项目代码、示例、数据集和评估资源。
- `00_archive/`：早期课程式结构归档，不作为当前主线。
- `99_foundation/`：非主线知识补充区，按问题回看。

## 核心文档

- [AGENTS.md](AGENTS.md)：AI Agent 协作规则。
- [docs/strategy.md](docs/strategy.md)：长期定位、背景、目标和方向。
- [docs/learning-guide.md](docs/learning-guide.md)：学习方式、课程设计、项目设计、写作与代码规范。
- [docs/agent-skill.md](docs/agent-skill.md)：AI Agent / Skill 协作指南。

## 说明

`00_archive/` 中保留的早期课程式文档和代码不作为当前主线，后续新内容以 `docs/` 下当前规范为准。
