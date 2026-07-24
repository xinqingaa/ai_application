# Agent Instructions

## 仓库定位

这是一个面向前端、Flutter 和跨端开发者的 AI 应用学习仓库。

唯一主项目是“需求评审助手”：阶段一完成可信 RAG + 单 Agent 产品，阶段二演进为 Workflow + 多 Agent 评审系统。V0–V6 是唯一项目里程碑。

长期目标见 [docs/strategy.md](docs/strategy.md)，学习与工程规则见 [docs/learning-guide.md](docs/learning-guide.md)。

## 处理任务前必读

按任务需要读取：

1. [README.md](README.md)。
2. [docs/strategy.md](docs/strategy.md)。
3. [docs/learning-guide.md](docs/learning-guide.md)。
4. [docs/agent-skill.md](docs/agent-skill.md)。
5. 涉及代码编写、审查或掌握判断时，读取 [docs/ai-coding-mastery.md](docs/ai-coding-mastery.md)。
6. 评估平台能力时，读取 [docs/ai-application-platform.md](docs/ai-application-platform.md)。
7. 编写或重写 `course/**/*.md` 时，读取 [skills/course-writing/SKILL.md](skills/course-writing/SKILL.md)。

## 学习与课程原则

- 用项目版本反推需要学习的知识，不先铺满能力目录。
- 项目反推是课程设计方法，不代表学习者先读完整项目篇；学习者从 `course/README.md` 按概念、机制与小实验正向进入，项目篇负责综合实践和验收。
- V0–V6 是唯一强学习顺序，不建立 M0–M6 或其他平行里程碑。
- LLM、RAG、Agent、Workflow、Eval 和 AI Native 是能力域，不是必须依次毕业的课程。
- 课程正文分为概念篇、机制篇和项目篇。
- “真实问题 → 原理 → 最小实现 → 框架 → 失败边界”是认知方法，不是固定文档模板。
- 概念篇可以没有代码；机制实验和项目版本按真实需要驱动代码。
- 知识清单与文档、demo 不强制一一对应。
- 知识清单不承担项目排课，不使用内部知识编号面向学习者；当前阅读顺序只维护在 `course/README.md`。
- 与当前项目关系较低但重要的知识，可以只进入概念或机制，不进入当前版本验收。

## 文档真源

- 职业定位、唯一目标、两个阶段和 V0–V6：`docs/strategy.md`。
- 学习方式、三类文档、代码组织、运行和真实模型规则：`docs/learning-guide.md`。
- AI Coding 掌握标准：`docs/ai-coding-mastery.md`。
- 企业平台远期能力：`docs/ai-application-platform.md`。
- AI Agent 执行路由：`docs/agent-skill.md`。
- 课程正文和集中知识清单：`course/`。
- 产品运行、测试、API 和部署：`review_assistant/`。

不要在多个文件中重复维护同一完整规则。

## 项目教材与产品真源

```text
course/project/       项目篇教材
review_assistant/     可运行产品真源
```

- 项目目标、必读知识、设计题、失败题和版本验收写入 `course/project/`。
- 产品代码、API、测试、配置、运行和部署写入 `review_assistant/`。
- 通用能力实现写入 `source/packages/`。
- 机制实验和对照写入 `source/demos/`。
- 学习期组合实验可以写入 `source/apps/`，但不能与产品保持平行实现。
- 项目篇引用产品入口，不复制产品 README；产品 README 不复制课程原理。

## 代码规则

- 每个能力域只维护一个 package，位于 `source/packages/`，全仓库 import 复用。
- 不按课程目录、文档类型或项目版本 copy 平行实现。
- package 根目录职责过多时按能力子目录组织。
- demo 只负责机制观察、对照和稳定失败复现；核心逻辑进入 package。
- 不为每篇正文创建 demo 或 package 增量。
- `review_assistant/` 从阶段一开始逐步形成，不等待课程末尾。
- 不预建 `.gitkeep`、空 package、空 demo、空 app 或空产品目录。
- 必须明确入口、配置、运行方式、观察点、失败边界和验收方式。

## 真实模型与外部服务

- LLM、RAG、Agent 和 Eval 主路径默认调用真实模型或真实外部服务。
- 缺少 key、鉴权失败、限流、超时、模型能力不支持和供应商异常必须清晰暴露。
- 不允许静默 fallback 到 fake、mock 或 simulation。
- Mock 仅用于单元测试、离线排查、稳定复现失败路径或明确标注的对照实验。
- Mock 结果不能作为真实模型效果、检索质量或 Agent 决策质量的主要证据。

## Python 与依赖

- 全仓库使用根目录一个 uv 环境。
- Python 依赖只维护在根 `pyproject.toml` 和 `uv.lock`。
- 使用 `uv add`、`uv add --dev`、`uv remove` 和 `uv run`。
- `.venv/` 可删除重建，不提交。
- API key、模型和数据库配置使用 `.env` / `.env.example`，不写入代码。

## Archive 与外部项目

- `archive/` 是历史资料，当前主线不依赖。
- 未经用户明确要求，不主动读取、映射、扩展或重构 `archive/`。
- `other/` 下的 RAGFlow、MaxKB 等材料用于吸收领域边界和演进经验。
- 不将完整多租户、低代码画布、连接器生态、工具市场或企业权限中台直接搬入当前项目。

## 协作方式

- 先收敛目标和版本边界，再设计结构和实现。
- 优先减少重复文档、重复入口和重复代码。
- 不在长期文档记录迁移过程、实时进度和临时讨论。
- 不把远期平台能力变成当前项目验收项。
- 不为展示复杂度提前引入 Multi-Agent。
- 未经用户要求，不主动创建 Git commit 或 tag。
