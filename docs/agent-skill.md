# Agent Skill Guide

这份文档用于指导 AI Agent 在本仓库中进行文档整理、课程设计、项目规划和代码生成。

它不是某个具体工具的安装说明，而是本仓库对 AI Agent 协作方式的长期约定。

**文档真源**：学习设计与代码规范以 [learning-guide.md](learning-guide.md) 为准；各课 `outline.md` 已定稿对齐（**暂定**，实施可微调单节）。**能力路线**（`02`–`07` 课程）与**项目版本**（V0–V6）是两条轴，不混为一谈。

## 目的

AI Agent 应帮助用户：

- 收敛学习目标。
- 整理长期文档。
- 设计课程结构。
- 规划项目闭环。
- 生成可运行、可解释、可验证的代码。
- 评审文档和代码是否符合当前学习方式。

## 推荐读取顺序

处理本仓库任务前，优先阅读：

1. [README.md](../README.md)
2. [AGENTS.md](../AGENTS.md)
3. [strategy.md](strategy.md)
4. [ai-application-platform.md](ai-application-platform.md)
5. [learning-guide.md](learning-guide.md)
6. [ai-coding-mastery.md](ai-coding-mastery.md)

编写或重写 `course/**/0N_*.md` 时，另读 [skills/course-writing/SKILL.md](../skills/course-writing/SKILL.md)。

## 工作前确认

开始任务前，先判断当前任务属于哪一类：

- 文档整理
- 课程设计
- 项目规划
- 代码实现
- 代码评审
- 学习路线讨论

不同任务使用不同深度：

- 文档整理优先找唯一真源。
- 课程设计优先确认真实问题和学习边界。
- 项目规划优先确认 V0 最小闭环与**项目版本**边界（非课程编号）。
- 代码实现优先确认入口、运行方式和验证方式。

## 整理文档

整理文档时：

- 找到唯一真源。
- 删除重复表达。
- 保留长期有效内容。
- 不写迁移说明。
- 不记录实时学习进度。
- 不把阶段性想法写进长期规范。

## 设计专题

设计或重写 `course/**/0N_*.md` 时，按下面索引执行；细则不在这里重复，以真源为准。

| 事项 | 真源 |
| --- | --- |
| 原则与正文模板 | [learning-guide.md §6–§7](learning-guide.md#6-课程正文写作标准) |
| 写前读、写后自检、禁止项 | [skills/course-writing/SKILL.md](../skills/course-writing/SKILL.md)（**必读**） |
| 新概念首篇（`00`） | learning-guide §6.1：是什么、输入输出、与相近概念区别、在项目中的位置 |
| 真实问题三层 | learning-guide §6.2：学习者 / 产品 / 工程 |
| 厚度与双层验收 | learning-guide §6.3：认知链路 + 交付链路；场景叙事、自检题、机制 prose |
| 一节一交付与 Demo | learning-guide §6.4：packages 主线；Demo 按决策树，非每节必建 |
| 正文链接 | learning-guide §6.5：仅同课上下节、当节 `source/`；少链未学课程 |
| 代码片段与概念示意 | learning-guide §6.6：默认内嵌真实片段；例外须标注「概念示意，不进入项目」 |

**正文两层结构**（learning-guide §7）：

```text
A. 认知链路：真实问题 → 基础原理 → 最小实现 → 主流框架实现 → 失败分析与能力边界
B. 交付链路：本节实战 → 完成标准 → 本节沉淀 → 相关专题（可选）
```

两层缺一不可。若正文像 outline 条目扩写、缺少机制讲解与反例，应加厚解释层（见 course-writing skill 写后自检），而不是继续堆表格或跨课链接。

**默认任务粒度**：一次只完成**一个专题** = 一篇 `course/.../*.md` + 对应 `source/` 变更 + 完成标准可勾选。不要批量写多节文档而不写代码。

**00 节**：在 `source/packages/` 创建或扩展 `*_core` + `source/demos/{课号}_*` demo；见 learning-guide §6.4「00 代码上限」。

**01 起**：「本节实战」必须写真实文件路径、命令与预期输出。

不要从工具名或框架名直接开始。课程正文不是 outline 的扩写，也不是项目架构设计笔记。

### 每节交付与 Git

完成当节文档 + 代码 + 完成标准后，可建议用户提交：

```text
course(02_llm/00): LLM 问题空间与 first_chat demo
```

Agent 在用户未要求时**不要主动 commit**。阶段 tag（如 `course/02_llm`）仅用户明确下令时执行，不要每节打 tag。

## 设计项目

设计项目时：

- 先写 V0 最小闭环。
- 再写 V1 能力增强。
- 最后写 V2 产品化完善。
- 不提前做大而全平台。
- 不把 RAG、Agent、Workflow、前端工作台割裂成互不相关的孤岛。
- 可以参考 [ai-application-platform.md](ai-application-platform.md) 判断项目能力未来可能属于知识库、智能体、工作流、工具生态、评测、安全运营还是平台前端；当前阶段以 [strategy.md](strategy.md) 中的需求评审助手闭环为准。
- 不把 AI 应用简化成聊天 UI、文件问答、工具调用 Demo 或普通后台管理页面。

## 企业级 AI 应用平台视角

AI Agent 在本仓库中设计课程、项目和代码时，必须记住：

- 企业级 AI 应用不是聊天机器人，而是围绕模型、知识库、工作流、智能体、工具生态、评测、安全和运营的应用平台。
- 前端不是普通展示层，而是 AI 应用平台的操作界面和控制台。
- RAG 不只是文件上传和问答，还包括知识库创建、文档分类、解析进度、切片管理、权限隔离、检索测试、引用溯源、版本治理和知识回流。
- Agent 不只是工具调用 Demo，还包括智能体创建、模型配置、Prompt 管理、知识库绑定、工具授权、参数设置、版本发布和运行记录。
- Workflow 不只是画节点，还包括节点校验、连线规则、版本管理、流程发布、运行调试、执行日志、失败节点重试和人工介入。
- MCP 和工具生态不只是后端连接，还需要前端配置、连接测试、权限控制、调用记录、异常状态、高风险确认和操作审计。
- Agent 运行过程可视化不是装饰，而是企业用户理解任务状态、工具调用、失败原因、耗时、成本和重试机制的核心入口。
- 数据标注、模型评测、bad case 回流、安全、审计、Token 成本和运营监控是企业级 AI 应用的一部分，不是后期可有可无的附加项。

详细能力地图以 [ai-application-platform.md](ai-application-platform.md) 为唯一真源。不要在多个文档中重复维护完整模块清单。

## 编写代码

编写代码时：

- **与当节文档同步**：一次只实现当前专题对应的 `source/` 变更；写完代码后正文引用真实入口，不用伪代码占位。
- 每门课 **00** 仅建 package 壳 + 第一个 demo（见 learning-guide §6.4「00 代码上限」）；**01 起**在同一包上增量实现。
- **单包 import**：每个 `*_core` 位于 `source/packages/`，全仓库唯一实例；禁止 copy 平行包。
- 学习期 app 在 `source/apps/`（当节正文落地时创建）；根 `review_assistant/` 为 `07_projects` 产品真源。
- **禁止预建占位**（`.gitkeep`、空目录）：见 learning-guide §6.4；无用户明确指令不得创建。
- `03_rag` 等以最小实现跑通；`06_ai_native` 在同一包上加深工程整合。
- 优先围绕主项目能力组织，不为了章节完整性造脚本。
- 保证可运行、可验证、可解释；README 写清命令与预期输出。
- 帮助用户理解代码为什么这样设计，而不是只交付 AI 生成结果。
- 说明关键代码的修改点、调试路径和验证方式。
- 对真实 API、模型、密钥和外部服务提供清晰配置边界。
- 对 RAG 和 Agent 相关代码保留必要的调试信息（在对应章节再展开）。

## Python 与依赖管理规范

全仓库默认使用一个 Python 虚拟环境和一个根依赖清单。

要求：

- 虚拟环境建议放在根目录 `.venv/`。
- Python 依赖统一维护在根目录 `requirements.txt`。
- 不在每个 package / demo / app 下维护独立 `requirements.txt`。
- 新增依赖时必须更新根目录 `requirements.txt`。
- `requirements.txt` 必须用注释分组，说明依赖用途。
- 每个 package / demo 的 README 只说明运行入口、配置方式和验证方式，不重复维护依赖清单。
- 如果某个依赖只是可选能力，先在 `requirements.txt` 中用注释标注 optional 或说明用途。
- 涉及 API key、模型配置、数据库连接等，使用 `.env` / `.env.example`，不要写入代码。

根依赖清单的推荐分组：

```text
# Core API
# HTTP / Async
# LLM Clients
# LangChain / Agent
# RAG / Vector Store
# Database / Cache
# Document Processing
# Evaluation / Testing
# Dev Tools
```

## 禁止行为

- 把旧版章节脚本模式扩散到新内容。
- **批量写多节课程文档而不写当节代码**。
- 把课程正文写成 outline 的简短扩写或架构设计笔记。
- 在 00/01 等早期专题写独立章节「评估观测」「项目收敛」或全课 capability 矩阵（应合并为运行与观察、本节沉淀）。
- 在正文中大量链接未学课程、`07_projects` 子专题或多个 outline。
- 在新概念入口篇默认读者已经理解该概念。
- 只写系统设计问题，不解释学习者真实问题。
- 用伪代码或设计草图替代当节真实 `source/` 入口（概念示意例外见上文）。
- 在 00 预建后续节模块或完整基础设施（见 learning-guide §6.4）。
- 在 `source/0x_*` 按课程编号镜像建 package（应使用 `source/packages/`）。
- 在长期文档里记录实时学习进度。
- 编写大量历史迁移说明。
- 过早引入复杂 Agent 平台。
- 为了显得完整而堆砌框架和目录。
- 把个人项目包装成公司真实项目。
- 为每个小 package 单独维护依赖文件，导致依赖分散不可查。
- **copy 或平行维护多个同名 package**（如两份 `llm_core`）；必须 import 单实例。
- 未经用户要求主动创建 Git commit。

## 输出偏好

AI Agent 的输出应该：

- 先给结论。
- 再给结构。
- 最后给必要细节。
- 保持文档能长期维护。
- 帮助用户减少认知负担，而不是增加入口和概念数量。
