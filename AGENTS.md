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
- 设计 RAG、Agent、Workflow、AI Native 前端和项目时，必须参考 `docs/ai-application-platform.md` 的企业级 AI 应用平台能力地图。

## 新内容规则

- 已有 `01_python`、`02_llm`、`03_foundation`、`04_rag` 内容不主动重构，除非用户明确要求。
- 后续新课程、新项目和新代码必须遵循 `docs/learning-guide.md`。
- 后续新课程、新项目和新代码必须符合 `docs/ai-application-platform.md` 中的平台能力地图，不把 AI 应用简化成聊天 UI 或单点 Demo。
- 课程编排可以继续讨论和演进，不要在未确认前创建过重目录结构。
- 新内容优先围绕 AI 应用主链路、RAG 项目、Agent 项目、Workflow 项目和前端工作台展开。

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
