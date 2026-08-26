# 第一阶段：固定 RAG 需求评审助手

本文是第一阶段综合实践教材。产品要求以根 [SPEC](../../../SPEC.md) 为准，工程实现边界以 [PLAN](../../../PLAN.md) 为准；本文负责设计题、检查点、需求变更和学习验收，不复制完整产品规格。

> 使用方式：阶段开始时只读“业务场景”“Definition of Ready”“输入与输出契约”和“明确不做”，理解本阶段要解决的产品问题；完成[第一阶段标准学习路径](../../learning-path.md)中的概念、机制和实验后，再回到本文完成实现、真实 bad case、变更题和阶段验收。产品要求始终以根 `SPEC.md` 为准。

第一阶段要交付需求评审助手的第一个可运行产品。

它不是“上传文件后聊天”的 Demo，也不是单纯比较几个模型调用脚本。第一阶段要回答一个具体问题：

> 给定一份待评审 PRD 和一组固定业务资料，应用能否先检索相关证据，再基于证据输出可观察、可重复比较的需求风险结果？

第一阶段使用固定 RAG Pipeline，不使用 Agent 动态决策。直接调用 LLM 只作为对照基线，用来证明外部知识和检索链路是否真的带来价值。

## 业务场景

以“售后入口与订单状态”需求为固定垂直切片。

固定业务集由三类对象组成：

- **Target Requirement**：当前被评审的“售后入口 PRD”，作为 `ReviewRequest` 的直接输入，不默认作为普通知识 Chunk 参与检索。
- **Reference Knowledge**：订单状态规则、售后接口文档和客户端展示规则，是当前有效、允许成为业务证据的参考知识。
- **Historical Material**：历史需求评审记录，用于提供历史背景或已知 bad case；必须标明历史属性，不能自动覆盖当前有效规则。

Reference Knowledge 与 Historical Material 必须共同覆盖 TXT 或 Markdown、DOCX 和文本型 PDF，不能只用手写 JSON 或已经整理好的字符串替代真实文档加载。扫描 PDF、OCR、图片、音频和视频不作为第一阶段产品输入。

第一阶段默认不把 Target Requirement 与 Reference Knowledge 混在同一个 Retriever 候选池。若后续出现超长 PRD 需要对目标文档内部检索，应建立独立的 target-document 通道、作用域和诊断，不能无说明地把当前 PRD 当作外部证据。

这些资料在两个阶段持续复用。第二阶段可以增加样例覆盖 Agent、Tool 和协作问题，但不能通过更换整套案例规避回归比较。

典型评审问题包括：

- 哪些订单状态允许进入售后？
- PRD 与接口约束是否冲突？
- 客户端展示条件是否遗漏？
- 需求中有哪些证据不足、无法确认的结论？
- 哪些风险来自当前资料，哪些只是模型猜测？

## 已有基础

仓库已经具备：

- 真实模型与 OpenAI-compatible Provider 调用。
- Prompt 版本和 Structured Output。
- Context Builder。
- Streaming、错误分类、可靠调用和基础 Harness。
- Token、成本、延迟和缓存实验。

这些能力位于 `source/packages/llm_core/` 和现有 LLM demos。

第一阶段不重新实现这些能力，而是在此基础上增加唯一 `rag_core`，并在 `source/apps/review_assistant/` 组合成产品入口。

## Definition of Ready

第一阶段可以分段实现，但进入产品组合前必须先确定下面这些契约。这里检查的是设计是否具备实施条件，不要求产品已经完成：

- 固定“售后入口与订单状态”的 Target Requirement、Reference Knowledge、Historical Material、问题集和数据集版本；后续只增量补样例，不替换基线。
- 明确三类对象的身份、作用域和证据资格：当前 PRD 是评审主体，现行规则是主要证据，历史材料只能以明确的历史角色进入 Context。
- 明确 TXT / Markdown、DOCX、文本型 PDF 的解析范围、所选解析库和已知不支持结构。
- 明确 `KnowledgeDocument`、`Chunk`、来源定位和稳定标识契约。
- 明确 PostgreSQL 与 pgvector 版本、迁移方式，以及 Embedding Provider、配置、模型、向量维度和预处理版本共同构成的空间身份。
- 明确 lexical、dense、RRF 的参数语义、过滤顺序、阈值位置和诊断字段。
- 明确 Citation 支持性、证据充分性、Refusal 和补充问题的最小业务语义。
- 明确 Review API 的业务结果与错误分层，以及唯一 Web 工作台入口。
- 为第一次基线实验登记数据集、对照组、参数、指标、通过条件、成本和延迟预算。
- 确认不需要 Agent、Reranker、OCR、多模态平台、Flutter App 或其他第一阶段非目标。

某项真实依赖只有在对应正文、代码和运行入口一起落地时才加入；Definition of Ready 不授权创建空 package、空产品目录或占位配置。

## 本阶段新增结果

第一阶段需要跑通：

```text
Reference Knowledge + Historical Material
→ TXT / Markdown / DOCX / 文本型 PDF 加载与清洗
→ KnowledgeDocument / Chunk + Metadata
→ PostgreSQL 全文索引 + pgvector 向量索引
Target Requirement
→ 作为待评审主体直接输入
两路在 ReviewRequest 中汇合
→ 固定查询或评审问题
→ Lexical Retrieval + Dense Retrieval
→ RRF 融合
→ Top-k / 阈值 / Metadata Filter
→ Retriever 返回候选证据和诊断
→ Context Construction
→ 真实 LLM 生成结构化风险结果
→ 应用校验 Citation 支持性和证据充分性
→ 证据不足时 Refusal 或提出补充问题
→ Review API 返回业务结果与诊断
→ 最小工作台展示评审、来源、状态和真实失败
```

第一阶段的核心不是追求高级检索，而是让每一层都可以观察和替换。

## 输入与输出契约

### 输入

`ReviewRequest` 至少表达：

- `request_id`
- `requirement_id`
- `requirement_version`
- `title`
- `requirement_text`
- `review_questions`
- `knowledge_scope`

`request_id` 标识一次运行，`requirement_id` / `requirement_version` 标识当前被评审对象，`requirement_text` 保存该版本的直接输入。`knowledge_scope` 只约束 Reference Knowledge 和 Historical Material 的可检索范围，不用于把当前 PRD 伪装成外部知识。

具体 Schema 以产品代码为真源。项目篇只规定业务上必须表达的信息。

### 知识候选

第一阶段中只有 Reference Knowledge 和 Historical Material 进入通用知识生产链。`KnowledgeDocument` 至少保留：

- 稳定 `document_id`。
- `document_version` 或内容版本。
- 原始文件名、格式和受控来源位置。
- `source_role`，至少区分 `reference_knowledge` 与 `historical_material`。
- `evidence_eligibility` 或等价字段，说明该资料能否作为当前规则证据、只能作为历史参考，还是不能进入 Citation Candidate。
- 内容哈希或其他可复现的变更标识。
- 解析状态和明确错误。

每个可检索 `Chunk` 至少保留：

- 稳定 `chunk_id` 和所属 `document_id` / `document_version`。
- 文档名称、文档类型和文本内容。
- 结构化 `locator`：按格式表达章节、页码、段落或字符范围，不把不同格式强行伪装成同一种定位。
- 用于 `knowledge_scope` 的业务 Metadata。
- Chunk 策略版本和必要的父块关系。

`document_id` 标识业务文档，`document_version` 标识内容版本，`chunk_id` 标识该版本下的稳定片段。重新入库同一内容应得到可预测的标识；内容或切分策略改变时必须能够区分新旧 Chunk，不能依赖数据库自增 ID 作为 Citation Candidate。Target Requirement 使用独立的 `requirement_id` / `requirement_version`，不与知识文档标识混用。

### 输出

`ReviewReport` 至少表达：

- 本次评审摘要。
- 风险项列表。
- 每项风险的分类、严重程度、说明和建议。
- 每项外部事实风险对应的已校验 Citation，以及无法建立支持关系时的明确状态。
- 本轮检索到的来源候选和实际使用的证据。
- 证据充分性、Refusal、无法确认的信息和需要用户回答的补充问题。
- 模型、Prompt、Retriever、Token、延迟和错误等诊断。

第一阶段先在第 16 节展示来源候选并校验模型声明的来源是否属于本轮候选；第 17 节继续完成 Citation 支持性、证据充分性、Refusal 和补充问题。项目验收不能把“模型写出了来源编号”当成证据已经支持结论。

第一阶段的产品交互使用普通请求响应即可，至少区分 `idle`、`submitting`、`success` 和 `error`。Streaming、SSE 和 Agent 运行轨迹不是本阶段门禁。

## 进入项目之前

第一阶段项目篇不从头教授下面这些知识。开始综合实现前，应当已经能够：

- 解释 [LLM 在 AI 应用中的位置与边界](../../concepts/llm-in-ai-applications.md)，知道固定 RAG 为什么仍然需要真实模型调用。
- 使用 [Prompt、Context 与 Schema 的模型契约](../../concepts/model-input-output-contracts.md)描述一次评审调用的任务、证据和结果边界。
- 通过 [模型 API、Provider 与统一调用入口](../../mechanisms/model-api-and-provider.md)运行真实模型。
- 使用 [面向应用的 Prompt Engineering](../../mechanisms/prompt-engineering.md)和 [Structured Output 与本地校验](../../mechanisms/structured-output.md)生成可被程序消费的风险结果。
- 解释 TXT、Markdown、DOCX 和文本型 PDF 怎样经过加载、清洗、Chunk、Metadata、Embedding、索引和 Retrieval，能够观察每一步的输入输出。
- 区分 PostgreSQL FTS 的词项排序、BM25 原理、pgvector Dense Retrieval 和 RRF 排名融合，不能把 PostgreSQL 原生全文排序直接称为 BM25。
- 解释 Top-k、阈值、Metadata Filter 怎样改变候选集，并读懂每路排名、融合排名和淘汰原因。
- 说明 Retriever 产生候选证据，Context Builder 决定哪些证据真正进入模型，两者不是同一机制。
- 区分 Citation Candidate、模型声明的来源和应用校验后的 Citation，并解释证据不足时为什么应拒答或追问。
- 区分检索失败、上下文失败、模型调用失败和结构化校验失败。
- 使用固定样例记录检索命中、风险覆盖、无依据结论、Token 和延迟。

具体顺序只在 [标准学习路径](../../learning-path.md) 维护；完整知识范围可在 [知识地图](../../knowledge-map.md) 查询。支撑知识不要求一次读完，遇到真实问题时再进入。

## 关键设计选择

开始实现前必须作出并记录这些选择：

### 1. 为什么固定 Pipeline 足够

第一阶段固定 RAG 的步骤是已知的：

```text
加载
→ 切分
→ 检索
→ 构造上下文
→ 生成
```

模型不需要动态选择下一步，因此暂不使用 Agent。

### 2. 第一版支持哪些知识资料

第一阶段的 Reference Knowledge 与 Historical Material 必须支持 TXT、Markdown、DOCX 和带文本层的 PDF，并保留文档、章节、页码或段落位置。Target Requirement 作为直接输入，不靠重复入库来满足格式数量。允许先覆盖项目固定资料中实际出现的 DOCX 和 PDF 结构，不要求建设通用 Office 解析平台。

扫描 PDF、复杂版面、表格语义、图片 OCR/VLM、音频 ASR 和视频理解进入扩展概念或机制实验，不阻塞第一阶段产品链路。

### 3. 怎样比较检索

至少保留三类问题：

- 词面一致的问题。
- 同义改写的问题。
- 精确接口名、状态码或枚举问题。

先用 PostgreSQL FTS 建立可解释的 Lexical Retrieval，再使用真实 Embedding 服务和 pgvector 建立 Dense Retrieval，最后在应用层用 RRF 融合两路排名。第一阶段必须在同一组样例上比较 lexical、dense 和 RRF 三条检索路径。

RRF 只融合名次，不假装不同检索器的原始分数可以直接相加。Reranker 会增加模型调用、延迟和调试面，保留为扩展机制；只有评估证明收益大于复杂度时才进入产品默认链路。

第一阶段的检索参数遵守下面的固定语义：

1. `knowledge_scope`、`source_role` 与 Metadata Filter 在 lexical 和 dense 两路检索前应用，保证两路候选来自同一可见文档池，并防止 Target Requirement 无说明地进入参考知识检索。
2. 每路分别设置 `candidate_k` 和该路原生分数阈值；FTS 相关性与向量相似度保留各自名称、方向和原始值。
3. 每路阈值在 RRF 前执行。不同检索器的原始分数不归一化相加，也不互相比较。
4. RRF 只接收通过过滤和阈值的排名列表，使用固定 `rrf_k`，按稳定 `chunk_id` 去重并保留命中路由。
5. `final_top_k` 在融合后执行。第一阶段默认不再用另一个模糊的“统一相关性阈值”过滤 RRF 结果；若实验需要 fused threshold，必须单独命名、解释分数含义并提前登记。
6. 任一参数变化都属于 Retriever 配置版本变化，必须进入运行记录，不能只修改代码常量。

一次 Retrieval 诊断至少返回：查询、知识范围、每路配置、过滤前后数量、候选 `chunk_id`、原生分数与方向、路由排名、阈值淘汰原因、RRF 分数、融合排名、最终入选结果、耗时和结构化错误。面向普通用户的业务结果不直接暴露全部工程字段，调试视图和运行记录必须可以查看。

### 4. 怎样组织上下文

必须确定：

- 每路 `candidate_k` 和最终 `final_top_k`。
- 每路原生分数阈值及其方向。
- `knowledge_scope` 与 Metadata Filter。
- RRF 的 `rrf_k`、候选去重和稳定标识。
- Chunk 排序。
- 去重。
- Token 预算。
- 来源标记格式。
- Reference Knowledge 与 Historical Material 的分区、证据资格和优先级。
- 没有候选材料时的行为。

### 5. 哪些信息进入产品输出

业务结果和工程诊断必须分开。用户看到评审报告，学习和调试入口还能看到检索候选、最终上下文、模型信息、Token、延迟和错误。

### 6. 唯一前端入口

第一阶段只建设一个 Web 工作台，不建设 Flutter App，也不在 `source/apps/` 维护第二份产品页面。工作台至少支持提交待评审需求，展示请求状态、结构化风险、Citation、Refusal、补充问题、最终上下文摘要和真实错误；诊断信息可以使用独立调试区域，不要求做通用知识库后台。

## 代码职责

### `source/packages/rag_core/`

负责通用能力：

- 文档和 Chunk 数据类型。
- Loader / Cleaning。
- Chunking / Metadata。
- PostgreSQL FTS 与 pgvector 适配。
- Lexical、Dense 与 RRF Retriever。
- Top-k、阈值、Metadata Filter 与检索诊断。
- RAG Context Construction。
- 固定 RAG Pipeline。
- Citation 支持性、证据充分性、Refusal 和补充问题的通用校验能力。

### `source/apps/review_assistant/`

负责产品组合：

- 固定 Target Requirement、Reference Knowledge 与 Historical Material fixtures。
- 产品级 ReviewRequest / ReviewReport。
- FastAPI Review API 与结构化错误契约。
- 最小 AI Native Web 工作台和请求状态。
- 产品测试与最小评估样例。
- 调用 `llm_core` 和 `rag_core`。
- 产品 README 中的安装、配置、运行和排错。

产品的真实运行入口和命令由 [review_assistant README](../../../source/apps/review_assistant/README.md) 维护，项目篇不复制产品运行手册。

## 运行契约

真实代码开始落地时，产品 README、配置和迁移必须共同说明：

- PostgreSQL 与 pgvector 的版本、扩展启用和迁移命令。
- 数据库连接、真实 Embedding 与真实 LLM 所需环境变量。
- Embedding Provider、配置、模型名称、向量维度、预处理版本，以及空间身份变化后的重建索引规则。
- DOCX、PDF 解析库、支持范围和失败表现。
- 资料入库、启动 API、启动 Web、运行测试和运行评估的唯一主命令。
- 本地输出、运行记录和敏感配置的保存边界。

这些选择是产品运行事实，不在项目篇长期固定供应商、库版本或秘密配置。实现发生变化时更新产品 README 和锁文件，项目篇只维护必须可运行、可诊断和可重建的契约。

## 分段实现顺序

第一阶段的范围必须按纵向切片推进，每一段都留下可观察结果，再进入下一段：

1. **契约与资料**：固定三类 fixtures，完成 Target Requirement 与知识资料的身份边界，以及 `KnowledgeDocument` / `Chunk` / locator / Metadata 契约和 TXT、Markdown、DOCX、文本型 PDF 的解析对照。
2. **Lexical 基线**：先让 PostgreSQL FTS 单路检索可运行，记录词项命中、原生 rank、阈值和过滤诊断。
3. **Dense 基线**：接入真实 Embedding 与 pgvector，固定 Provider、配置、模型、维度和预处理版本，记录相似度方向、索引和单路失败。
4. **RRF 融合**：在两路结果之上实现应用侧 rank fusion、去重、`rrf_k`、`final_top_k` 和完整诊断。
5. **Context 与生成**：将 RetrievalResult 交给已有 Context Builder 和真实结构化 LLM，区分检索、上下文、生成和 Schema 失败。
6. **Review API 与 Web**：组合唯一产品入口，先完成普通请求响应、状态、风险、来源候选、上下文摘要和真实错误展示。
7. **评估与验收**：运行四路对照、真实 bad case / 策略边界、需求变更和实验前登记的质量门槛，形成第一阶段运行记录。

某一段暂时失败时，优先修复该段的契约或诊断，不通过增加新框架或跳过前置段落推进。

## 数据流、状态流与异常流

### 数据流

```text
Reference Knowledge + Historical Material
→ KnowledgeDocument
→ Chunk
→ PostgreSQL FTS / pgvector 索引
→ LexicalResult + DenseResult
→ RRF Fusion
→ RetrievalResult ────────────┐
                              ├→ ReviewContext → ReviewReport
Target Requirement ──────────┘
```

每次转换必须能保留来源关系，不能到模型输出时才临时猜测来源。Target Requirement 是评审主体，不因进入 ReviewContext 就成为 Citation Candidate；只有满足证据资格的知识来源才能进入候选引用。

### 状态流

第一阶段即使不建立后台任务，也要能够区分：

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
- Lexical 或 Dense 单路检索失败。
- RRF 候选无法通过稳定 Chunk ID 合并。
- 检索无结果。
- 候选全部被阈值或 Metadata Filter 淘汰。
- Context 超出预算。
- 模型鉴权、限流、超时或能力不支持。
- Structured Output 校验失败。

真实失败必须清晰暴露，不静默退回 Mock 或伪造评审结果。

## 需要观察的真实 bad case 与策略边界

完成正常链路后，从固定业务样例、真实外部依赖和正常参数变化中至少复现或观察一项：

1. 问题不在知识资料中。
2. 关键词相同但实际语义不相关。
3. 同义改写导致关键词检索失败。
4. 精确接口名被纯向量检索排到后面。
5. top-k 太小遗漏关键证据。
6. top-k 太大导致无关上下文干扰。
7. 阈值太高导致两路候选全部被淘汰。
8. 一路检索排名很差，但 RRF 仍错误提升无关结果。
9. Metadata Filter 错误排除本应可见的资料。
10. Target Requirement 被错误加入参考知识候选，导致检索和评估泄漏。
11. Historical Material 与当前规则冲突，却因未标明历史角色覆盖现行证据。
12. 缺少真实模型 API key。
13. 模型返回不符合 Schema 的结果。

这些现象不要求通过损坏实现或凭空构造异常获得。每个被选作验收证据的现象都要记录：

- 表现。
- 可能原因。
- 如何验证。
- 应修改数据、Retriever、Context、Prompt、Schema 还是模型配置。

## 需求变更题

在第一阶段主链跑通后，完成一次真实变更：

> 新增“客户端影响范围”，要求每个风险项标明影响 Web、Flutter、服务端还是多端共同修改。

需要判断：

- 修改业务 Schema 的位置。
- Prompt 如何同步。
- 哪些评估样例需要更新。
- UI 如何展示。
- 旧结果如何兼容或明确不兼容。

## 评估与通过条件

### 固定评估数据

第一阶段使用版本化的小型固定数据集。每个 Case 至少记录：

- `case_id`、问题和所属问题类型。
- `requirement_id`、`requirement_version` 和对应 Target Requirement。
- `split`，取值为用于开发诊断和调参的 `development`，或只用于阶段验收的 `acceptance`。
- `dataset_version` 和允许的 `knowledge_scope`。
- 期望命中的 `document_id` / `chunk_id` 或可验证来源范围。
- 不应命中的来源。
- 期望覆盖的风险类别。
- 是否应该明确表示证据不足。

`development` Case 用于观察失败、选择 Chunk 策略和调整 Retriever 参数；`acceptance` Case 在首次验收运行前冻结，不能用于选择参数。两部分都至少覆盖词面一致、同义改写、精确接口名或枚举、无答案、噪声相似和 Metadata Filter 六类问题，每类至少有一个稳定 Case。Reference Knowledge 与 Historical Material 至少各有明确角色，知识资料格式至少各有一个可重复解析的 TXT 或 Markdown、DOCX 和文本型 PDF fixture。

样例数量可以增长，但删除、改写或改变 Case 的 split 必须提升 `dataset_version` 并说明原因。验收失败后可以保留失败记录并创建新实验，但不能根据 acceptance 结果删除 Case、降低门槛或把 Case 移入 development；若要改变验收集，必须发布新的数据集版本，并把原结果保留为历史证据。第一阶段只建立小型基线，完整数据集治理和评估平台保留为后续质量收束或扩展能力。

### 对照路径

至少比较：

- 直接 LLM。
- PostgreSQL FTS Lexical RAG。
- 使用真实 Embedding 和 pgvector 的 Dense RAG。
- 使用 RRF 多路召回的 RAG。

四条路径使用相同输入、数据集版本、生成模型、Prompt、Schema 和输出预算。检索策略是主要变量；若必须改变其他变量，应建立新的实验而不是混入当前比较。

### 指标契约

| 维度 | 第一阶段必须记录 | 能证明什么 |
| --- | --- | --- |
| 解析 | 文件成功/失败、文档与 Chunk 数、来源角色、证据资格和定位完整性 | 参考与历史资料能否稳定进入知识系统且不混淆角色 |
| Retrieval | 每路与融合后的 Source Hit@k、Source Recall@k、MRR@k、禁止来源命中、无结果原因 | 是否命中、是否覆盖完整及排序是否改善 |
| Generation | Schema 结果、风险类别覆盖、无依据结论、证据不足行为 | 检索结果是否转化为更可靠的评审结果 |
| 工程 | 成功/失败层级、Token、成本、各阶段耗时和总延迟 | 改进是否付出不可接受的工程代价 |

每个 Case 必须在运行前确定相关性判断单位是 `document_id`、`chunk_id` 还是可验证来源范围，运行后不能为了提高结果更换单位。第一阶段使用以下定义：

- Source Hit@k：期望来源集合中至少有一个来源出现在前 `k` 个结果中，命中记为 `1`，否则为 `0`。
- Source Recall@k：前 `k` 个结果命中的期望来源数除以该 Case 的全部期望来源数。
- MRR@k：前 `k` 个结果中第一个期望来源排名的倒数；没有期望来源时记为 `0`。

无答案 Case 的期望来源集合为空，Hit@k、Recall@k 和 MRR@k 记为 `N/A`，不混入有答案 Case 的均值；它通过禁止来源命中、无结果原因、证据不足行为和无依据结论单独验收。汇总时至少同时保留 Case 结果、问题类型的宏平均和整体宏平均，不能用高频类别掩盖弱项。禁止来源命中也必须独立记录，不能被总体 Hit 或 Recall 抵消。风险覆盖和无依据结论需要保存 Case 级判断依据。

第一阶段不使用“感觉更好”作为指标，也不要求 RRF 在每个 Case 都排名第一。人工判断风险覆盖或无依据结论时，必须保存判断依据，不能只保留总分。

### 实验前登记

第一次运行及后续每次比较前，必须登记：

- `experiment_id`、`dataset_version`、Case 范围、development / acceptance split 和运行时间窗口。
- 生成模型、Embedding 空间身份、Prompt、Schema、Chunk 和 Retriever 配置版本。
- lexical / dense 的 `candidate_k`、原生阈值、`rrf_k`、`final_top_k` 和 Metadata Filter。
- 对照组、实验组、Source Hit@k / Recall@k / MRR@k 的具体 `k`，以及按问题类型登记的最低门槛。
- 允许的禁止来源命中、无依据结论、成本和延迟预算。
- 本轮通过条件和运行记录位置。

具体数值按数据规模和运行环境在实验前确定，不写成全课程永久常量。运行后修改任一项都必须创建新的 `experiment_id`，不得覆盖原记录。

### 质量通过条件

除下方完成标准外，本轮基线必须同时满足：

1. 所有固定 Case 都在四条路径留下可关联配置版本的运行记录；真实服务失败可以记为失败，不能被删除或替换成 Mock 成功。
2. 三种必需资料格式都有成功解析样例，来源定位和稳定标识满足契约；不支持结构以明确错误暴露。
3. 每个成功模型响应都通过业务 Schema；解析失败作为生成失败记录，不进入成功结果。
4. 每项声称依赖外部事实的风险都能回到经过应用校验的 Citation；证据不足时进入 Refusal 或补充问题，而不是生成无依据结论。
5. RRF 在冻结的 acceptance Case 上达到实验前按问题类型登记的 Source Hit@k / Recall@k 最低门槛；无答案 Case 按独立门槛验收，不参与这些指标的平均。
6. 在相同 `final_top_k` 下，RRF 至少在一种已登记的 lexical 或 dense 单路弱项问题中恢复期望来源，证明两路召回具有互补价值；第一阶段小型数据集不要求 RRF 的整体均值机械高于每个单路基线。
7. RRF 的禁止来源命中和无依据结论不超过实验前登记的上限；成本和延迟不超过实验前登记的第一阶段预算。lexical、dense 与 RRF 的分类结果仍必须并列保存，不能只报告融合结果。
8. 若第 4–7 项不满足，第一阶段不能宣称可信混合检索基线成立。应在 development Case 上调整数据、Chunk、阈值、证据策略或融合配置并创建新实验，保留失败的 acceptance 记录，而不是删除验收 Case、降低原实验标准或用新的总体均值掩盖分类弱项。

这里验收的是可重复的产品基线，不是完整评估平台。自动评审、实验管理、反馈和质量工作台在第二阶段质量收束或扩展能力中进入。

## 范围冻结与变更规则

Definition of Ready 完成后，第一阶段主路径默认冻结：

- 只有缺少某项能力会使第一阶段输入、输出、可信性、可用性或验收契约不成立，或者现有内容无法解释已复现的阻塞失败时，才允许增加第一阶段主线知识。
- 新框架、数据库、模型或平台功能本身不是扩展理由；优先合并进现有机制，或按分级准入进入概念、机制和未来认知。
- 改变支持格式、检索路线、产品入口或产品验收要求时，先更新根 `SPEC.md`；改变稳定工程分解时更新 `PLAN.md`，随后再实现代码并提升受影响的数据集或实验版本。
- 实现中的任务拆分、实时进度和运行结果不写回 `course/learning-path.md`；它们进入代码、产品 README、测试、eval 配置和运行记录。

## 明确不做

- Query Rewrite 和 Source Routing。
- Retriever as Tool。
- Agent Loop。
- Workflow、Checkpoint 和 Human-in-the-loop。
- Multi-Agent。
- 完整 Citation 运营后台、跨版本知识治理和自动化证据标注平台。
- Reranker 进入产品默认链路。
- 完整知识库运营平台。
- 多租户、权限中台和通用连接器。
- GraphRAG、RAPTOR、Neo4j 和复杂 OCR / 多模态解析平台。

这些能力只有在第二阶段或扩展机制解决真实问题时进入。

## 完成标准

- [ ] 使用固定 Target Requirement、Reference Knowledge 和 Historical Material 跑通完整 RAG 数据流。
- [ ] 当前 PRD 作为评审主体直接输入，不会无说明地进入参考知识候选或成为 Citation Candidate。
- [ ] TXT 或 Markdown、DOCX 和文本型 PDF 知识资料都能进入同一 Document / Chunk 契约并保留来源角色与位置。
- [ ] 主路径调用真实 Embedding 和真实 LLM；失败不降级 Mock。
- [ ] 使用 PostgreSQL FTS、pgvector 和应用侧 RRF 完成 lexical、dense 与多路融合召回。
- [ ] 能看到 Chunk、Metadata、每路排名、融合排名、Top-k、阈值、过滤结果和最终上下文。
- [ ] 输出通过本地业务 Schema 校验。
- [ ] 外部事实风险能回到经过应用校验的 Citation；证据不足时 Refusal 或提出补充问题。
- [ ] 直接 LLM、Lexical RAG、Dense RAG 和 RRF RAG 使用同一组样例比较。
- [ ] 能区分检索失败、上下文失败和生成失败。
- [ ] 至少完成一个真实 bad case / 策略边界观察和一个需求变更。
- [ ] 有最小固定评估样例和运行记录。
- [ ] 通用能力只存在于唯一 `rag_core`。
- [ ] 产品入口位于 `source/apps/review_assistant/`，没有在 `source/apps/` 维护第二份产品。
- [ ] 最小工作台能提交需求、展示结构化风险、Citation、Refusal、补充问题和来源候选，并区分运行、成功与真实失败。
- [ ] 能解释为什么第一阶段不需要 Agent。

达到这些标准后，固定 RAG 已具备进入第二阶段 Agent Harness 与 Retriever as Tool 的稳定契约。
