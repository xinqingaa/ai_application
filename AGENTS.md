# Agent Instructions

## 仓库定位

这是一个面向前端 / Flutter 开发者的 AI 应用开发学习仓库。

核心目标是建立 AI Native 前端与 AI 应用闭环能力，而不是转向纯 AI 后端、大模型算法或 AI Infra 方向。

## 必读文档

AI Agent 在处理本仓库任务前，优先阅读：

1. [README.md](README.md)
2. [docs/strategy.md](docs/strategy.md)
3. [docs/ai-application-platform.md](docs/ai-application-platform.md)
4. [docs/learning-guide.md](docs/learning-guide.md)
5. [docs/agent-skill.md](docs/agent-skill.md)

## 学习内容组织原则

- 以真实问题和项目闭环组织学习。
- 不要求每个知识点都配一组脚本。
- 代码服务理解和项目交付，而不是服务章节数量。
- RAG、Tool Calling、Agent、Workflow 可以围绕项目需要交叉出现。
- 学习顺序服务项目闭环，而不是服务目录编号。
- 设计 RAG、Agent、Workflow、AI Native 前端和项目时，可以参考 `docs/ai-application-platform.md` 的远期能力地图，但当前阶段以 `docs/strategy.md` 和需求评审 RAG 助手闭环为准。

## 内容规则

- `00_archive` 是之前的学习资料，规则是从`llm`开始都归档进去，全部重写。其中旧`llm`已经学习完毕，`rag`是卡点，资料完整，但是没有学习完成。
- `01_python` 作为已完成的 Python 基础，不主动重构，除非用户明确要求。
- `99_foundation` 作为非主线知识补充区，不前置、不扩展为新的主线课程。
- `02_llm`、`03_rag`、`04_agent`、`05_eval_observability`、`06_ai_native_frontend` 和 `07_projects` 可以围绕当前项目目标继续评估和收敛。
- 后续的课程、项目和代码必须遵循 `docs/learning-guide.md`。
- 后续的课程、项目和代码不应把 AI 应用简化成聊天 UI 或单点 Demo；`docs/ai-application-platform.md` 作为远期平台化方向参考，不作为当前阶段的完整验收标准。
- 课程编排可以继续讨论和演进，不要在未确认前创建过重目录结构。
- 新内容优先围绕需求评审 RAG 助手、AI 应用主链路、RAG、Agent、Workflow、评估观测和 AI Native 工作台展开。

## 文档规则

- 文档先于代码。
- 不写迁移过程、历史过程、过渡状态。
- 不把实时学习进度写进长期文档。
- 不重复维护多个真源。
- 背景、目标和长期定位统一写入 `docs/strategy.md`。
- 学习设计、课程规范、项目规范和代码规范统一写入 `docs/learning-guide.md`。

## 代码规则

- 新代码优先围绕项目闭环组织。
- 可以按 `V0 / V1 / V2` 逐步完善。
- 可以有多个 package，但每个 package 必须有清晰职责。
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
