# Agent Instructions

## 仓库定位

这是一个面向前端 / Flutter 开发者的 AI 应用开发学习仓库。

核心目标是建立 AI Native 前端与 AI 应用闭环能力，而不是转向纯 AI 后端、大模型算法或 AI Infra 方向。

学习方式：通过唯一主项目「**需求评审助手**」（从 RAG 知识助手演进为多 Agent + Workflow 评审系统），以文档 + 代码边学边做，完成完整业务逻辑闭环。详见 [docs/learning-guide.md](docs/learning-guide.md)。

## 必读文档

AI Agent 在处理本仓库任务前，优先阅读：

1. [README.md](README.md)
2. [docs/strategy.md](docs/strategy.md)
3. [docs/ai-application-platform.md](docs/ai-application-platform.md)
4. [docs/learning-guide.md](docs/learning-guide.md)
5. [docs/agent-skill.md](docs/agent-skill.md)
6. [docs/ai-coding-mastery.md](docs/ai-coding-mastery.md)（涉及代码编写或审查时）

编写或重写 `course/**/*.md` 专题正文时，另读 [skills/course-writing/SKILL.md](skills/course-writing/SKILL.md)。

## 学习内容组织原则

- 以唯一主项目和真实问题闭环组织学习，不按章节堆脚本。
- 文档先于代码：文档定义问题、原理、边界、完成标准；代码验证机制并收敛到项目。
- 不要求每个知识点都配一组脚本；代码服务理解和项目交付，而不是服务章节数量。
- RAG、Tool Calling、Agent、Workflow、Eval、AI Native 可以围绕项目需要交叉出现。
- 学习顺序服务主项目闭环，可按项目需要交叉选课节；**能力路线**（`02_llm`–`07_projects`）与**项目版本**（V0–V6）是两条轴，不混为一谈。
- `02_llm` / `03_rag` / `04_agent` 等是教学分层，不是能力割裂。
- 设计 RAG、Agent、Workflow、AI Native 和项目时，可参考 `docs/ai-application-platform.md` 的远期能力地图，以及 `other/` 下 MaxKB、RAGFlow 的设计思路；当前阶段以 `docs/strategy.md` 和需求评审助手闭环为准。
- AI Coding 是预期开发方式；掌握标准以 [docs/ai-coding-mastery.md](docs/ai-coding-mastery.md) 的代码所有权为准，不以谁敲键盘判断学会。

## 与 archive 的关系

- [archive/](archive/) 存放历史课程式代码与文档，与新课程 `02_llm`–`07_projects` **无学习路径关系**。
- 新文档和新代码**默认不依赖** archive；编写时最多偶发参考某个机制或设计思路。
- 旧学习模式（一篇文档 ↔ 一个目录 ↔ 大量脚本）已废弃；新内容围绕 `source/packages`、`source/demos` 与根 `review_assistant/` 组织（详见 learning-guide §6.4）。
- AI Agent 处理新课程或新项目任务时，**不应主动读取、映射或对照** `archive/`，除非用户明确要求。

## 内容规则

- `archive/` 仅作过渡保留，见上一节；不主动扩展或重构。
- `python_base` 作为已完成的 Python 基础，不主动重构，除非用户明确要求。
- `02_llm`、`03_rag`、`04_agent`、`05_eval_observability`、`06_ai_native` 和 `07_projects` 围绕需求评审助手继续评估和收敛。
- 后续的课程、项目和代码必须遵循 [docs/learning-guide.md](docs/learning-guide.md)。
- 后续的课程、项目和代码不应把 AI 应用简化成聊天 UI 或单点 Demo；`docs/ai-application-platform.md` 作为远期平台化方向参考，不作为当前阶段的完整验收标准。
- 课程编排可以继续讨论和演进，不要在未确认前创建过重目录结构。
- **禁止预建占位**：无用户明确指令，不得创建 `.gitkeep`、空 package、空 demo、空 app；目录仅在当节文档 + 代码落地时创建（learning-guide §6.4）。
- **不为一节一 demo**；主战场是 `source/packages/` 增量。`outline.md` 与 `docs/` 规范文档不为对齐目录而频繁改动。
- 新内容优先围绕需求评审助手、AI 应用主链路、RAG、Agent、Workflow、评估观测和 AI Native 工作台展开。

## 文档规则

- 文档先于代码。
- 不写迁移过程、历史过程、过渡状态。
- 不把实时学习进度写进长期文档。
- 不重复维护多个真源。
- 背景、目标和长期定位统一写入 `docs/strategy.md`。
- 学习设计、课程规范、项目规范和代码规范统一写入 `docs/learning-guide.md`。

## 代码规则

- 新代码优先围绕主项目闭环组织。
- 项目按 V0 / V1 / V2 … V6 逐步完善（**项目版本轴**，与课程目录编号无关）。
- 每个能力域只维护**一个** package（位于 `source/packages/`），全仓库 **import 复用**，禁止 copy 平行实现。
- 学习期 app 在 `source/apps/`（当节正文落地时创建）；`07_projects` 起可部署产品在根 `review_assistant/`。
- 可以有多个 package，但每个 package 必须有清晰职责、单一实例。
- 必须明确入口、运行方式、完成标准和能力边界。
- 不为了章节完整性硬造脚本。
- 全仓库默认使用根目录一个 Python 虚拟环境，例如 `.venv/`。
- Python 依赖统一维护在根目录 `requirements.txt`，不在每个 package / demo / app 下维护独立 requirements。
- 新增依赖时必须更新根 `requirements.txt`，并按类别注释说明用途。

## 协作风格

- 先收敛目标，再设计结构，再编写内容。
- 优先减少重复文档和重复入口。
- 对未定事项保持开放，不提前固化过大的课程或项目结构。
- 如果用户提出职业定位、学习方式或项目方向调整，优先更新 `docs/strategy.md` 和 `docs/learning-guide.md`。
