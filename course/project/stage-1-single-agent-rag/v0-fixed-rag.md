# V0：固定 RAG 需求评审基线

> 课程位置：这是 V0 的综合实践与验收文档，不是课程第一篇。请先完成 [V0 标准学习路径](../../learning-path.md) 中的核心概念、机制和小实验；如果下面的术语仍然陌生，先回到对应步骤。

V0 是需求评审助手的第一个可运行产品版本。

它不是“上传文件后聊天”的 Demo，也不是单纯比较几个模型调用脚本。V0 要回答一个具体问题：

> 给定一份待评审 PRD 和一组固定业务资料，应用能否先检索相关证据，再基于证据输出可观察、可重复比较的需求风险结果？

V0 使用固定 RAG Pipeline，不使用 Agent 动态决策。直接调用 LLM 只作为对照基线，用来证明外部知识和检索链路是否真的带来价值。

## 业务场景

以“售后入口与订单状态”需求为固定垂直切片。

核心资料集至少包含：

- 一份售后入口 PRD。
- 一份订单状态规则。
- 一份售后接口文档。
- 一份客户端展示规则。
- 一份历史需求评审记录。

这些资料在 V0–V6 持续复用。后续版本可以增加样例覆盖新问题，但不能通过更换整套案例规避回归比较。

典型评审问题包括：

- 哪些订单状态允许进入售后？
- PRD 与接口约束是否冲突？
- 客户端展示条件是否遗漏？
- 需求中有哪些证据不足、无法确认的结论？
- 哪些风险来自当前资料，哪些只是模型猜测？

## V0 已有基础

仓库已经具备：

- 真实模型与 OpenAI-compatible Provider 调用。
- Prompt 版本和 Structured Output。
- Context Builder。
- Streaming、错误分类、可靠调用和基础 Harness。
- Token、成本、延迟和缓存实验。

这些能力位于 `source/packages/llm_core/` 和现有 LLM demos。

V0 不重新实现这些能力，而是在此基础上增加唯一 `rag_core`，并在 `review_assistant/` 组合成产品入口。

## 本版本新增结果

V0 需要跑通：

```text
固定知识资料
→ 文档加载与清洗
→ Chunk + Metadata
→ 建立可检索索引
→ 输入待评审 PRD
→ 固定查询或评审问题
→ Retriever 返回候选证据
→ Context Construction
→ 真实 LLM 生成结构化风险结果
→ 输出检索诊断、来源候选和调用信息
```

V0 的核心不是追求高级检索，而是让每一层都可以观察和替换。

## 输入与输出契约

### 输入

`ReviewRequest` 至少表达：

- `request_id`
- `title`
- `requirement_text`
- `review_questions`
- `knowledge_scope`

具体 Schema 以产品代码为真源。项目篇只规定业务上必须表达的信息。

### 知识候选

每个可检索 Chunk 至少保留：

- 稳定 `source_id`
- 文档名称
- 文档类型
- 章节或位置
- 文本内容
- 版本或更新时间

### 输出

`ReviewReport` 至少表达：

- 本次评审摘要。
- 风险项列表。
- 每项风险的分类、严重程度、说明和建议。
- 检索到的来源候选。
- 无法确认或需要补充的信息。
- 模型、Prompt、Retriever、Token、延迟和错误等诊断。

V0 可以展示来源候选，但不把“模型写出了来源编号”视为已经完成 Citation 校验。严格 Citation、Refusal 和证据充分性进入 V1。

## 进入项目之前

V0 不从头教授下面这些知识。开始综合实现前，应当已经能够：

- 解释 [LLM 在 AI 应用中的位置与边界](../../concepts/llm-in-ai-applications.md)，知道固定 RAG 为什么仍然需要真实模型调用。
- 使用 [Prompt、Context 与 Schema 的模型契约](../../concepts/model-input-output-contracts.md)描述一次评审调用的任务、证据和结果边界。
- 通过 [模型 API、Provider 与统一调用入口](../../mechanisms/llm/model-api-and-provider.md)运行真实模型。
- 使用 [面向应用的 Prompt Engineering](../../mechanisms/llm/prompt-engineering.md)和 [Structured Output 与本地校验](../../mechanisms/llm/structured-output.md)生成可被程序消费的风险结果。
- 解释文档为什么要经过加载、清洗、Chunk、Metadata、Embedding、索引和 Retrieval，能够观察每一步的输入输出。
- 说明 Retriever 产生候选证据，Context Builder 决定哪些证据真正进入模型，两者不是同一机制。
- 区分检索失败、上下文失败、模型调用失败和结构化校验失败。
- 使用固定样例记录检索命中、风险覆盖、无依据结论、Token 和延迟。

具体顺序只在 [标准学习路径](../../learning-path.md) 维护；完整知识范围可在 [知识地图](../../knowledge-map.md) 查询。支撑知识不要求一次读完，遇到真实问题时再进入。

## 关键设计选择

开始实现前必须作出并记录这些选择：

### 1. 为什么固定 Pipeline 足够

V0 的步骤是已知的：

```text
加载
→ 切分
→ 检索
→ 构造上下文
→ 生成
```

模型不需要动态选择下一步，因此暂不使用 Agent。

### 2. 第一版支持哪些资料

优先支持能稳定解析、能保留来源的 Markdown、TXT 或结构化样例。复杂 PDF、OCR、表格理解属于后续机制，不应阻塞第一条垂直链路。

### 3. 怎样比较检索

至少保留三类问题：

- 词面一致的问题。
- 同义改写的问题。
- 精确接口名、状态码或枚举问题。

可先用关键词检索建立可解释基线，再增加 Embedding 或向量检索比较。不能只展示一种策略的成功案例。

### 4. 怎样组织上下文

必须确定：

- top-k。
- Chunk 排序。
- 去重。
- Token 预算。
- 来源标记格式。
- 没有候选材料时的行为。

### 5. 哪些信息进入产品输出

业务结果和工程诊断必须分开。用户看到评审报告，学习和调试入口还能看到检索候选、最终上下文、模型信息、Token、延迟和错误。

## 代码职责

### `source/packages/rag_core/`

负责通用能力：

- 文档和 Chunk 数据类型。
- Loader / Cleaning。
- Chunking / Metadata。
- Embedding 和检索适配。
- Retriever 契约与诊断。
- RAG Context Construction。
- 固定 RAG Pipeline。

### `review_assistant/`

负责产品组合：

- 固定业务资料。
- 产品级 ReviewRequest / ReviewReport。
- FastAPI 或明确的产品运行入口。
- 产品测试与最小评估样例。
- 调用 `llm_core` 和 `rag_core`。
- 产品 README 中的安装、配置、运行和排错。

产品的真实运行入口和命令由 [review_assistant README](../../../review_assistant/README.md) 维护，项目篇不复制产品运行手册。

## 数据流、状态流与异常流

### 数据流

```text
文件
→ KnowledgeDocument
→ Chunk
→ 索引
→ RetrievalResult
→ ReviewContext
→ ReviewReport
```

每次转换必须能保留来源关系，不能到模型输出时才临时猜测来源。

### 状态流

V0 即使不建立后台任务，也要能够区分：

- 资料未加载。
- 加载成功。
- 索引成功。
- 检索完成。
- 模型生成完成。
- 运行失败。

### 异常流

至少区分：

- 文档加载失败。
- 没有生成有效 Chunk。
- Embedding 或索引失败。
- 检索无结果。
- Context 超出预算。
- 模型鉴权、限流、超时或能力不支持。
- Structured Output 校验失败。

真实失败必须清晰暴露，不静默退回 Mock 或伪造评审结果。

## 需要主动制造的失败

完成正常链路后，至少复现：

1. 问题不在知识资料中。
2. 关键词相同但实际语义不相关。
3. 同义改写导致关键词检索失败。
4. 精确接口名被纯向量检索排到后面。
5. top-k 太小遗漏关键证据。
6. top-k 太大导致无关上下文干扰。
7. 缺少真实模型 API key。
8. 模型返回不符合 Schema 的结果。

每个失败都要记录：

- 表现。
- 可能原因。
- 如何验证。
- 应修改数据、Retriever、Context、Prompt、Schema 还是模型配置。

## 需求变更题

在 V0 跑通后，完成一次真实变更：

> 新增“客户端影响范围”，要求每个风险项标明影响 Web、Flutter、服务端还是多端共同修改。

需要判断：

- 修改业务 Schema 的位置。
- Prompt 如何同步。
- 哪些评估样例需要更新。
- UI 如何展示。
- 旧结果如何兼容或明确不兼容。

## 最小评估

V0 至少保留一组小型固定样例：

- 问题。
- 期望命中的来源。
- 不应命中的来源。
- 期望覆盖的风险类别。
- 是否应该明确表示证据不足。

至少比较：

- 直接 LLM。
- 关键词检索 RAG。
- 向量或混合检索 RAG（当该机制落地后）。

关注：

- Retrieval 命中。
- 风险覆盖。
- 无依据结论。
- Token、成本和延迟。

V0 不要求完整评估平台，但结果必须可重复记录。

## V0 明确不做

- Query Rewrite 和 Source Routing。
- Retriever as Tool。
- Agent Loop。
- Workflow、Checkpoint 和 Human-in-the-loop。
- Multi-Agent。
- 完整 Citation 校验。
- 完整知识库运营平台。
- 多租户、权限中台和通用连接器。
- GraphRAG、RAPTOR 和复杂 OCR 平台。

这些能力只有在后续版本解决真实问题时进入。

## 完成标准

- [ ] 使用固定业务资料跑通完整 RAG 数据流。
- [ ] 主路径调用真实 Embedding 和真实 LLM；失败不降级 Mock。
- [ ] 能看到 Chunk、Metadata、检索候选和最终上下文。
- [ ] 输出通过本地业务 Schema 校验。
- [ ] 直接 LLM 与至少一种检索 RAG 使用同一组样例比较。
- [ ] 能区分检索失败、上下文失败和生成失败。
- [ ] 至少完成一个主动失败复现和一个需求变更。
- [ ] 有最小固定评估样例和运行记录。
- [ ] 通用能力只存在于唯一 `rag_core`。
- [ ] 产品入口位于 `review_assistant/`，没有在 `source/apps/` 维护第二份产品。
- [ ] 能解释为什么 V0 不需要 Agent。

达到这些标准后，才进入 V1 的 Citation 校验、Refusal 和证据充分性。
