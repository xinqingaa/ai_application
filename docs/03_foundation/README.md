# 03 Foundation 文档导航

`03_foundation` 是 `02_llm -> 04_rag -> 05_agent` 之间的过渡阶段。

它的目标不是产出一个业务产品，而是完成两件事：

- 建立应用开发者视角下的 LLM 原理判断力
- 建立 LangChain 核心抽象与最小工程骨架认知

本阶段对应的独立项目是：

- `foundation_lab`

代码目录建议放在：

- `source/03_foundation/foundation_lab/`

## 文档定位

本目录下文档分为两类：

- 总体规划与执行：
  - [outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md)
  - [implementation.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/implementation.md)
- 原理理解文档：
  - [01_llm_principles.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/01_llm_principles.md)
  - [02_transformer_attention.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/02_transformer_attention.md)
  - [03_model_lifecycle_and_selection.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/03_model_lifecycle_and_selection.md)
- 本轮优先落地文档：
  - [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
  - [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
  - [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
  - [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

## 代码边界说明

`03_foundation` 的代码实践不是从 `01` 开始，而是从：

- [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)

开始真正进入。

具体边界是：

- `01-03`：原理理解、方案判断、模型认知边界
- `04-05`：LangChain 抽象与工程化基础，开始真正写代码
- `06-07`：`foundation_lab` 设计与任务拆解，进入项目落地

所以如果你的目标是启动 `foundation_lab`，真正的编码起点应该是：

- `04_langchain_core_abstractions.md`

## 阅读顺序

建议按这个顺序读：

1. `outline.md`
2. `README.md`
3. `01_llm_principles.md`
4. `02_transformer_attention.md`
5. `03_model_lifecycle_and_selection.md`
6. `04_langchain_core_abstractions.md`
7. `05_langchain_engineering.md`
8. `06_foundation_lab_design.md`
9. `07_foundation_lab_tasks.md`
10. `implementation.md`

## 和 02、04、05 的边界

### 和 02_llm 的边界

- `02` 解决“怎么稳定地调用模型”
- `03` 解决“为什么这样组织工程，以及为什么要引入 LangChain 抽象”

### 和 04_rag 的边界

- `03` 只建立 `Document / Retriever` 的抽象认知
- `04` 才真正实现文档处理、向量化、检索链路和 RAG 优化

### 和 05_agent 的边界

- `03` 只建立 `Tool`、`Runnable`、`Service` 的边界认知
- `05` 才真正实现 Function Calling、LangGraph、Agent 工作流

## 本阶段完成标准

- 能解释 LLM 应用开发者需要理解到什么程度
- 能说明 Prompt、RAG、长上下文、微调的边界
- 能理解并写出最小 `Model / Prompt / Parser / Runnable / Retriever / Tool`
- 能完成 `foundation_lab` 的最小工程骨架

一句话总结：

- `03` 不是为了做大项目
- `03` 是为了让你在 `04` 和 `05` 不再“只会跟着写”
