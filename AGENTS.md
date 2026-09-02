# Agent Instructions

## 仓库定位

本仓库面向前端、Flutter 和跨端开发者，通过唯一项目“需求评审助手”（以需求基线为核心的需求定义、评审与交付工作台）学习 AI 应用开发。第一阶段建立固定 RAG 与需求对象模型、人工批准和交付包的闭环，第二阶段在同一对象模型上演进为 Agent、Tools 与 Multi-Agent 系统。

## 真源与必读

- 长期定位与两个阶段：`docs/strategy.md`。
- 产品规格：`SPEC.md`。
- 系统详细设计：`SDD.md`。
- 工程实现方案：`PLAN.md`。
- 学习、四类文档和代码规则：`docs/learning-guide.md`。
- 唯一阅读顺序：`course/learning-path.md`。
- 完整知识范围：`course/knowledge-map.md`。
- AI Coding 掌握标准：`docs/ai-coding-mastery.md`。
- AI 协作路由：`docs/ai-collaboration.md`。
- 编写或审查 `course/**/*.md`：必须读取 `skills/course-writing/SKILL.md`。
- 制作、审查或重构课程架构图、流程图、机制图及系列技术图：必须读取 `skills/editorial-system-diagrams/SKILL.md`。

评估平台能力时另读 `docs/ai-application-platform.md`；涉及代码编写、审查或掌握判断时读取 `docs/ai-coding-mastery.md`。

## 课程规则

- 课程只有第一阶段、第二阶段和一套全局连续编号，不建立阶段内版本轴。
- 编号与阅读顺序只维护在 `course/learning-path.md`。
- 课程分为概念篇、机制篇、实验篇和项目篇。
- 机制篇讲原理、数据或状态变化和边界；可讲解框架公开能力、核心抽象与关键接口，不逐行导览源码、不讲安装与完整调试（以 `docs/learning-guide.md` 为准）。
- 实验篇位于 `course/labs/`，负责初始化、运行、日志、调试、读码和验证。
- 项目篇引用 `SPEC.md` 与 `SDD.md`，负责综合实践和学习验收，不复制产品规格、详细设计或运行手册。
- 知识地图不排课，知识项、正文和 demo 不强制一一对应。

## 代码规则

```text
source/packages/                  通用能力唯一实现
source/demos/                     机制实验代码
source/apps/review_assistant/     唯一产品
course/                           学习材料
```

- 每个能力域只维护一个 package，demo 和产品通过 import 复用。
- 不为课程编号、文档类型或检查点复制实现。
- demo 只观察机制、做对照和复现确定性失败。
- 不预建空 package、demo、app 或产品目录。
- 产品代码、fixtures、migration、测试、API 和部署全部进入 `source/apps/review_assistant/`。
- 全仓库使用根 `pyproject.toml`、`uv.lock` 和一个 uv 环境。

## 真实调用

- LLM、RAG、Agent 和 Eval 主路径使用真实模型或真实外部服务。
- 缺少 Key、鉴权、限流、超时和能力不支持必须清晰暴露。
- 不静默降级到 fake、Mock、假向量或内存检索。
- Mock 只用于单元测试、离线排查、稳定失败复现或明确对照，不能证明真实质量。

## 边界

- `archive/` 是历史资料，未经用户明确要求不读取、不映射、不重构。
- `other/` 只用于吸收领域边界，不直接搬入完整平台能力。
- 不在长期文档记录迁移过程、实时进度和临时讨论。
- 不为展示复杂度提前引入 Multi-Agent、低代码 Workflow 或企业平台设施。
- 未经用户要求，不创建 Git commit 或 tag。
