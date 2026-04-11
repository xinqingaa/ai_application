# 03 Foundation 文档导航

`03_foundation` 是 `02_llm -> 04_rag -> 05_agent` 之间的过渡阶段。

它的目标不是立即产出一个业务产品，而是先把后续工程会反复用到的判断力、抽象边界和最小项目骨架说明写清楚。

这一阶段必须坚持一个原则：

- 文档是核心
- 代码是文档设计的落实结果

也就是说，`03` 不是“先写代码，再补说明”，而是：

- 先把原理、边界、流程、实施顺序写清楚
- 再让代码按文档约束逐步落地

本阶段对应的独立项目是：

- `foundation_lab`

计划中的代码目录是：

- `source/03_foundation/foundation_lab/`

## 当前状态

当前阶段仍然以文档为主，但 `foundation_lab` 已经完成 `Phase 1` 空骨架落地。

这意味着：

- 文档仍然是第一约束，不因为已经有代码骨架而退位
- `04-07` 不再只是“编码前置设计”，同时已经开始承担“代码实施约束”职责
- `source/03_foundation/foundation_lab/` 已存在，但当前实现只到 `Phase 1`
- 后续 `Phase 2-6` 应继续按既定文档推进，而不是边写边重新设计结构

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

如果你现在要查看已经落下的项目骨架，第一代码入口是：

- [source/03_foundation/README.md](/Users/linruiqiang/work/ai_application/source/03_foundation/README.md)
- [foundation_lab/README.md](/Users/linruiqiang/work/ai_application/source/03_foundation/foundation_lab/README.md)
- [qa_service.py](/Users/linruiqiang/work/ai_application/source/03_foundation/foundation_lab/app/services/qa_service.py)
- [qa_chain.py](/Users/linruiqiang/work/ai_application/source/03_foundation/foundation_lab/app/chains/qa_chain.py)

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

## 文档优先级

从现在开始，`03_foundation` 里的文档可以再明确分成两层：

### 第一层：稳定规范文档

这些文档的角色是：

- 固定原理
- 固定边界
- 固定结构
- 固定实施顺序

正常情况下不应因为某个小实现细节就频繁改写：

- [README.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/README.md)
- [01_llm_principles.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/01_llm_principles.md)
- [02_transformer_attention.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/02_transformer_attention.md)
- [03_model_lifecycle_and_selection.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/03_model_lifecycle_and_selection.md)
- [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
- [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
- [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
- [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

只有在以下情况出现时，才需要回头修改这些文档：

1. 实际代码落地和当前设计不一致
2. 当前文档没有覆盖新的关键边界
3. 某个 Phase 的完成标准已经不足以判断是否完成

### 第二层：持续更新的实施文档

这些文档的角色是：

- 反映当前代码已经做到哪里
- 给出实际运行入口
- 给出实际命令、示例和当前限制

它们应随着 `Phase 2-6` 持续补充：

- [source/03_foundation/README.md](/Users/linruiqiang/work/ai_application/source/03_foundation/README.md)
- [foundation_lab/README.md](/Users/linruiqiang/work/ai_application/source/03_foundation/foundation_lab/README.md)

一句话说：

- `docs/03_foundation/*.md` 负责“约束代码应该长成什么样”
- `source/03_foundation/**/*.md` 负责“说明当前代码已经长成什么样”

## 当前阶段映射

| 文档部分 | 当前角色 | 未来代码承载 | 当前状态 |
|----------|----------|--------------|----------|
| `README.md` | 阶段导航与第一入口 | 后续项目 README 的上位入口 | 已完成并进入代码阶段总导航 |
| `outline.md` | 阶段大纲与验收总览 | 不直接对应代码 | 已完成 |
| `01-03` | 原理与方案判断 | 为后续 Prompt、Retriever、Tool、Service 边界提供依据 | 已完成 |
| `04-05` | 抽象与工程主规范 | `foundation_lab/app/*` 与 `scripts/*` | 已开始按文档落地 |
| `06-07` | 项目设计与任务拆解 | `foundation_lab/README.md`、目录骨架与测试路径 | 已进入按 Phase 推进阶段 |

## 当前实施进度

当前代码实施进度应明确记录为：

- `Phase 1` 已完成：目录骨架、主要模块文件、脚本入口、测试骨架、项目 README 已建立
- `Phase 2-6` 未完成：真实 native 调用、LangChain 等价实现、retriever/tool 强化、service 完整编排、API 收口仍需继续补齐

这意味着当前阶段的关系是：

- 文档侧：主规范已经基本稳定
- 代码侧：刚进入按文档实施的起点

所以现在最不应该做的事是：

- 因为已经有代码骨架，就反过来让代码定义文档

正确顺序仍然是：

- 先以 `04-07` 约束实现
- 再在 `source/03_foundation` 下更新“当前实际做到哪里”

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

## 当前有骨架、未完成阶段怎么使用这些文档

建议这样使用：

1. 先用 `01-03` 建立统一判断，不急着写文件。
2. 再用 `04-05` 固定代码结构、请求流和职责边界，避免实现时写散。
3. 再用 `06-07` 锁定项目边界、目录、顺序、主流程和验收标准。
4. 真正推进代码时，直接按 `07` 的 Phase 顺序执行。
5. 每推进一个 Phase，优先更新 `source/03_foundation/foundation_lab/README.md`，而不是先改主规范文档。
6. 只有当实现和设计发生偏差时，才回头修订 `05-07`。

卡住时优先回看：

1. 判断模型边界时回看 `01-03`
2. 判断抽象和分层时回看 `04-05`
3. 判断项目范围和实施顺序时回看 `06-07`

## 后续到 Phase 6 时，文档应该怎么补

后续继续写到 `Phase 6` 时，文档补充应遵循这个原则：

### 必须持续补的

- [source/03_foundation/README.md](/Users/linruiqiang/work/ai_application/source/03_foundation/README.md)
- [foundation_lab/README.md](/Users/linruiqiang/work/ai_application/source/03_foundation/foundation_lab/README.md)

这两份要持续反映：

- 当前已经实现到哪个 Phase
- 当前能运行哪些脚本或接口
- 当前有哪些已验证能力
- 当前还有哪些边界和未完成项

### 不应频繁重写的

- [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
- [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
- [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

这三份后续只在以下情况下修改：

1. 代码已经证明原设计不够准确
2. 需要补新的关键流程说明
3. 需要修正 Phase 完成标准

所以到 `Phase 6` 时，正确做法不是每个阶段都大改主文档，而是：

- 主文档保持稳定
- 项目 README 持续更新
- 真有设计偏差时再回改 `05-07`

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
