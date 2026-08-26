# 需求评审助手标准学习路径

本文是课程阅读顺序和课程序号的唯一真源。课程只有第一阶段、第二阶段和一套从 1 到 78 的连续编号。

一节课代表一个核心学习问题，可以同时包含概念或机制正文与配套实验篇。知识地图、目录、文件名和工程 `PLAN.md` 都不规定阅读顺序。

## 怎样学习一节课

```text
概念篇建立问题和边界
→ 机制篇理解数据或状态变化
→ 实验篇运行、观察和调试
→ 在检查点回到项目篇组合能力
```

状态：

- **可学习**：正文和必要实验已经存在。
- **待编写**：位置和核心问题已经确定。
- **等待前置**：材料存在，但需要先完成前面的课程或产品能力。

## 必备基础检查

必备基础不占课程序号。开始前确认能够使用 `uv run`，阅读 Python 类型、异常和异步代码，理解 HTTP、JSON、Schema、环境变量和流式响应。开始第 11 节前，还要理解 PostgreSQL Server、Database、Schema、Table、Role、migration 和基础 SQL；不足时回查 `source/python_base/` 与 PostgreSQL 概念篇。

# 第一阶段：RAG 应用基础

第一阶段回答：真实资料怎样成为可检索证据，固定 RAG 怎样形成可诊断、可引用、可拒答并能通过 API 与 Web 工作台交付的需求评审应用？

开始前先阅读[第一阶段项目篇](project/stage-1-rag-application/rag-review-assistant.md)中的业务场景、学习检查点和非目标，并了解根 [SPEC](../SPEC.md) 的第一阶段要求。

## 模型进入应用

1. **[LLM 在 AI 应用中的位置与边界](concepts/llm-in-ai-applications.md)** · 可学习
   区分普通程序、LLM、RAG、Agent 和 Workflow。
2. **[模型输入输出契约：Prompt、Schema 与 Context](concepts/model-input-output-contracts.md)** · 可学习
   理解任务、证据和结果为什么必须由应用建立契约。
3. **[Model API、调用生命周期与 Provider 抽象](mechanisms/model-api-and-provider.md)** · 可学习
   实验：[真实模型与 Provider](labs/model-api-and-provider.md)。
4. **[面向应用的 Prompt Engineering](mechanisms/prompt-engineering.md)** · 可学习
   实验：[Prompt 单变量对照](labs/prompt-engineering.md)。
5. **[Structured Output 与应用侧校验](mechanisms/structured-output.md)** · 可学习
   实验：[结构化输出与失败观察](labs/structured-output.md)。
6. **[Reliability、错误分类与可见降级](mechanisms/reliability-and-errors.md)** · 可学习
   实验：[可靠调用与结构化错误](labs/reliability-and-errors.md)。

## 建立固定 RAG 核心链

7. **[RAG 与外部知识的边界](concepts/rag-and-external-knowledge.md)** · 可学习
   建立文件到可信生成的总图，区分固定 RAG 与 Agentic RAG。
8. **[文档内容识别、解析路由、结构还原与来源保留](mechanisms/document-loading-and-cleaning.md)** · 可学习
   实验：[真实文档解析与错误边界](labs/document-loading-and-cleaning.md)。
9. **[Chunking、父子块与 Metadata](mechanisms/chunking-and-metadata.md)** · 可学习
   实验：[Chunk 策略对照](labs/chunking-and-metadata.md)。
10. **[Embedding 表示与向量相似度](mechanisms/embedding-and-similarity.md)** · 可学习
    实验：[真实 Embedding 相似度](labs/embedding-and-similarity.md)。
11. **[Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](mechanisms/lexical-retrieval.md)** · 可学习
    实验：[从空库到第一次按词检索](labs/lexical-retrieval.md)。
12. **[pgvector、Dense Retrieval 与向量索引](mechanisms/vector-store-and-pgvector.md)** · 可学习
    实验：[pgvector、exact 与 HNSW](labs/vector-store-and-pgvector.md)。
13. **[多路召回与 RRF 融合](mechanisms/multi-retrieval-and-rrf.md)** · 可学习
    实验：[Lexical、Dense 与 RRF 对照](labs/multi-retrieval-and-rrf.md)。
14. **[Top-k、阈值、Metadata Filter 与 Retrieval 诊断](mechanisms/retriever-contract.md)** · 可学习
    实验：[固定 Retriever 控制与诊断](labs/retriever-contract.md)。
15. **[Context Engineering：输入装配、预算与证据边界](mechanisms/context-engineering.md)** · 可学习
    实验：[从 RetrievalResult 到 BuiltContext](labs/context-engineering.md)。
16. **[可信生成、Sources、Citation Candidate 与证据不足](mechanisms/trusted-generation.md)** · 可学习
    实验：[结构化生成与 Citation Candidate](labs/trusted-generation.md)。

## 完成可信 RAG 与产品交付

17. **Citation 支持性校验** · 待编写
    判断模型声明的 Citation 是否真的支持对应结论。
18. **证据充分性、Refusal 与补充问题** · 待编写
    证据不足时拒绝强结论，并提出可回答的补充问题。
19. **AI Native 界面与不确定性表达** · 待编写
    建立结果、证据、状态和真实失败的产品表达。
20. **FastAPI、Review API 与错误契约** · 待编写
    将固定 RAG 暴露为稳定产品 API。
21. **Review 请求生命周期与状态契约** · 待编写
    区分接收、处理、完成、证据不足和失败状态。
22. **结构化风险、证据、Refusal 与补充信息交互** · 待编写
    用最小 Web 工作台呈现可信评审结果。

## 建立最小比较能力

23. **[LLM Calling Harness 与最小回归](mechanisms/calling-harness-and-regression.md)** · 等待前置
    固定 Case、Run Config 与 Record。
24. **[Token、成本、延迟与缓存边界](mechanisms/cost-latency-and-caching.md)** · 等待前置
    记录 usage、成本、阶段耗时和缓存影响。
25. **Evaluation Dataset 与最小 Golden Set** · 待编写
    固定问题、期望来源、风险覆盖和证据不足行为。
26. **直接 LLM、Lexical、Dense 与 RRF RAG 对比** · 待编写
    使用同一批样例比较质量、成本、延迟和失败。
27. **[第一阶段：固定 RAG 需求评审助手](project/stage-1-rag-application/rag-review-assistant.md)** · 等待前置
    完成固定 RAG 产品、真实 bad case、需求修改、固定对照和阶段验收。

# 第二阶段：Agent、Tools 与 Multi-Agent 系统

第二阶段回答：当查询、知识源、工具和协作步骤不能完全预先固定时，怎样让 Agent 动态行动，同时由应用控制权限、状态、停止、证据、恢复和评估？

开始第 28 节前，先阅读[第二阶段项目篇](project/stage-2-agent-system/agent-review-assistant.md)的业务目标、检查点和非目标。

## 最小 Agentic RAG

28. **固定程序、Workflow、Agent 与 Multi-Agent 的边界** · 待编写
29. **Agent Harness 与应用控制面** · 待编写
30. **Function Calling 与 Tool Schema** · 待编写
31. **Tool Runtime、结果与结构化错误** · 待编写
32. **Retriever as Tool** · 待编写
33. **Query Rewrite** · 待编写
34. **Source Routing 与补检索策略** · 待编写
35. **Agent Loop、预算与停止原因** · 待编写
36. **只读 Tool 的最小治理** · 待编写
37. **最小 Agentic RAG 检查点** · 待编写
    回到第二阶段项目篇，完成受治理 Retriever Tool 和可停止 Agent Loop。

## MCP、通用工具与 Agent Skills

38. **MCP 解决的问题、角色与连接边界** · 待编写
39. **MCP 生命周期、能力发现与真实接入** · 待编写
40. **Browser 与 Search Tool** · 待编写
41. **File Tool：读取、写入、权限与来源** · 待编写
42. **Code Tool：执行、沙箱、超时与副作用** · 待编写
43. **Agent Skills 与 Prompt、Tool、MCP 的边界** · 待编写
44. **Skill 的说明、资源、脚本、加载与执行** · 待编写
45. **外部工具与可复用能力检查点** · 待编写
    接入一个真实 MCP 能力和一个需求评审 Skill，验证权限、来源与错误。

## 状态、事件与产品运行

46. **Run State、Conversation、Memory 与业务知识边界** · 待编写
47. **短期记忆、摘要与 Context Budget** · 待编写
48. **Token Stream 与结构化 Event Stream** · 待编写
49. **SSE 传输和事件协议** · 待编写
50. **事件顺序、取消、重连与重复消费** · 待编写
51. **Agent Response State Machine 与运行界面** · 待编写
52. **Agent Tool、轨迹、停止与记忆评估检查点** · 待编写

长期偏好记忆保留在知识地图扩展区，不阻塞工具、Research 和 Multi-Agent 主线。

## Deep Research

53. **Planning、Task Decomposition 与进度检查** · 待编写
54. **迭代搜索与证据积累** · 待编写
55. **来源判断、交叉验证与冲突证据** · 待编写
56. **带来源综合、Citation 与停止条件** · 待编写
57. **Deep Research 评估与项目检查点** · 待编写

## Multi-Agent 与 A2A

58. **Multi-Agent 拆分判断** · 待编写
59. **角色、上下文、工具与输出契约** · 待编写
60. **Supervisor、Worker 与 Delegation** · 待编写
61. **共享状态、私有上下文与证据** · 待编写
62. **并行、依赖、取消与失败隔离** · 待编写
63. **结果合并、证据归属与冲突裁决** · 待编写
64. **A2A 解决的问题与协议边界** · 待编写
65. **A2A 任务生命周期、结果、错误与互操作** · 待编写
66. **Multi-Agent 运行观测与协作界面** · 待编写
67. **单 Agent 与 Multi-Agent 基线比较** · 待编写

## 必要 Workflow

68. **Workflow State、Node 与状态转换** · 待编写
69. **Checkpoint、Interrupt 与 Resume** · 待编写
70. **Human-in-the-loop** · 待编写
71. **重试、副作用与幂等** · 待编写
72. **Workflow as Tool、子 Agent 与可恢复编排** · 待编写

Workflow 不单独成为项目阶段，不建设低代码画布。

## 质量收束与最终交付

73. **结构化日志、Metrics 与事件关联** · 待编写
74. **Trace、Span 与 Run** · 待编写
75. **Versioning、Experiment 与 Regression** · 待编写
76. **LLM-as-Judge 与 Human Eval** · 待编写
77. **Bad Case 与 Feedback Loop** · 待编写
78. **[第二阶段：Agent 协作需求评审系统](project/stage-2-agent-system/agent-review-assistant.md)** · 待编写
    完成 Agentic RAG、MCP、Agent Skills、Deep Research、Multi-Agent、A2A、必要 Workflow、运行界面和阶段验收。

完整能力范围、扩展知识和实现位置见[知识地图](knowledge-map.md)。
