# AI Application Learning Workspace

这是一个面向前端 / Flutter 开发者的 AI 应用开发学习与项目实践仓库。

本仓库的核心目标不是转向纯算法、纯 AI Infra 或纯后端平台方向，而是基于已有前端、跨端客户端和复杂业务交付经验，补齐 LLM、RAG、Agent、FastAPI、评估、观测和前端可视化能力，形成 AI Native 前端与 AI 应用闭环能力。

## 学习方式

当前学习以真实问题和项目闭环为中心。**学习认知链路**与**单节交付约定**以 [docs/learning-guide.md](docs/learning-guide.md) 为准：

```text
A. 学习认知链路
真实问题
-> 基础原理
-> 最小实现
-> 主流框架实现
-> 失败分析与能力边界

B. 单节交付约定
-> 本节实战（文档 + 代码）
-> 完成标准（含运行与观察）
-> 本节沉淀
```

**两条轴**：`02_llm`–`07_projects` 是**能力路线**（学什么）；需求评审助手 **V0–V6** 是**项目版本**（产品演进到哪），二者相关但不一一对应。

学习重点不是机械完成每个章节，而是能解释一个 AI 应用为什么这样设计、如何运行、在哪里失败、怎样被评估，以及如何被做成可交付的产品体验。

文档负责沉淀问题、原理、边界和完成标准；代码通过 **import 复用 `source/packages/`**、逐节增量完善；`07_projects` 在根目录 [review_assistant/](review_assistant/) 作品化。

## 目录结构

```text
.
├── README.md
├── AGENTS.md
├── archive/              # 历史课程代码与文档（主线不依赖）
├── docs/
├── course/
│   ├── python_base/
│   ├── 02_llm/
│   ├── 03_rag/
│   ├── 04_agent/
│   ├── 05_eval_observability/
│   ├── 06_ai_native/
│   └── 07_projects/
├── review_assistant/       # 07 起完整可部署产品
├── source/                 # 见 source/README.md（当前实物清单）
│   ├── packages/
│   ├── demos/
│   └── python_base/
└── requirements.txt
```

## 目录职责

- `docs/`：长期有效的战略、学习设计和 AI Agent 协作规范。
- `course/`：课程正文、专题文档、项目规划和阶段性学习内容。
- `source/`：扁平化的共享 package、demo 与 Python 基础练习（规范见 learning-guide §6.4）。
- `review_assistant/`：`07_projects` 起的可部署产品与作品化入口。
- `archive/`：历史课程式资料归档，不作为当前主线。

## 核心文档

- [AGENTS.md](AGENTS.md)：AI Agent 协作规则。
- [docs/strategy.md](docs/strategy.md)：长期定位、背景、目标和方向。
- [docs/learning-guide.md](docs/learning-guide.md)：学习方式、课程设计、项目设计、写作与代码规范。
- [docs/agent-skill.md](docs/agent-skill.md)：AI Agent / Skill 协作指南。

## 说明

历史课程式文档和代码在 `archive/`，不作为当前主线；新内容以 `docs/` 下当前规范为准。
