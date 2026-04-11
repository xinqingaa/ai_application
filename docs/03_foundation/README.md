# 03 Foundation 文档导航

`03_foundation` 是 `02_llm -> 04_rag -> 05_agent` 之间的过渡阶段。

它的目标不是立即产出一个业务产品，而是先把后续工程会反复用到的判断力、抽象边界和最小项目骨架说明写清楚。

本阶段对应的独立项目是：

- `foundation_lab`

计划中的代码目录是：

- `source/03_foundation/foundation_lab/`

## 当前状态

当前阶段以文档为主，还没有正式开始落实 `foundation_lab` 代码。

这意味着：

- 现在的第一入口是文档，不是代码目录
- `04-07` 先承担“编码前置设计”职责
- 后续开始写代码时，应直接按本目录既定结构落地，而不是重新讨论边界

## 第一入口

如果你现在要开始学习 `03_foundation`，第一阅读入口是：

- [README.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/README.md)

如果你现在要判断本阶段整体内容是否完整，第二入口是：

- [outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md)

如果你现在要为未来 `foundation_lab` 编码做准备，编码前置入口是：

- [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
- [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
- [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
- [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

## 文档定位

本目录下文档当前分为三类：

- 总体规划与导航：
  - [outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md)
  - [README.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/README.md)
- 原理理解文档：
  - [01_llm_principles.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/01_llm_principles.md)
  - [02_transformer_attention.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/02_transformer_attention.md)
  - [03_model_lifecycle_and_selection.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/03_model_lifecycle_and_selection.md)
- 编码前置与项目落地文档：
  - [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
  - [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
  - [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
  - [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

## 当前阶段映射

| 文档部分 | 当前角色 | 未来代码承载 | 当前状态 |
|----------|----------|--------------|----------|
| `README.md` | 阶段导航与第一入口 | 后续项目 README 的上位入口 | 已完成 |
| `outline.md` | 阶段大纲与验收总览 | 不直接对应代码 | 已完成 |
| `01-03` | 原理与方案判断 | 为后续 Prompt、Retriever、Tool、Service 边界提供依据 | 已完成 |
| `04-05` | 编码前置设计 | 后续 `foundation_lab/app/*` 与 `scripts/*` | 待按文档落代码 |
| `06-07` | 项目设计与任务拆解 | 后续 `foundation_lab/README.md`、目录骨架与测试路径 | 待按文档落代码 |

## 学习顺序

建议按这个顺序读：

1. [README.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/README.md)
2. [outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md)
3. [01_llm_principles.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/01_llm_principles.md)
4. [02_transformer_attention.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/02_transformer_attention.md)
5. [03_model_lifecycle_and_selection.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/03_model_lifecycle_and_selection.md)
6. [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
7. [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
8. [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
9. [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

如果你现在不准备写代码，最低阅读通过线是：

1. `README`
2. `outline`
3. `01-03`

如果你准备在下一阶段开始落实 `foundation_lab`，则必须继续完成：

1. `04-05`
2. `06-07`

## 当前无代码阶段怎么使用这些文档

建议这样使用：

1. 先用 `01-03` 建立统一判断，不急着写文件。
2. 再用 `04-05` 固定未来代码结构，避免一开始就写散。
3. 最后用 `06-07` 锁定项目边界、目录、顺序和验收标准。
4. 真正开始编码时，直接以 `07` 的 Phase 顺序推进，不再反复修改文档边界。

卡住时优先回看：

1. 判断模型边界时回看 `01-03`
2. 判断抽象和分层时回看 `04-05`
3. 判断项目范围和实施顺序时回看 `06-07`

## 和 02、04、05 的边界

### 和 02_llm 的边界

- `02` 解决“怎么稳定地调用模型”
- `03` 解决“为什么这样组织工程，以及为什么要引入 LangChain 抽象”

### 和 04_rag 的边界

- `03` 只建立 `Document / Retriever` 的抽象认知和项目骨架
- `04` 才真正实现文档处理、向量化、检索链路和 RAG 优化

### 和 05_agent 的边界

- `03` 只建立 `Tool`、`Runnable`、`Service` 的边界认知和最小编排入口
- `05` 才真正实现 Function Calling、LangGraph、Agent 工作流

## 本阶段完成标准

### 理解层

- 能解释 LLM 应用开发者需要理解到什么程度
- 能说明 Prompt、RAG、长上下文、微调的边界
- 能说明为什么 `03` 必须先建立抽象和工程骨架

### 操作层

- 能按既定顺序读完 `01-07`
- 能根据当前目标判断该先回看哪一组文档
- 能用 `07` 中的阶段顺序组织后续实施

### 代码准备层

- 能说明未来 `foundation_lab` 应包含哪些核心文件
- 能说明最小 `Model / Prompt / Parser / Runnable / Retriever / Tool / Service` 会如何落位
- 能说明当前阶段为什么还没有代码但已经具备编码前提

### 映射层

- 能说清 `01-03` 负责原理判断
- 能说清 `04-05` 负责编码前置设计
- 能说清 `06-07` 负责项目设计与任务拆解
- 能说清未来代码目录将落在 `source/03_foundation/foundation_lab/`

一句话总结：

- `03` 不是为了做大项目
- `03` 是为了让你在 `04` 和 `05` 不再“只会跟着写”
