# 需求评审助手标准学习路径

这份文档是课程阅读顺序的唯一真源。

目录名称、文件排列、知识地图分组和代码模块出现的先后，都不能替代这里规定的顺序。课程设计由项目目标反推知识；学习者按照认知前置正向学习：

```text
项目愿景
→ 概念
→ 机制与真实实验
→ 项目综合实践
→ 失败、修改与验收
```

## 怎样使用这条路径

- 按主线顺序阅读，不按 `concepts/`、`mechanisms/` 的目录顺序遍历。
- 每篇正文只说明知识前置和本文交付；读完后回到本页继续。
- “按需支撑”不是主线门禁，遇到对应产品或运行问题时再进入。
- 尚未有正文的步骤保留在正确位置，但不创建空文档或无效链接。
- package 中已经存在某项能力，不代表当前步骤已经学习，也不代表项目已经启用。

状态说明：

| 状态 | 含义 |
| --- | --- |
| 可学习 | 正文和必要实验已经存在，可以按路径进入 |
| 待编写 | 位置和目标已确定，正文与真实代码一起落地 |
| 等待前置 | 正文已经存在，但必须先完成前面的知识 |
| 按需支撑 | 不阻塞主线，在真实问题出现时进入 |

## V0：建立固定 RAG 评审基线

V0 的学习目标不是先读完整项目规格，而是逐步回答：

> 模型怎样理解需求，外部资料怎样成为可检索证据，应用怎样基于证据生成可校验的评审结果？

### 第一段：模型在应用中负责什么

1. **[LLM 在 AI 应用中的位置与边界](concepts/llm-in-ai-applications.md)** · 可学习
   建立普通程序、LLM、RAG、Agent 和 Workflow 的职责边界。
2. **[模型输入输出契约：Prompt、Schema 与 Context](concepts/model-input-output-contracts.md)** · 可学习
   理解任务、证据和结果为什么必须由应用建立契约。
3. **[Model API、调用生命周期与 Provider 抽象](mechanisms/model-api-and-provider.md)** · 可学习
   运行真实模型，理解统一调用入口、供应商差异和错误边界。

完成这一段后，你应该能解释一次真实模型调用从配置到响应经历了什么，但还没有建立稳定的业务输出。

### 第二段：让模型结果进入程序

4. **[面向应用的 Prompt Engineering](mechanisms/prompt-engineering.md)** · 可学习
   把临时提示词变成可命名、可版本化、可比较的任务协议。
5. **[Structured Output 与应用侧校验](mechanisms/structured-output.md)** · 可学习
   用 Schema、解析和业务校验决定结果能否进入程序。
6. **[Reliability、错误分类与可见降级](mechanisms/reliability-and-errors.md)** · 可学习
   区分可重试、不可重试、结构化失败和显式降级。

完成这一段后，你应该能使用真实模型生成一份结构化风险结果，并解释失败发生在哪一层。此时证据仍然来自固定输入，不要提前把 Context Builder 当成 Retriever。

### 第三段：让外部资料成为可检索证据

7. **RAG 与外部知识的边界** · 待编写
   区分模型已有知识、搜索、数据库查询、固定 RAG 和 Agentic RAG。
8. **文档加载、清洗与来源保留** · 待编写
   把业务资料转换为有来源身份的文档对象。
9. **Chunking、父子块与 Metadata** · 待编写
   理解切分怎样影响召回、引用和后续更新。
10. **Embedding、Vector Store 与相似度** · 待编写
    理解文本怎样进入向量空间，以及索引真正保存什么。
11. **关键词、向量、混合检索与 Retriever 契约** · 待编写
    让同一查询可以比较不同检索策略，并保留候选结果和诊断。
12. **[Context Engineering：输入装配、预算与证据边界](mechanisms/context-engineering.md)** · 等待前置
    Retriever 先产生候选证据，Context Builder 再决定本轮模型真正看到什么。
13. **可信生成、Sources、Citation Candidate 与证据不足** · 待编写
    约束模型只依据候选证据生成，并区分来源候选、真实引用和拒答。

这里刻意把 LLM 与 RAG 交叉起来：Context Engineering 位于 Retriever 之后。机制篇文件平铺在 `mechanisms/`，不按能力域分子目录；阅读顺序只以本路径为准，不要按文件名或目录排列提前进入。

### 第四段：建立可比较基线

14. **[LLM Calling Harness 与最小回归](mechanisms/calling-harness-and-regression.md)** · 等待前置
    先记录直接 LLM 基线，再用相同 Case 比较检索 RAG。
15. **Golden Set 与最小检索、生成评估** · 待编写
    固定问题、期望来源、风险覆盖和证据不足行为。
16. **直接 LLM、关键词 RAG、向量或混合 RAG 对比** · 待编写
    使用同一批样例判断检索是否真正改善结果。

### 第五段：进入综合项目

17. **[V0：固定 RAG 需求评审基线](project/stage-1-single-agent-rag/v0-fixed-rag.md)** · 等待前置
    组合 `llm_core`、后续 `rag_core` 和 `review_assistant/`，完成真实运行、失败复现、需求修改和版本验收。

V0 项目篇不是新一轮基础教学。前面的术语、数据流或实验仍然无法解释时，应回到对应步骤，而不是跳过理解直接照着项目规格写代码。

## V0 的按需支撑

这些内容已经存在，但不组成进入 RAG 的固定链条：

- **[Streaming、事件协议与 Conversation](mechanisms/streaming-and-conversation.md)** · 按需支撑
  当产品需要 SSE、增量渲染、取消或会话历史时进入。必要前置是 Provider。
- **[Token、成本、延迟与缓存边界](mechanisms/cost-latency-and-caching.md)** · 按需支撑
  当 Harness 已有重复调用记录，需要比较预算、延迟或缓存失效时进入。

支撑篇读完后返回当前主线，不把它的目录位置解释成新的课程顺序。

## V1–V6 怎样接入

后续版本继续使用同一循环：

```text
当前版本出现新问题
→ 在本路径中接入必要概念和机制
→ 完成真实实验
→ 进入对应项目篇
→ 失败、修改、评估与验收
```

| 版本 | 进入项目篇前必须补齐的能力 |
| --- | --- |
| V1 可信结构化评审 | Citation 校验、证据充分性、Refusal、补充问题 |
| V2 质量闭环 | Golden Set、RAG Eval、Bad Case、Feedback、版本回归 |
| V3 单 Agent RAG | Tool Schema、Tool Runtime、Agent Loop、Retriever as Tool、停止条件 |
| V4 可控 Workflow | State、Node、Edge、Checkpoint、Interrupt、Resume、Human-in-the-loop、幂等 |
| V5 多 Agent 评审 | 角色契约、共享状态、并行执行、失败隔离、汇总与冲突裁决 |
| V6 产品化 | AI Native 工作台、质量面板、运行观测、部署与作品化 |

对应正文只有在知识、实验和真实实现一起落地时，才链接到本路径中。完整但不规定先后的知识范围见 [知识地图](knowledge-map.md)。
