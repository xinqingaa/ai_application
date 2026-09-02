# 第一阶段：固定 RAG 需求评审助手

本文是第一阶段综合实践教材。产品要求以根 [SPEC](../../../SPEC.md) 为准，工程实现边界以 [PLAN](../../../PLAN.md) 为准；本文负责设计题、检查点、需求变更和学习验收，不复制完整产品规格。

> 使用方式：阶段开始时只读“业务场景”“Definition of Ready”“输入与输出契约”和“明确不做”，理解本阶段要解决的产品问题；完成[第一阶段标准学习路径](../../learning-path.md)中的概念、机制和实验后，再回到本文完成实现、真实 bad case、变更题和阶段验收。产品要求始终以根 `SPEC.md` 为准。

第一阶段要交付需求评审助手的第一个可运行产品。

它不是“上传文件后聊天”的 Demo，不是单纯比较几个模型调用脚本，也不是“贴一份 PRD、拿一份报告”的一次性工具。第一阶段要回答一个具体问题：

> 给定一份待定义或待评审的需求和一组固定业务资料，应用能否把需求收敛为结构化条目，先检索相关证据，再基于证据输出可定位、可逐项决策、可重复比较的评审结论，并让人把收敛后的版本批准为基线、从基线导出交付包？

第一阶段使用固定 RAG Pipeline，不使用 Agent 动态决策；需求版本的持久状态迁移全部由人的显式动作触发，ReviewRun、知识解析与索引状态由固定程序推进，且不自动改变需求版本状态。直接调用 LLM 只作为对照基线，用来证明外部知识和检索链路是否真的带来价值。

## 业务场景

以“售后入口与订单状态”需求为固定垂直切片，并映射到产品对象：Project 是一个电商 App；Requirement 是“售后入口”这一需求主题；第一阶段的 v1 版本由导入现有 Target Requirement fixture 得到，经评审、决策、人工批准后成为该 Requirement 的第一条基线。

固定业务集由四类对象组成：

- **Target Requirement**：当前被定义和评审的“售后入口 PRD”。第一阶段通过导入入口保存为 SourceArtifact，再映射为 RequirementVersion 的条目；它是评审主体，可以支撑内部缺失与矛盾 Finding 的定位，但不进入 Retriever 候选池，不能成为 Citation Candidate。
- **Reference Knowledge**：订单状态规则、售后接口文档和客户端展示规则，是当前有效、允许成为业务证据的参考知识，进入全局知识库。
- **Historical Material**：历史需求评审记录，用于提供历史背景或已知 bad case；必须标明历史属性，不能自动覆盖当前有效规则。
- **Approved Requirement**：同一 Project 内其他 Requirement 已批准并已索引的基线，以 `approved_requirement` 角色进入项目检索池，用于说明“项目内已批准的产品决定”；它不自动覆盖现行业务规则，二者冲突时应产生可见 Finding。因为派生版本评审时排除自身基线，主路径上必须有一个独立的第二个 Requirement 才能让这个池子非空：固定业务集提供一个同 Project 的小型“订单状态展示”需求，以已批准、已索引的基线 fixture 形式存在，其中至少一条条目与售后入口需求存在可复现的冲突点（例如可进入售后的订单状态集合）。

Reference Knowledge 与 Historical Material 必须共同覆盖 TXT 或 Markdown、DOCX 和文本型 PDF，不能只用手写 JSON 或已经整理好的字符串替代真实文档加载。扫描 PDF、OCR、图片、音频和视频不作为第一阶段产品输入。

Target Requirement 不与 Reference Knowledge 混在同一个 Retriever 候选池；当前待评审版本也不能把自身或自身旧基线伪装成外部证据。若后续出现超长 PRD 需要对目标文档内部检索，应建立独立的 target-document 通道、作用域和诊断，不能无说明地把当前 PRD 当作外部证据。

这些资料在两个阶段持续复用。第二阶段的“售后接口 v2 与多端契约一致性”是同一 Requirement 的新 RequirementVersion，不是新 Requirement；第二阶段可以增加样例覆盖 Agent、Tool 和协作问题，但不能通过更换整套案例规避回归比较。

典型评审问题包括：

- 哪些订单状态允许进入售后？
- PRD 与接口约束是否冲突？
- 客户端展示条件是否遗漏？
- 需求中有哪些证据不足、无法确认的结论？
- 哪些风险来自当前资料，哪些只是模型猜测？
- 当前需求与同项目已批准的其他需求是否矛盾？

## 已有基础

仓库已经具备：

- 真实模型与 OpenAI-compatible Provider 调用。
- Prompt 版本和 Structured Output。
- Context Builder。
- 错误分类、可靠调用和基础 Harness。
- Token、成本、延迟和缓存实验。
- 真实文档解析、Chunk、Embedding、PostgreSQL FTS、pgvector、RRF、Retriever Contract、Context 适配与来源声明集合检查。

这些能力位于 `source/packages/llm_core/`、`source/packages/rag_core/` 和现有 demos。

第一阶段不重新实现这些能力，而是补齐 Citation 支持性与证据充分性，在 `source/apps/review_assistant/` 建立需求对象模型，并把它们组合成产品入口。

## Definition of Ready

第一阶段可以分段实现，但进入产品组合前必须先确定下面这些契约。这里检查的是设计是否具备实施条件，不要求产品已经完成：

- 固定“售后入口与订单状态”的 Target Requirement、Reference Knowledge、Historical Material、同项目“订单状态展示”已批准基线 fixture、问题集和数据集版本；后续只增量补样例，不替换基线。
- 明确四类对象的身份、作用域和证据资格：当前需求版本是评审主体，现行规则是主要证据，历史材料只能以明确的历史角色进入 Context，已批准需求以 `approved_requirement` 角色进入项目检索池且不覆盖现行规则。
- 明确 TXT / Markdown、DOCX、文本型 PDF 的解析范围、所选解析库和已知不支持结构。
- 明确 `KnowledgeDocument`、`Chunk`、来源定位和稳定标识契约。
- 明确 PostgreSQL 与 pgvector 版本、迁移方式，以及 Embedding Provider、配置、模型、向量维度和预处理版本共同构成的空间身份。
- 明确 lexical、dense、RRF 的参数语义、过滤顺序、阈值位置和诊断字段。
- 明确 Citation 支持性、证据充分性、Refusal 和补充问题的最小业务语义。
- 明确需求对象主链 Project → Requirement → RequirementVersion → RequirementItem 的稳定身份（`item_key`、`revision`、`baseline_version_id`、`brief_revision`）、固定 `section_key` 枚举、条目的来源 / 陈述类型 / 确认状态写入路径，以及 SourceArtifact 的哈希与定位契约。
- 明确 `finding_kind` 五类枚举、各自的目标与依据资格、阻断规则，以及 `decision_type` 五类枚举和活动 Decision 的替换规则。
- 明确四个持久状态、三个派生状态、批准门不变量、乐观修订号并发规则和“同一 Requirement 只有一个开放版本”的约束。
- 明确批准事务与事务后索引的边界：哪些在同一事务内，`index_state` 怎样暴露与重试，项目检索池与全局知识库怎样分别快照。
- 明确 Review API 的业务结果与错误分层，以及唯一 Web 工作台入口。
- 明确用户身份认证的最小生命周期，以及系统 admin / member 与项目 owner / editor / viewer 两层角色各自能看到的路由和能执行的动作；这条边界不与第二阶段 Tool 权限混用。
- 明确知识资料上传后的暂存与发布流程：谁能触发入库、诊断信息如何展示、哪一个动作才会产生新的 `dataset_version`。
- 明确生成阶段结构化增量流式的事件契约：模型流式调用怎样被增量解析为局部 Finding、“生成中未校验”与“已校验完成”两种状态怎样在 SSE 事件和界面上区分、校验失败时增量内容如何被撤回。
- 明确 DeliveryPackage 的导出前提、内容与哈希可验规则，以及草稿非正式预览的标记。
- 为第一次基线实验登记数据集、对照组、参数、指标、通过条件、成本和延迟预算。
- 确认不需要 Agent、Reranker、OCR、多模态平台、Flutter App 或其他第一阶段非目标。

某项真实依赖只有在对应正文、代码和运行入口一起落地时才加入；Definition of Ready 不授权创建空 package、空产品目录或占位配置。

## 本阶段新增结果

第一阶段需要跑通：

```text
Reference Knowledge + Historical Material
→ TXT / Markdown / DOCX / 文本型 PDF 加载与清洗
→ KnowledgeDocument / Chunk + Metadata
→ PostgreSQL 全文索引 + pgvector 向量索引（全局知识库，dataset_version）
已批准需求版本
→ 批准事务后索引进项目检索池（approved_requirement_version_ids）
Target Requirement
→ 导入为 SourceArtifact → 映射为 RequirementVersion 的 proposed 条目
固定表单
→ 人写条目（confirmed）→ 检索 → 固定生成补全草稿（proposed）
用户处理 proposed 条目（confirm_items / 删除）
→ 运行 ReviewRun（钉住需求修订、Brief 修订、dataset_version、可见已批准需求）
→ Lexical Retrieval + Dense Retrieval → RRF → Top-k / 阈值 / Metadata Filter → 候选证据与诊断
→ Context Construction
→ 真实 LLM 生成结构化 Finding
→ 应用校验 Citation 成员资格、支持性、证据充分性与按 finding_kind 的依据资格
→ Finding 挂到条目 / 分区 / 版本；证据不足时 evidence_gap 转成补充问题
→ 用户逐项 Decision（accept_suggestion / reject / waive / supplement）→ 改了内容就再评审
→ 最后一轮 Finding 只剩 reject / waive → editor 提交 → owner 批准（同一事务切换基线）
→ 新基线事务后索引 → 人工导出 DeliveryPackage
→ 从基线派生新版本 → 条目级 Diff → 重新评审
→ Review API 返回业务结果与诊断
→ 工作台展示需求正文、Finding、Decision、状态和真实失败
```

第一阶段的核心不是追求高级检索，而是让每一层都可以观察和替换，并让评审结果落进一条有身份、有状态、能批准和交付的对象链。

## 输入与输出契约

### 需求对象

产品的业务对象以 SPEC 第 4 节为准，项目篇只规定业务上必须表达的信息：

- `Project`：成员、SourceArtifact、Project Brief（`brief_revision` 单调递增，append-only 修订历史）。
- `Requirement`：一个可独立版本化、批准和交付的需求主题，持有 `baseline_version_id`。
- `RequirementVersion`：`derived_from_version_id`、只随内容变化递增的 `revision`、四个持久状态、批准时钉住的 `approved_brief_revision` 与 `approval_review_run_id`、批准后的 `index_state`。
- `RequirementItem`：`item_id`、跨版本稳定的 `item_key`、`section_key`、`provenance`（用户输入 / 导入 PRD / AI 建议 / 派生自旧版本）、`statement_kind`、`confirmation_state`、已验证 `citations` 与 `citation_state`。
- `SourceArtifact`：导入原文的文件名或来源标识、格式、内容哈希、版本与 locator 契约；导入条目保留 `source_artifact_id`、`source_locator`、`mapping_method`。

导入的 PRD 可以来自粘贴文本或上传文件，两种输入共享同一个 SourceArtifact 契约；导入本身不代表这份内容进入知识检索候选池。

### 知识候选

第一阶段中 Reference Knowledge 和 Historical Material 进入通用知识生产链；已批准需求版本在批准事务之后进入项目检索池。`KnowledgeDocument` 至少保留：

- 稳定 `document_id`。
- `document_version` 或内容版本。
- 原始文件名、格式和受控来源位置。
- `source_role`，至少区分 `reference_knowledge`、`historical_material` 与 `approved_requirement`。
- `evidence_eligibility` 或等价字段，说明该资料能否作为当前规则证据、只能作为历史参考或项目内已批准决定，还是不能进入 Citation Candidate。
- 内容哈希或其他可复现的变更标识。
- 解析状态和明确错误。

每个可检索 `Chunk` 至少保留：

- 稳定 `chunk_id` 和所属 `document_id` / `document_version`。
- 文档名称、文档类型和文本内容。
- 结构化 `locator`：按格式表达章节、页码、段落或字符范围，不把不同格式强行伪装成同一种定位。
- 用于 `knowledge_scope` 的业务 Metadata。
- Chunk 策略版本和必要的父块关系。

`document_id` 标识业务文档，`document_version` 标识内容版本，`chunk_id` 标识该版本下的稳定片段。重新入库同一内容应得到可预测的标识；内容或切分策略改变时必须能够区分新旧 Chunk，不能依赖数据库自增 ID 作为 Citation Candidate。已批准需求版本以 `requirement_version_id` 作为 `document_version` 身份进入项目检索池，ReviewRun 按 `approved_requirement_version_ids` 集合过滤可见版本，`superseded` 版本因不在集合内自然离开，不做角色重标。

### 评审运行与结论

一次 `ReviewRun` 至少表达：

- 运行身份，以及进入检索时钉住的证据快照：`requirement_version_id + revision`、`brief_revision`、`dataset_version`、`approved_requirement_version_ids`（只含 `indexed` 版本，排除本 Requirement 自身基线）与 `proposed_count_at_start`。
- 状态 `submitted → retrieving → generating_unverified → validating → completed | failed | cancelled`；`completed` 带 `evidence_decision`（可回答 / 部分回答 / 拒答）。
- 本轮检索到的来源候选和实际使用的证据。
- 生成过程中的增量结果与生成完成后经过完整校验的最终结果的明确区分标记。
- 模型、Prompt、Retriever、Token、延迟和错误等诊断，错误至少区分模型鉴权失败、限流、超时、能力不支持、结构化校验失败与用户取消；所有未进入本轮候选的项目内当前基线（`index_state=pending | index_failed`）连同不可见原因列入诊断。

每条 `Finding` 至少表达：`finding_kind`、严重度、`target_kind + target_ref`（属于该版本当时修订的条目、分区或版本本身）、说明、建议，以及按类型要求的依据——内部缺失 / 矛盾回到当前版本定位，外部事实冲突回到已校验 Citation，影响推断带推断标记，证据缺口转成用户可回答的问题。

每条 `Decision` 至少表达：`decision_type`、操作人、时间、理由、指向的 Finding（`confirm_items` 除外）、受影响的条目与 `active | deactivated` 状态。

`DeliveryPackage` 只从 `approved` / `superseded` 版本导出，按版本生成 Markdown 与 JSON，记录 `approved_brief_revision`、`compared_to_version_id`、导出人、时间、格式、内容哈希与成功 / 失败。

[可信生成](../../mechanisms/trusted-generation.md)先展示来源候选，并校验模型声明的来源是否属于本轮候选；Citation 支持性机制继续判断内容能否支持声明，证据充分性机制再决定 Refusal 和补充问题；产品层再按 `finding_kind` 校验依据资格与目标成员资格。项目验收不能把“模型写出了来源编号”当成证据已经支持结论；同样不能把“生成过程中出现的增量内容”当成已经校验的结论——校验失败时，增量内容必须从界面上被显式撤回，不能只是停止更新。

生成阶段使用真实模型流式接口，后端按 Finding 结构增量解析已完整字段并通过 SSE 推送为“生成中、未校验”状态，生成结束后再执行一次完整 Schema、Citation 与依据资格校验；这只是一次生成调用内部的增量渲染与最终校验边界，不是完整的 Agent Event 协议——没有多步骤循环、没有 Tool 调用事件、没有断线重连游标，SSE 连接断开时前端改用普通请求重新获取当前持久化状态即可。完整的 Agent Event 协议、断线重连和运行轨迹留给第二阶段。

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
- 区分条目来源、外部 Citation 与人的 Decision 三种不同的权威来源，解释为什么产品意图不因缺 Citation 被拒绝、外部事实不因人的确认而免除 Citation。
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
→ 校验
→ 由人决策
```

模型不需要动态选择下一步，也不替人做任何状态迁移，因此暂不使用 Agent。

### 2. 第一版支持哪些知识资料

第一阶段的 Reference Knowledge 与 Historical Material 必须支持 TXT、Markdown、DOCX 和带文本层的 PDF，并保留文档、章节、页码或段落位置。Target Requirement 通过导入入口成为 SourceArtifact 与条目，不靠重复入库来满足格式数量。允许先覆盖项目固定资料中实际出现的 DOCX 和 PDF 结构，不要求建设通用 Office 解析平台。

扫描 PDF、复杂版面、表格语义、图片 OCR/VLM、音频 ASR 和视频理解进入扩展概念或机制实验，不阻塞第一阶段产品链路。

### 3. 怎样比较检索

至少保留三类问题：

- 词面一致的问题。
- 同义改写的问题。
- 精确接口名、状态码或枚举问题。

先用 PostgreSQL FTS 建立可解释的 Lexical Retrieval，再使用真实 Embedding 服务和 pgvector 建立 Dense Retrieval，最后在应用层用 RRF 融合两路排名。第一阶段必须在同一组样例上比较 lexical、dense 和 RRF 三条检索路径。

RRF 只融合名次，不假装不同检索器的原始分数可以直接相加。Reranker 会增加模型调用、延迟和调试面，保留为扩展机制；只有评估证明收益大于复杂度时才进入产品默认链路。

第一阶段的检索参数遵守下面的固定语义：

1. `knowledge_scope`、`source_role`、`dataset_version`、`approved_requirement_version_ids` 与 Metadata Filter 在 lexical 和 dense 两路检索前应用，保证两路候选来自同一可见文档池，并防止当前需求版本或其自身基线无说明地进入参考知识检索。
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
- Reference Knowledge、Historical Material 与 Approved Requirement 的分区、证据资格和优先级。
- 当前需求版本的条目怎样作为被评审对象进入 Context，而不进入 Evidence 分区。
- 没有候选材料时的行为。

### 5. 哪些信息进入产品输出

业务结果和工程诊断必须分开。用户看到需求正文、Finding 与 Decision，学习和调试入口还能看到检索候选、最终上下文、模型信息、Token、延迟和错误。

### 6. 唯一前端入口

第一阶段只建设一个 Web 工作台，不建设 Flutter App，也不在 `source/apps/` 维护第二份产品页面。工作台以需求正文为中心：项目列表 → 需求列表 → 需求工作区（左侧版本与条目导航；中间分区表单式结构化正文；右侧评审面板与决策面板；顶部运行评审 / 提交 / 批准 / 导出动作；诊断放抽屉）。知识管理视图仅系统 admin 可见，支持上传知识资料、查看解析诊断、暂存与发布。这是一个真实但克制的最小工作台——不做可配置审批链、通知或跨版本知识治理平台，但也不能只是能跑的脚本外壳。

### 7. 需求对象模型与基线

Requirement 是稳定容器，RequirementVersion 是内容快照，RequirementItem 是最小单位。基线只在 Requirement 粒度（`baseline_version_id`），全产品基线是非目标。条目的 `item_key` 跨版本稳定，使派生版本能按条目对齐 Diff 并回查历史 Finding 与 Decision。`revision` 只随内容变化递增，是乐观并发控制与“旧评审是否仍可用于批准”的唯一判据。必须解释：为什么 Project Brief 是 Project 上的字段集合而不是一个特殊 Requirement，为什么 Brief 修订历史必须 append-only。

### 8. 来源、引用与决策三分

`external_fact` 只能由系统赋予（AI 草稿携带已校验 Citation，或 `accept_suggestion` 写回）；导入映射和人写默认 `product_intent`；人只能降级不能升级，编辑正文自动降级。人写和原样派生的条目创建即 `confirmed`，AI 生成和导入映射的条目是 `proposed`。必须能解释：如果允许导入器产生 `external_fact`，或允许人把条目标成 `external_fact`，批准门会出现什么死锁。

### 9. 批准门与两步人工门

四个持久状态 `draft / pending_approval / approved / superseded`，每个迁移都由人触发；“评审中”“待补充”“已交付”是派生展示状态。批准门在提交时预检、批准时复检：门禁运行必须是当前 `revision` 上最近一次 `completed` 且 `brief_revision` 匹配的 ReviewRun，`proposed_count_at_start=0`，其全部 Finding 的活动 Decision 只能是 `reject` / `waive`。Decision 只在 `draft` 可创建或替换，提交后只读，批准时把活动 Decision 集合冻结为 `approved_decision_ids` 与 `approved_decision_set_hash`，DeliveryPackage 固定使用 IDs 并校验哈希——否则批准后改一条 `reject` 为 `waive`，导出的交付包就与 owner 批准时看到的不是同一份。Brief 修改使待批准版本过期后必须先退回 `draft`，再重新评审、处理 Finding 并提交。必须解释为什么 `accept_suggestion` / `supplement` 递增 `revision` 就自然逼出“最后一轮零内容变更”，循环因此有限收敛。

### 10. 两层角色边界

系统 admin / member 与项目 owner / editor / viewer 两层，权限取交集；系统 admin 不因系统角色获得项目批准权。批准、退回、编辑 Brief、管理成员归 owner；创建需求、编辑草稿、运行评审、处理 Finding、提交批准、导出归 editor 及以上。其中提交批准、退回 / 撤回、批准、正式导出、成员管理、编辑 Brief 六类动作只能由人触发。这里的角色只回答产品界面上谁能点什么，是产品 RBAC，不是第二阶段 Tool 权限（模型能执行什么）；两者概念独立，不能相互替代或合并实现。

### 11. 两个检索池与事务后索引

全局知识库以 `dataset_version` 为快照身份，由系统 admin 发布；项目检索池以 `approved_requirement_version_ids` 为快照身份，由批准事务之后的独立索引步骤维护。批准事务只写数据库（基线切换、`superseded`、审计），索引失败真实暴露为 `index_failed`、可重试、不回滚批准。必须解释：为什么不把索引放进批准事务，为什么派生版本评审时排除自身基线而交给 Diff。

### 12. 知识资料的暂存与发布

系统 admin 上传的知识资料先进入暂存状态，只有明确的发布动作才会产生新的 `dataset_version` 并改变全局知识库候选池；上传和暂存本身不生效。这条规则是为了保护 Golden Set 的冻结纪律——不能因为一次误传就悄悄改变已经冻结的验收基线。发布记录必须保留谁在什么时候发布了哪些文档，形成可追溯的版本历史。“发布产生 `dataset_version`”只约束全局知识库，不约束项目检索池。

### 13. 生成阶段的结构化增量流式

评审生成调用真实模型的流式接口，后端边接收 token 边做增量 JSON 解析，按 Finding 结构提取已经完整的字段并通过 SSE 推送给前端，标记为“生成中、未校验”；生成结束后再执行一次完整的 Schema、Citation 与依据资格校验，前端用“已校验”的最终结果替换之前的增量展示。若最终校验失败，前端必须显式撤回增量内容。这套流式契约只服务于一次生成调用，不引入 Tool 事件、多步骤循环或断线重连游标，与第二阶段完整的 Agent Event 协议保持边界。

## 代码职责

### `source/packages/rag_core/`

负责通用能力：

- 文档和 Chunk 数据类型。
- Loader / Cleaning。
- Chunking / Metadata。
- PostgreSQL FTS 与 pgvector 适配。
- Lexical、Dense 与 RRF Retriever。
- Top-k、阈值、Metadata Filter（含按 `document_version` 集合过滤）与检索诊断。
- RAG Context Construction。
- 固定 RAG Pipeline。
- Citation Candidate 成员资格、Citation 支持性、证据充分性、Refusal 和补充问题的通用校验能力。

`rag_core` 不承载 Finding、Decision 或任何需求对象；`SourceRole` 增加 `approved_requirement` 是唯一的领域相关枚举扩展。

### `source/apps/review_assistant/`

负责产品组合：

- 固定 Target Requirement、Reference Knowledge 与 Historical Material fixtures。
- 需求领域 Schema 与 migration：Project、Brief 修订历史、Requirement、RequirementVersion、RequirementItem、SourceArtifact、ReviewRun、Finding、Decision、DeliveryPackage，以及状态机与批准门。
- 结构化需求草稿生成：固定表单补全与导入 PRD 到条目的映射及未映射诊断（第二个 Prompt 族）。
- Finding 目标成员资格与按 `finding_kind` 的依据资格校验；`external_fact` 赋予规则；乐观并发控制。
- 批准事务、事务后索引与 `index_state`；ReviewRun 证据快照。
- 身份认证、会话生命周期，以及两层角色的路由与动作边界。
- 知识管理后台：知识资料上传、解析诊断展示、入库暂存、系统 admin 发布与 `dataset_version` 记录。
- FastAPI Review API 与结构化错误契约，包含结构化增量流式与最终校验的 SSE 事件契约。
- DeliveryPackage 导出与草稿非正式预览。
- 最小 AI Native Web 工作台，以需求正文与决策为中心。
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
- 认证所需的会话密钥等环境变量，以及初始系统 admin 账号的建立方式。
- 资料入库、启动 API、启动 Web、运行测试和运行评估的唯一主命令。
- 第一阶段验收时起，用 Docker Compose 启动应用与 Postgres/pgvector 两个服务的命令；Redis 只在真实异步任务需求出现后才加入。
- 本地输出、运行记录和敏感配置的保存边界。

这些选择是产品运行事实，不在项目篇长期固定供应商、库版本或秘密配置。实现发生变化时更新产品 README 和锁文件，项目篇只维护必须可运行、可诊断和可重建的契约。

## 分段实现顺序

第一阶段的范围必须按纵向切片推进，每一段都留下可观察结果，再进入下一段：

1. **契约与资料**：固定 fixtures，完成 Target Requirement 与知识资料的身份边界，以及 `KnowledgeDocument` / `Chunk` / locator / Metadata 契约和 TXT、Markdown、DOCX、文本型 PDF 的解析对照。
2. **Lexical 基线**：先让 PostgreSQL FTS 单路检索可运行，记录词项命中、原生 rank、阈值和过滤诊断。
3. **Dense 基线**：接入真实 Embedding 与 pgvector，固定 Provider、配置、模型、维度和预处理版本，记录相似度方向、索引和单路失败。
4. **RRF 融合**：在两路结果之上实现应用侧 rank fusion、去重、`rrf_k`、`final_top_k` 和完整诊断。
5. **Context 与生成**：将 RetrievalResult 交给已有 Context Builder 和真实结构化 LLM，验证真实模型的流式接口、增量 JSON 解析与最终校验的边界，区分检索、上下文、生成和 Schema 失败。
6. **Citation 支持性与证据充分性**：在成员资格之上建立支持性校验与充分性判定，把缺口转成结构化补充问题。
7. **需求对象模型与状态机**：落地领域 Schema、migration、四个持久状态、`revision`、`item_key`、SourceArtifact 与 Brief 修订历史；由脚本和确定性测试驱动，早于 API 与认证。进入本段前先完成通用机制与领域 Schema 的职责对齐。
8. **结构化需求草稿**：固定表单补全与导入 PRD 映射，验证来源、`proposed` 状态、`external_fact` 只由系统赋予、未映射诊断。
9. **Finding 定位与 Decision**：把评审结果落为带目标与依据资格的 Finding，实现五类 Decision、活动 Decision 替换、`confirm_items`、条目级 Diff 与批准门预检。
10. **身份认证与两层角色**：建立登录、会话生命周期，以及系统与项目两层角色的路由与动作边界。
11. **版本生命周期、批准与交付**：提交、退回、批准事务、基线切换、事务后索引与 `index_state`、项目检索池、DeliveryPackage 导出与非正式预览。
12. **Review API 与 Web**：组合唯一产品入口，完成 ReviewRun 状态、证据快照、结构化增量流式与最终校验的 SSE 事件契约、需求工作区、评审与决策面板、真实错误展示；接入知识管理视图（上传、暂存、发布）。
13. **评估与验收**：运行四路对照、真实 bad case / 策略边界、需求变更和实验前登记的质量门槛，形成第一阶段运行记录。
14. **环境打包**：用 Docker Compose 固定应用与 Postgres/pgvector 的本地运行环境，作为阶段验收的可复现环境收尾。

某一段暂时失败时，优先修复该段的契约或诊断，不通过增加新框架或跳过前置段落推进。

## 数据流、状态流与异常流

### 数据流

```text
Reference Knowledge + Historical Material
→ KnowledgeDocument → Chunk → PostgreSQL FTS / pgvector（全局知识库）
已批准 RequirementVersion
→ Chunk → 项目检索池（approved_requirement）
                                      ↓
RequirementVersion（当前修订）→ ReviewRun 快照 → Lexical + Dense → RRF → RetrievalResult
                  │                                                       ↓
                  └────────────── 被评审对象 ──────────────→ ReviewContext → Finding
                                                                          ↓
                                                    Decision → 条目变化（revision+1）→ 再评审
                                                                          ↓
                                            批准（基线切换）→ 事务后索引 → DeliveryPackage
```

每次转换必须能保留来源关系，不能到模型输出时才临时猜测来源。当前需求版本是评审主体，不因进入 ReviewContext 就成为 Citation Candidate；只有满足证据资格的知识来源与已批准需求才能进入候选引用。

### 状态流

三个独立状态机加派生状态，不写第四套生命周期：

- **版本持久态**：`draft → pending_approval → approved → superseded`，`pending_approval → draft` 由 owner 退回或撤回；每个迁移由人触发。内容写入与 Decision 写入都只在 `draft` 允许。派生展示状态“评审中”（存在活跃 ReviewRun）、“待补充”（门禁运行存在未处理的 `evidence_gap` / `internal_gap`）、“已交付”（存在成功 DeliveryPackage）由查询得出。
- **ReviewRun**：`submitted → retrieving → generating_unverified → validating → completed | failed | cancelled`；`completed` 带 `evidence_decision`；失败不改变版本状态；一个版本可跑多次；SSE 连接断开是传输层事件，不改变任何业务状态。
- **已批准版本索引**：`pending → indexed | index_failed`，`index_failed` 可重试，只影响该版本能否作为 `approved_requirement` 被检索。

DeliveryPackage 是导出记录（成功 / 失败、哈希、导出人），不是独立生命周期。知识资料侧仍要区分：上传成功、解析诊断可用、暂存中、已发布（产生新 `dataset_version`）。

### 异常流

至少区分：

- 文档加载失败。
- 没有生成有效 Chunk。
- Embedding 或索引失败（含已批准版本 `index_failed`）。
- Lexical 或 Dense 单路检索失败。
- RRF 候选无法通过稳定 Chunk ID 合并。
- 检索无结果。
- 候选全部被阈值或 Metadata Filter 淘汰。
- Context 超出预算。
- 模型鉴权、限流、超时或能力不支持。
- Structured Output 校验失败。
- Finding 目标不属于当前修订，或依据资格不满足（`external_fact_conflict` 缺 Citation）。
- 基于旧 `revision` 的写入被拒绝；`pending_approval` 或活跃 ReviewRun 期间的写入被拒绝；非 `draft` 状态下创建或替换 Decision 被拒绝。
- 批准门预检 / 复检失败：过期运行、未处理 Finding、`proposed` 条目、过期 Brief。
- 导入原文哈希变化后旧映射不能沿用。

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
10. 当前需求版本或其自身基线被错误加入参考知识候选，导致检索和评估泄漏。
11. Historical Material 与当前规则冲突，却因未标明历史角色覆盖现行证据。
12. 已批准需求与现行业务规则冲突，模型把 `approved_requirement` 当成更高资格的规则。
13. 导入映射把 PRD 中的一句陈述误标为需要 Citation 的外部事实，或模型把产品意图当成缺证据的事实拒绝。
14. 用户先评审再确认 `proposed` 条目，门禁运行 `proposed_count_at_start>0` 无法批准。
15. 缺少真实模型 API key。
16. 模型返回不符合 Schema 的结果。

这些现象不要求通过损坏实现或凭空构造异常获得。每个被选作验收证据的现象都要记录：

- 表现。
- 可能原因。
- 如何验证。
- 应修改数据、Retriever、Context、Prompt、Schema、状态规则还是模型配置。

## 需求变更题

在第一阶段主链跑通后，完成一次真实变更：

> 为 `impact_inference` Finding 新增“影响范围”字段，要求标明影响 Web、Flutter、服务端还是多端共同修改，并让 DeliveryPackage 按影响范围汇总。

需要判断：

- 修改业务 Schema 与 migration 的位置。
- Prompt 如何同步。
- 依据资格校验是否受影响。
- 哪些评估样例需要更新。
- UI 与交付包如何展示。
- 旧 ReviewRun 与旧 DeliveryPackage 如何兼容或明确不兼容。

## 评估与通过条件

### 固定评估数据

第一阶段使用版本化的小型固定数据集。每个 Case 至少记录：

- `case_id`、问题和所属问题类型。
- 被评审的 `requirement_id`、`requirement_version_id` 与 `revision`（由导入 Target Requirement fixture 得到的固定版本）。
- `split`，取值为用于开发诊断和调参的 `development`，或只用于阶段验收的 `acceptance`。
- `dataset_version`、允许的 `knowledge_scope` 与 `approved_requirement_version_ids`。
- 期望命中的 `document_id` / `chunk_id` 或可验证来源范围。
- 不应命中的来源。
- 期望覆盖的 `finding_kind` 与目标。
- 是否应该明确表示证据不足。

`development` Case 用于观察失败、选择 Chunk 策略和调整 Retriever 参数；`acceptance` Case 在首次验收运行前冻结，不能用于选择参数。两部分都至少覆盖词面一致、同义改写、精确接口名或枚举、无答案、噪声相似和 Metadata Filter 六类问题，每类至少有一个稳定 Case；另至少一个 Case 的期望来源落在同项目“订单状态展示”已批准基线上，用于验证 `approved_requirement` 池确实可检索并能支撑 `external_fact_conflict`。Reference Knowledge 与 Historical Material 至少各有明确角色，知识资料格式至少各有一个可重复解析的 TXT 或 Markdown、DOCX 和文本型 PDF fixture。另加需求草稿引用正确性样例：固定表单补全与导入映射产生的条目，其来源、`proposed` 状态与 `external_fact` 归属可确定性验证。

样例数量可以增长，但删除、改写或改变 Case 的 split 必须提升 `dataset_version` 并说明原因。验收失败后可以保留失败记录并创建新实验，但不能根据 acceptance 结果删除 Case、降低门槛或把 Case 移入 development；若要改变验收集，必须发布新的数据集版本，并把原结果保留为历史证据。第一阶段只建立小型基线，完整数据集治理和评估平台保留为后续质量收束或扩展能力。

### 对照路径

至少比较：

- 直接 LLM。
- PostgreSQL FTS Lexical RAG。
- 使用真实 Embedding 和 pgvector 的 Dense RAG。
- 使用 RRF 多路召回的 RAG。

四条路径使用相同输入、数据集版本、生成模型、Prompt、Schema 和输出预算，对照物是 ReviewRun 的已校验 Finding 与 `evidence_decision`。检索策略是主要变量；若必须改变其他变量，应建立新的实验而不是混入当前比较。

### 指标契约

| 维度 | 第一阶段必须记录 | 能证明什么 |
| --- | --- | --- |
| 解析 | 文件成功/失败、文档与 Chunk 数、来源角色、证据资格和定位完整性 | 参考与历史资料能否稳定进入知识系统且不混淆角色 |
| Retrieval | 每路与融合后的 Source Hit@k、Source Recall@k、MRR@k、禁止来源命中、无结果原因 | 是否命中、是否覆盖完整及排序是否改善 |
| Generation | Schema 结果、`finding_kind` 覆盖、无依据结论、证据不足行为 | 检索结果是否转化为更可靠的评审结果 |
| 工程 | 成功/失败层级、Token、成本、各阶段耗时和总延迟 | 改进是否付出不可接受的工程代价 |

每个 Case 必须在运行前确定相关性判断单位是 `document_id`、`chunk_id` 还是可验证来源范围，运行后不能为了提高结果更换单位。第一阶段使用以下定义：

- Source Hit@k：期望来源集合中至少有一个来源出现在前 `k` 个结果中，命中记为 `1`，否则为 `0`。
- Source Recall@k：前 `k` 个结果命中的期望来源数除以该 Case 的全部期望来源数。
- MRR@k：前 `k` 个结果中第一个期望来源排名的倒数；没有期望来源时记为 `0`。

无答案 Case 的期望来源集合为空，Hit@k、Recall@k 和 MRR@k 记为 `N/A`，不混入有答案 Case 的均值；它通过禁止来源命中、无结果原因、证据不足行为和无依据结论单独验收。汇总时至少同时保留 Case 结果、问题类型的宏平均和整体宏平均，不能用高频类别掩盖弱项。禁止来源命中也必须独立记录，不能被总体 Hit 或 Recall 抵消。Finding 覆盖和无依据结论需要保存 Case 级判断依据。

第一阶段不使用“感觉更好”作为指标，也不要求 RRF 在每个 Case 都排名第一。人工判断 Finding 覆盖或无依据结论时，必须保存判断依据，不能只保留总分。

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
4. 每条声称依赖外部事实的 Finding 都能回到经过应用校验的 Citation；证据不足时进入 Refusal 或 `evidence_gap` 补充问题，而不是生成无依据结论。
5. RRF 在冻结的 acceptance Case 上达到实验前按问题类型登记的 Source Hit@k / Recall@k 最低门槛；无答案 Case 按独立门槛验收，不参与这些指标的平均。
6. 在相同 `final_top_k` 下，RRF 至少在一种已登记的 lexical 或 dense 单路弱项问题中恢复期望来源，证明两路召回具有互补价值；第一阶段小型数据集不要求 RRF 的整体均值机械高于每个单路基线。
7. RRF 的禁止来源命中和无依据结论不超过实验前登记的上限；成本和延迟不超过实验前登记的第一阶段预算。lexical、dense 与 RRF 的分类结果仍必须并列保存，不能只报告融合结果。
8. 若第 4–7 项不满足，第一阶段不能宣称可信混合检索基线成立。应在 development Case 上调整数据、Chunk、阈值、证据策略或融合配置并创建新实验，保留失败的 acceptance 记录，而不是删除验收 Case、降低原实验标准或用新的总体均值掩盖分类弱项。

这里验收的是可重复的产品基线，不是完整评估平台。自动评审、实验管理、反馈和质量工作台在第二阶段质量收束或扩展能力中进入。

## 范围冻结与变更规则

Definition of Ready 完成后，第一阶段主路径默认冻结：

- 只有缺少某项能力会使第一阶段输入、输出、可信性、可用性或验收契约不成立，或者现有内容无法解释已复现的阻塞失败时，才允许增加第一阶段主线知识。
- 新框架、数据库、模型或平台功能本身不是扩展理由；优先合并进现有机制，或按分级准入进入概念、机制和未来认知。
- 改变支持格式、检索路线、产品入口、对象模型、状态规则或产品验收要求时，先更新根 `SPEC.md`；改变稳定工程分解时更新 `PLAN.md`，随后再实现代码并提升受影响的数据集或实验版本。
- 实现中的任务拆分、实时进度和运行结果不写回 `course/learning-path.md`；它们进入代码、产品 README、测试、eval 配置和运行记录。

## 明确不做

- Query Rewrite 和 Source Routing。
- Retriever as Tool。
- Agent Loop；接收模糊想法并动态追问；Agent 驱动的变更影响分析。
- Workflow、Checkpoint 和 Human-in-the-loop 节点（第一阶段的人工批准是普通的产品动作，不是图中的 Interrupt）。
- Multi-Agent。
- 可配置的多级审批链、审批委托与通知；第一阶段只有固定的“提交 → 批准”两步人工门。
- 两层之外的权限模型、多租户和通用连接器。
- 全产品基线、Requirement 归档 / 下线、项目自定义分区、独立的 Brief 版本界面、被替代版本作为历史材料参与检索。
- 完整 Citation 运营后台、跨版本知识治理和自动化证据标注平台。
- Reranker 进入产品默认链路。
- 完整的 Agent Event 协议：心跳、断线重连游标、Tool 事件和多步骤运行轨迹留给第二阶段；第一阶段的 SSE 只服务于一次生成调用的阶段状态和结构化增量。
- Redis 或后台任务队列：知识资料的暂存/发布与已批准版本索引先用数据库状态字段和 FastAPI 自带的后台任务承担，只有真实异步阻塞场景出现才引入。
- GraphRAG、RAPTOR、Neo4j 和复杂 OCR / 多模态解析平台。

这些能力只有在第二阶段或扩展机制解决真实问题时进入。

## 完成标准

- [ ] 使用固定 Target Requirement、Reference Knowledge 和 Historical Material 跑通完整 RAG 数据流。
- [ ] 当前需求版本作为评审主体进入 Context，不会无说明地进入参考知识候选或成为 Citation Candidate；派生版本评审时不检索自身基线。
- [ ] TXT 或 Markdown、DOCX 和文本型 PDF 知识资料都能进入同一 Document / Chunk 契约并保留来源角色与位置。
- [ ] 主路径调用真实 Embedding 和真实 LLM；失败不降级 Mock。
- [ ] 使用 PostgreSQL FTS、pgvector 和应用侧 RRF 完成 lexical、dense 与多路融合召回。
- [ ] 能看到 Chunk、Metadata、每路排名、融合排名、Top-k、阈值、过滤结果和最终上下文。
- [ ] 输出通过本地业务 Schema 校验。
- [ ] 外部事实 Finding 能回到经过应用校验的 Citation；内部缺失 / 矛盾 Finding 回到当前版本定位且不伪造 Citation；证据不足时 Refusal 或 `evidence_gap` 补充问题。
- [ ] 导入 PRD 后条目覆盖与未映射内容可见，导入条目能回到 SourceArtifact 的哈希与原文定位；固定表单创建的人写条目创建即 `confirmed`，AI 补全条目为 `proposed`。
- [ ] 导入映射与人的直接输入永不产生 `external_fact`；人只能降级不能升级；编辑 `external_fact` 正文自动降级并清空 Citation。
- [ ] 五类 Decision 按规则生效：`confirm_items` 不指向 Finding、不递增 `revision`；`accept_suggestion` / `supplement` 递增 `revision` 并使当前运行失去批准资格；活动 Decision 可替换且旧记录 `deactivated` 可查；目标已删除的 Finding 只允许 `reject` / `waive`。
- [ ] 批准门在提交与批准时用同一规则拒绝过期运行、未处理 Finding、`proposed` 条目、过期 Brief，`proposed_count_at_start` 必须为 0；批准记录能回到对应 ReviewRun、`approved_decision_ids` 与 `approved_decision_set_hash`；Brief 修改使待批准版本过期后必须先退回草稿。
- [ ] 非 `draft` 状态下创建或替换 Decision 被拒绝；DeliveryPackage 使用的决策集合与 `approved_decision_ids`、`approved_decision_set_hash` 一致。
- [ ] 批准在同一事务内切换 `baseline_version_id` 并把旧基线置为 `superseded`；索引失败时 `index_state=index_failed`、可重试、不回滚批准；同一 Requirement 存在开放版本时派生被拒绝。
- [ ] ReviewRun 钉住 `requirement_version_id + revision`、`brief_revision`、`dataset_version` 与 `approved_requirement_version_ids`，`superseded` 版本不出现在新运行的项目池候选中，`pending` 与 `index_failed` 版本都列入诊断并标明原因；同项目“订单状态展示”基线能被检索到并支撑至少一条 `external_fact_conflict`。
- [ ] 乐观修订号拒绝基于旧 `revision` 的写入；`pending_approval` 与活跃 ReviewRun 期间拒绝内容写入；Brief 修订历史 append-only 且可取回。
- [ ] DeliveryPackage 只从 `approved` / `superseded` 版本导出，与钉住的版本和 `approved_brief_revision` 哈希一致；草稿只能生成带标记的非正式预览。
- [ ] 条目级 Diff 能按 `item_key` 对齐并给出原因；历史 Finding 与 Decision 可按 `item_key` 回查，不自动迁移。
- [ ] 直接 LLM、Lexical RAG、Dense RAG 和 RRF RAG 使用同一组样例比较，对照物是已校验 Finding 与 `evidence_decision`。
- [ ] 能区分检索失败、上下文失败、生成失败与状态规则拒绝。
- [ ] 至少完成一个真实 bad case / 策略边界观察和一个需求变更。
- [ ] 有最小固定评估样例和运行记录。
- [ ] 通用能力只存在于唯一 `rag_core`，需求领域 Schema 与 Prompt 留在产品层。
- [ ] 产品入口位于 `source/apps/review_assistant/`，没有在 `source/apps/` 维护第二份产品。
- [ ] 工作台能创建 / 导入需求、展示结构化正文、Finding、Decision、Citation、补充问题、版本状态与真实失败，并能提交、批准、导出。
- [ ] 用户能够登录，两层角色的可见路由和可执行动作有明确边界，系统 admin 不能仅凭系统角色批准项目需求，且这条边界没有与第二阶段 Tool 权限混用。
- [ ] 系统 admin 能够上传知识资料、查看解析诊断，并通过独立的发布动作产生新的 `dataset_version`；上传和暂存本身不改变检索候选池。
- [ ] 评审生成阶段有结构化增量流式展示，生成完成后的最终校验结果能够清晰替换未校验的增量内容；校验失败时增量内容被显式撤回。
- [ ] 能对模型调用失败（鉴权、限流、超时、能力不支持）与结构化校验失败分别给出可定位错误，并通过统一 SSE 事件契约呈现。
- [ ] 本地可以用 Docker Compose 一次性启动应用与 Postgres/pgvector 两个服务。
- [ ] 能解释为什么第一阶段不需要 Agent，以及第二阶段 Agent 将怎样复用同一写入路径与批准门。

达到这些标准后，固定 RAG 与需求对象模型已具备进入第二阶段 Agent Harness、Retriever as Tool 与 `propose_requirement_patch` / `apply_requirement_patch` 的稳定契约。
