# 需求评审助手产品规格

本文是需求评审助手“必须做什么”的唯一产品规格。课程项目篇引用本文开展综合实践，但不复制完整产品契约；真实 API、Schema、状态和错误以产品代码及测试为精确执行真源。

## 1. 产品目标

需求评审助手是以需求基线为核心的需求定义、评审与交付工作台。它接收对需求的结构化输入、已有 PRD 或对已有需求的变更，结合内部业务规则、历史资料和项目内已批准的需求，把输入收敛为结构化、可追溯、经过逐项决策、可批准、可版本化的需求基线，并导出人和 Agent 都能读懂的需求交付包。

评审贯穿整个过程，不是一次性的报告：系统找出需求内部的缺失与矛盾、与外部规则或已批准需求的冲突以及研发影响，每一条结论都要回到可定位的依据；证据不足时拒绝强事实结论并转成用户可回答的问题，但不拒绝由人明确做出的产品选择。

产品分为两个连续阶段：

- 第一阶段用固定 RAG 建立完整闭环。输入只有固定表单和导入 PRD；所有状态迁移由人的显式动作触发。
- 第二阶段在同一对象模型上增加 Agent、Tools、Deep Research 与 Multi-Agent。Agent 接收模糊想法、追问缺失信息、在用户裁决下推动需求收敛，并在迭代时分析变更影响。

阶段不是产品版本，代码只维护一条演进主线。核心对象、身份、来源与状态见第 4 节。

## 2. 用户与核心任务

主要用户是需要定义、评审和交付需求的产品与研发人员，评审重点是规则冲突、遗漏、歧义与 Web / Flutter / 服务端影响。产品区分两层角色：

- 系统级：`admin` 与 `member`。系统 `member` 可以创建项目，创建后成为该项目的 `owner`；系统 `admin` 额外负责维护全局知识资料。
- 项目级：`owner`、`editor` 与 `viewer`。

权限取两层交集：系统 `admin` 不因系统角色自动获得任何项目的批准、导出或成员管理权，必须先成为项目成员。这是产品内的最小权限边界，回答“界面上谁能点什么”，不是第二阶段 Tool 权限（模型能执行什么）的替代或前置。批准、导出、成员管理和编辑 Project Brief 只能由人触发；Agent 以发起者的项目角色行动，没有独立角色，即使发起者是 `owner` 也不能代替人触发上述动作。

核心任务包括：

- 把固定表单输入或已有 PRD 收敛为结构化、可追溯的需求条目，并区分人写、导入、AI 建议与派生自旧版本的来源。
- 找出需求中的内部缺失与矛盾、与现行业务规则或项目内已批准需求的冲突、歧义和多端影响。
- 给出能够回到原始资料或当前需求位置的依据。
- 证据不足时拒绝强结论并提出具体补充问题。
- 逐项处理评审结论，形成可审计、可替换的决策记录，并按条目追踪版本差异。
- 由人工批准版本成为基线，从不可变基线导出交付包，并从基线派生新版本继续迭代。
- 在复杂任务中搜索外部资料、调用受治理工具并保留过程（第二阶段）。
- 在多角色评审中保留分歧、证据归属和最终裁决（第二阶段）。
- 系统管理员上传、审核解析结果并发布新的知识资料版本，同一操作必须留下可追溯的版本记录。

动作矩阵：

| 动作 | viewer | editor | owner | 系统 admin |
| --- | --- | --- | --- | --- |
| 查看项目、需求、版本、Finding、Decision、诊断 | 是 | 是 | 是 | 仅在成为项目成员后 |
| 创建 Requirement、导入 PRD | 否 | 是 | 是 | 按项目角色 |
| 编辑草稿、派生版本、确认 `proposed` 条目 | 否 | 是 | 是 | 按项目角色 |
| 运行评审、取消自己发起的 ReviewRun | 否 | 是 | 是 | 按项目角色 |
| 取消任何 ReviewRun | 否 | 否 | 是 | 按项目角色 |
| 处理 Finding，形成 Decision | 否 | 是 | 是 | 按项目角色 |
| 提交批准（`draft → pending_approval`） | 否 | 是 | 是 | 按项目角色 |
| 退回 / 撤回（`pending_approval → draft`） | 否 | 否 | 是 | 按项目角色 |
| 批准版本 | 否 | 否 | 是，且必须由人触发 | 不因系统 admin 身份自动获得 |
| 编辑 Project Brief | 否 | 否 | 是，且必须由人触发 | 不因系统 admin 身份自动获得 |
| 导出 `approved` / `superseded` 版本 | 否 | 是，且必须由人触发 | 是，且必须由人触发 | 按项目角色 |
| 生成草稿的非正式预览 | 否 | 是 | 是 | 按项目角色 |
| 管理项目成员 | 否 | 否 | 是，且必须由人触发 | 不因系统 admin 身份自动获得 |
| 重试已批准版本索引 | 否 | 是 | 是 | 按项目角色 |
| 管理全局知识资料 | 否 | 否 | 否 | 是 |

编辑 Brief 限 `owner`，因为它会让项目内所有待批准的评审失去资格。权限判断在后端路由与动作层同时执行，前端隐藏按钮不是授权依据。

## 3. 输入与输出

### 输入

- 用户登录身份、系统角色与项目角色。
- Project Brief：项目上的独立字段集合，由 `owner` 维护；每次修订单调递增并保留 append-only 历史。
- 从零创建需求：固定表单与固定步骤填写的结构化条目，不是对话式 Agent。
- 导入 PRD：粘贴文本或上传 TXT、Markdown、DOCX、文本型 PDF；原文保存为 SourceArtifact，并映射为需求条目。
- 人的动作：确认 `proposed` 条目、对 Finding 做 Decision、提交批准、退回、批准、派生新版本、导出。
- 系统管理员上传的 Reference Knowledge、Historical Material 文件（同样限定为 TXT、Markdown、DOCX、文本型 PDF），以及触发入库、暂存和发布的管理操作。
- 业务范围、资料角色和证据资格等检索约束。
- 第二阶段：模糊想法与对追问的回答、会话上下文、工具权限、预算、人工确认和受控评审工作区（PRD、会议纪要、OpenAPI / JSON Schema、客户端模型、JSON / YAML 配置和项目已有的验证入口）。
- 用户明确确认保存的跨会话偏好，以及查看、更新、删除或关闭长期偏好记忆的控制请求。

第一阶段不接收模糊想法；接收模糊想法并动态追问是第二阶段能力。

### 输出

- 结构化需求版本：固定分区、条目、来源、陈述类型、确认状态、已验证 Citation 与修订号。
- 导入诊断：条目覆盖、每条导入条目到原文的定位、未映射内容。
- ReviewRun 结果：按类型与严重度组织的 Finding，每条挂在条目、分区或版本上并带可定位依据；Sources 与 Citation；证据充分性状态；Refusal 或可回答的补充问题。
- 生成过程中的增量结果与经过完整校验的最终结果之间的明确区分标记。
- Decision 记录、每条 Decision 影响的条目，以及按条目对齐的版本差异。
- 版本持久状态与派生展示状态、当前基线指针、已批准版本的索引状态。
- DeliveryPackage：按版本生成的 Markdown 与 JSON，包含钉住的 Project Brief 修订、相对上一基线的差异、决策、验收条件和证据；草稿只能生成明确标记为“非正式预览”的导出。
- 运行状态、停止原因和真实错误，第一阶段至少区分模型鉴权失败、限流、超时、能力不支持、结构化校验失败与用户取消。
- 管理员可见的知识资料入库诊断、暂存状态与 `dataset_version` 发布记录。
- 第二阶段：Agent 提出的需求补丁及其 Diff、追问、变更影响分析、Tool Call、研究证据、Agent 分工和冲突信息。
- 长期偏好记忆的确认、变更、删除和关闭结果。

## 4. 核心业务对象、稳定身份、来源与状态

本节是产品对象与状态语义的规格；精确字段以产品代码、migration 和测试为准。

### 对象主链

`Project → Requirement → RequirementVersion → RequirementItem`。

- Project：拥有成员、SourceArtifact 与 Project Brief。Brief 是 Project 上的独立字段集合，不伪装成 Requirement；`brief_revision` 单调递增，每次修订的内容以 append-only 历史持久化，ReviewRun 与 DeliveryPackage 钉住修订号即可复现当时的 Brief。第一阶段不建独立 Brief 版本界面。
- Requirement：可独立版本化、批准和交付的稳定需求容器，对应一个功能点或可独立交付的需求主题，不与单个条目混用。它持有 `baseline_version_id` 指向当前基线；基线只在 Requirement 粒度，全产品基线是非目标。
- RequirementVersion：一次可评审、可批准的内容快照。保留 `derived_from_version_id`、只随内容变化递增的 `revision`、批准时写入的 `approved_brief_revision` 与 `approval_review_run_id`、批准后的 `index_state`。已批准版本内容不可修改。
- RequirementItem：需求正文的最小单位。保留 `item_id`（当前版本实例）、`item_key`（跨版本稳定业务身份）、可选 `derived_from_item_id`、`section_key`、`provenance`、`statement_kind`、`confirmation_state`、`citations` 与 `citation_state`。
- SourceArtifact：导入的 PRD 原文，至少包含文件名或来源标识、格式、内容哈希、版本与 locator 契约。由它映射得到的条目保留 `source_artifact_id`、`source_locator` 与 `mapping_method`；未映射内容作为诊断保留。导入原文是被定义和评审的对象，可支持内部结构与矛盾 Finding 的定位，不因被导入而成为外部 Citation Candidate。
- ReviewRun：对某个版本某个修订的一次评审运行，产出 Finding。
- Finding：评审结论，固定到 `requirement_version_id` 与 `requirement_version_revision`，目标为 `item | section | document`（优先条目）。
- Decision：人对 Finding 或对 `proposed` 条目的处理记录。
- DeliveryPackage：从不可变版本导出的交付记录。

分区 `section_key` 第一阶段使用固定枚举：`problem / target_users / goals / non_goals / scope / business_rules / functional_requirements / constraints / dependencies / acceptance_criteria / other`；项目自定义分区是非目标。

### 来源、引用与决策三分

- 每个条目必须保留来源与形成过程：`provenance` 至少区分用户输入、导入 PRD、AI 建议、派生自旧版本。
- 事实性主张及引用外部规则、历史资料或已批准需求的 Finding 必须回到合格 Citation。
- 基于当前需求内部缺失、结构或矛盾的 Finding 必须回到当前版本的条目、分区或文档定位，不伪造外部 Citation。
- 用户提出或批准的产品意图由人的输入（`provenance=user_input`）或人的 Decision 提供权威来源，不能伪装成外部 Citation，也不因缺少 Citation 而被拒绝。
- 每个 Finding 都必须有可定位依据，但“可定位依据”不等于“外部 Citation”；依据资格由 `finding_kind` 决定，应用按类型校验，不只靠 Prompt。

### 条目字段的写入路径

`statement_kind` 取 `product_intent / external_fact / constraint / acceptance_criterion`；`confirmation_state` 取 `proposed | confirmed`；`citations` 只保存已验证 Citation；`citation_state` 取 `verified | unverified | none`。

- `external_fact` 只能由系统赋予，来源只有两条：AI 草稿生成时携带并通过校验的 Citation；`accept_suggestion` 把 Finding 的已验证 Citation 写回条目。导入映射器和人的直接输入一律不产生 `external_fact`：导入条目默认 `product_intent`，按分区可为 `constraint` / `acceptance_criterion`；与外部规则的矛盾交给 `external_fact_conflict` Finding 发现。
- 人可以把 `external_fact` 降级为 `product_intent`（同时清空 `citations`），不能反向升级；人编辑 `external_fact` 条目正文会自动降级并清空 Citation，由下一次评审重新检验。
- AI 草稿生成的 `external_fact` 若 Citation 未通过校验，条目保留为 `proposed` 且 `citation_state=unverified`；`confirm_items` 拒绝确认这类条目，用户只能改为 `product_intent` 或删除。
- `confirmation_state` 在创建时确定：人直接写入的条目、从已批准基线派生且正文未改的条目创建即 `confirmed`；只有 AI 生成和自动导入映射的条目是 `proposed`。不需要的导入条目直接删除（内容变更，递增 `revision`），不设 `discarded`。
- 权威来源规则：`external_fact` 靠 `citations`；`product_intent`、`acceptance_criterion` 与作为人的选择的 `constraint`，权威来源是 `provenance=user_input` 或一条人的 Decision。

### Finding

`finding_kind` 第一阶段固定枚举：

| 类型 | 含义 | 目标 | 依据资格 | 阻断 |
| --- | --- | --- | --- | --- |
| `internal_gap` | 当前版本缺失 | section | 当前版本定位 | 否 |
| `internal_conflict` | 当前版本内部矛盾 | item | 当前版本定位 | 是 |
| `external_fact_conflict` | 与外部规则或已批准需求冲突 | item / section | 必须有合格 Citation，缺 Citation 时拒绝写入而不是降级 | 是 |
| `impact_inference` | Web / Flutter / 服务端影响推断 | item / section / document | 允许无 Citation，界面必须标为推断 | 否 |
| `evidence_gap` | 证据不足转成的补充问题 | item / section | 当前版本定位 | 否 |

Finding 的 `target_kind + target_ref` 必须属于该版本当时修订的条目集合、分区枚举或版本本身，成员资格校验属于产品层。阻断与非阻断只影响严重度展示和 `waive` 时要求的理由强度；非阻断 Finding 也必须有 Decision 才能进入批准门。

### Decision

`decision_type` 固定枚举：

- `accept_suggestion`：采纳建议并修改条目，若 Finding 携带已验证 Citation 则写回条目，递增 `revision`。
- `reject`：判定 Finding 不成立，内容不变。
- `waive`：Finding 成立但接受风险，必须留理由，内容不变，原 Finding 保留。
- `supplement`：回答补充问题并新增或修改条目，递增 `revision`。
- `confirm_items`：确认 `proposed` 条目，不指向 Finding，可一次指向多个条目，只改 `confirmation_state`，不写 Citation、不递增 `revision`。

前四类必须指向本版本某次已完成运行的 Finding，且目标仍能解析到当前修订（`reject` / `waive` 不依赖目标，始终允许；`accept_suggestion` / `supplement` 要求目标条目仍存在）；目标已删除的 Finding 只读。同一 Finding 同时只有一条 `active` Decision；活动 Decision 可被替换，旧记录置为 `deactivated` 保留审计。所有 Decision 记录操作人、时间、理由和零个或多个受影响的条目，是条目级 Diff 的原因。

Decision 可作用于本版本任何已完成运行的 Finding，因此用户可以在一轮评审后连续接受多条建议再重跑一次。新一轮运行产生新的 Finding 对象；界面可按 `(finding_kind, item_key)` 匹配上一轮 Decision 供一键沿用，但沿用仍是一条新的、由人确认的 Decision，不自动迁移。旧版本的 Finding 与 Decision 继续可回查，新版本必须重新评审。

### 持久状态与派生状态

版本持久状态只有四个，每个迁移都由人的显式动作触发，没有任何迁移由 ReviewRun 结果自动驱动：

```text
draft → pending_approval        editor 提交批准（预检批准门）
pending_approval → draft        owner 退回，或 owner 主动撤回
pending_approval → approved     owner 人工批准（复检批准门，同一事务切换基线）
approved → superseded           同一 Requirement 的新版本被批准
```

派生展示状态由查询得出、不持久化：“评审中”= 该版本存在活跃 ReviewRun；“待补充”= 门禁运行存在未处理的 `evidence_gap` 或 `internal_gap`；“已交付”= 存在成功 DeliveryPackage。界面可以显示草稿、待补充、评审中、待批准、已批准、已交付、被替代七个词，后端只持久化四个。Requirement 归档 / 下线是非目标，不预建 `archived`。

### 编辑规则与并发

- `draft` 可写；`pending_approval`、`approved`、`superseded` 拒绝任何内容写入，要修改 `pending_approval` 的版本必须先退回 `draft`。
- 该版本存在活跃 ReviewRun 时拒绝内容写入，必须先取消运行。
- `revision` 只随条目与分区内容变化递增（含增删条目、改正文、改 `statement_kind`、改分区归属）；Decision 不递增 `revision`。每次内容写入携带客户端持有的 `revision`，不匹配则整个请求拒绝，不留部分变更；不建单编辑者锁。
- 同一 Requirement 同时最多一个 `draft | pending_approval` 版本；没有开放版本时才能从基线派生新版本。
- `owner` 编辑 Brief 不改变任何版本的持久状态，但让项目内所有匹配旧 `brief_revision` 的 ReviewRun 失去批准资格；处于 `pending_approval` 的版本显示“评审已过期”，`owner` 只能退回或在重新评审后批准。

### 批准门

提交时预检、批准时复检，两次使用同一规则：

- 门禁运行 = 当前 `revision` 上最近一次 `completed` 的 ReviewRun，且其 `brief_revision` 匹配当前 Brief。任何条目、分区或 Brief 变更都使旧 ReviewRun 失去批准资格；旧运行与 Finding 不删除。
- 门禁运行的 `proposed_count_at_start` 为 0，即时序钉死为“先确认、再评审”。
- 门禁运行产生的每条 Finding 都有 `active` Decision，且只能是 `reject` 或 `waive`；任何 `accept_suggestion` / `supplement` 都会递增 `revision` 并使当次运行失去资格，因此最后一轮评审必然是零内容变更的一轮。
- 没有 `confirmation_state=proposed` 的活动条目；每条 `external_fact` 活动条目 `citation_state=verified`（按写入路径构造上恒成立，门禁只做一致性断言）。
- 批准时将 `approval_review_run_id` 与 `approved_brief_revision` 写入不可变版本。

### 基线切换、索引与两个检索池

- 新版本批准、`baseline_version_id` 切换、旧基线进入 `superseded` 与批准审计记录在同一数据库事务内完成，任一步失败则全部回滚。
- 已批准版本的索引是批准事务之后的独立步骤：Chunk、Embedding 与写入项目检索池随后执行，版本上保留 `index_state=pending | indexed | index_failed`；失败真实暴露、可重试、不回滚批准。
- 已批准且作为当前基线的版本以 `approved_requirement` 来源角色进入同一 Project 的检索候选池。它用于说明项目内已批准的产品决定，不自动覆盖更高资格的现行业务规则；二者冲突时产生可见 Finding。
- ReviewRun 进入检索时钉住证据快照：`requirement_version_id + revision`、`brief_revision`、`dataset_version`、本轮可见的 `approved_requirement_version_ids`（只含 `indexed` 版本，排除本 Requirement 自身基线）以及 `proposed_count_at_start`；全部检索、校验与报告都在该快照内进行。诊断列出因 `index_failed` 而不可见的已批准需求。
- 项目检索池由 `approved_requirement_version_ids` 按版本身份过滤：`superseded` 版本因不在集合内自然离开池子，不做角色重标；把被替代版本作为历史材料参与检索是非目标。当前待评审版本不能把自身伪装成外部证据；派生版本的评审排除自身基线，版本间差异由 Diff 负责。
- 项目检索池与全局知识库是两个池子、两个快照身份（`approved_requirement_version_ids` 与 `dataset_version`），互不替代；“发布是产生新 `dataset_version` 的唯一动作”只约束全局知识库。

### 迭代与交付

- 第一阶段迭代 = 人手动从基线派生新版本；条目级 Diff 按 `item_key` 对齐并给出原因；Agent 驱动的变更分析属于第二阶段。
- DeliveryPackage 只能从 `approved` 或 `superseded` 版本导出（后者用于回溯历史交付），记录需求版本、`approved_brief_revision`、`compared_to_version_id`、导出人、时间、格式、内容哈希与成功 / 失败；一个版本可导出多次。草稿的非正式预览不产生 DeliveryPackage 记录。与具体下游系统的协作契约不在本规格内。

## 5. 第一阶段能力

第一阶段必须形成可运行的固定 RAG 需求定义、评审与交付闭环：

```text
真实资料
→ 解析、清洗、来源保留
→ Chunk 与 Metadata
→ PostgreSQL FTS + pgvector
→ 应用侧 RRF
→ Retriever 诊断
→ Context Builder
→ 结构化生成（结构化增量流式 + 最终校验）
→ Citation 支持性与证据充分性
→ 需求对象模型：项目、需求、版本、条目、基线
→ 固定表单创建 / 导入 PRD → 结构化需求草稿
→ ReviewRun → 可定位 Finding → 人的 Decision → 条目级 Diff
→ 版本生命周期、人工批准、基线切换、事务后索引
→ 从不可变版本导出交付包
→ 身份认证与两层角色
→ 知识管理后台（上传、暂存、发布、dataset_version）
→ Review API 与 Web 工作台
```

必须具备：

- 真实模型、真实 PostgreSQL 和真实 Embedding 主路径。
- 稳定的 Retriever 输入、输出、诊断和错误契约。
- 两个入口：固定表单创建（人写条目创建即 `confirmed`，检索后固定生成补全草稿，AI 条目标 `proposed` 并保留来源，只有携带已校验 Citation 的条目才成为 `external_fact`）；导入 PRD（保存 SourceArtifact，解析并映射到 `section_key`，条目一律 `proposed`、默认 `product_intent`，绝不产生 `external_fact`，保留原文定位，未映射内容进 `other` 且在诊断中可见）。
- 评审循环：先处理 `proposed`（`confirm_items` 或删除；含 `proposed` 条目时也允许运行评审作为参考，但该运行不具备批准资格）→ 运行评审 → Finding 挂条目 / 分区 / 版本 → 用户逐项 Decision → 改了内容就再评审 → 最后一轮的所有 Finding 只剩 `reject` 或 `waive` → editor 提交批准 → owner 人工批准 → 人工触发导出。
- Sources、Citation、Refusal 和补充问题；Finding 按 `finding_kind` 校验依据资格。
- 迭代：从基线手动派生新版本，条目级 Diff，评审时不检索自身基线，批准后原子切换基线，随后异步索引新基线。
- 用户登录、会话生命周期，以及第 2 节两层角色与动作矩阵的路由与动作边界。
- 受角色保护的知识资料上传、解析诊断查看、入库暂存与发布：发布是产生新 `dataset_version` 的唯一动作，上传本身不直接改变检索候选池。
- 生成阶段的结构化增量流式事件：真实调用模型的流式接口，后端按 Finding 结构增量解析已完整字段并通过 SSE 推送为“生成中、未校验”状态；生成结束后再执行一次完整 Schema、Citation 与依据资格校验，前端必须用“已校验”结果替换前述增量展示；校验失败时增量展示必须被显式撤回。
- 工作台：项目列表 → 需求列表 → 需求工作区（版本与条目导航、分区表单式结构化正文、评审面板与决策面板、运行评审 / 批准 / 导出动作、诊断抽屉）。
- 固定 Golden Set 与可重复对照，对照物是 ReviewRun 的已校验 Finding 与证据充分性判定。
- 可见的成本、延迟和依赖错误。

第一阶段只提供固定的“提交 → 批准”两步人工门和两层角色，不建设可配置的多级审批链、审批委托与通知、两层之外的权限模型、多租户或通用连接器意义上的完整知识运营平台；知识管理后台只提供上传、暂存、发布、诊断查看这些最小真实能力。第一阶段不接收模糊想法、不做动态追问、不做 Agent 变更分析、不建设通用 Workflow、Multi-Agent 或完整质量平台。全产品基线、Requirement 归档、项目自定义分区、Brief 版本界面、被替代版本作为历史材料检索都是非目标。

## 6. 第二阶段能力

第二阶段在第一阶段能力与对象模型上增加：

- Agent Harness：模型、上下文、工具、状态、权限、循环、停止、事件和观测。
- Tool Runtime：Schema 校验、执行、超时、取消、权限、审计和结构化错误。
- Agentic RAG：Query Rewrite、Source Routing、Retriever as Tool、补检索和追问。
- 需求 Brief 形成与缺失信息追问：Agent 接收模糊想法，识别缺失信息并通过正式的人工介入节点追问，结合内部 RAG、MCP、Search / Browser 形成产品 Brief 与结构化草稿。
- 正式需求写入的确认门：Agent 只能通过 `propose_requirement_patch` 提出补丁，展示 Diff 并等待人确认后由 `apply_requirement_patch` 写入 `draft` 版本；这是一次内容写入（递增 `revision`），人对 Diff 的确认同时记录为一条 Decision，使写入的条目直接成为 `confirmed`；Agent 携带已校验 Citation 的条目走 `external_fact` 路径，其余为 `product_intent`。
- 变更影响分析：选定基线、输入变更后，Agent 产出条目级差异，并结合 RAG 规则、File Tool 读取的 OpenAPI 与客户端模型、Code Tool 沙箱中的定向测试分析影响，经 Diff 确认形成新版本与增量交付包。
- MCP：连接外部 Tool / Resource；内部治理仍由 Tool Runtime 负责。
- 通用工具：Browser、Search、File 与受控 Code Tool。
- Agent Skills：按需加载需求评审领域说明、资源和脚本，不绕过 Tool Runtime。
- 状态与记忆：分离 Conversation、Run State、短期摘要和长期偏好；长期偏好记忆只能写入用户确认的偏好并接受用户治理。
- Deep Research：规划、迭代搜索、来源验证、证据积累、综合和停止。
- Multi-Agent：真实责任拆分、委派、并行、失败隔离、证据合并和冲突裁决。
- A2A：在本地责任契约成立后交换任务、状态、结果和错误。
- 必要 Workflow：显式状态、Checkpoint、恢复、人工介入和副作用治理。

Agent 修改正式需求前必须展示 Diff 并等待确认；主界面以需求文档和决策为中心，运行轨迹放在可展开详情。批准、导出与成员管理仍只能由人触发。

## 7. 第二阶段产品取舍

- 产品至少消费一个真实、只读、可观察的 MCP 能力；不建设通用 MCP 市场。
- Browser / Search 用于外部研究，不替代内部可引用 RAG。
- File Read 在用户批准的工作区中选择性读取需求附件、接口契约、客户端模型和配置，并保留路径、版本、内容哈希与定位；不得逃逸工作区或把文件内容自动视为可信 Citation。
- File Write 只向运行级暂存目录写入附件与中间产物（补充问题清单、证据清单、带批注副本等）；原始输入默认只读，覆盖需要独立确认、审计和幂等控制。File Write 不创建 DeliveryPackage，正式交付包只由人触发的导出动作产生；正式需求写入走 `propose_requirement_patch` / `apply_requirement_patch`，不是文件写入。
- Code Tool 用于运行项目已有或产品允许的接口契约校验、静态检查和定向测试；优先使用专用 Validator，不能把任意 Shell 或任意生成代码作为默认能力。
- Code Tool 只能在受控沙箱中执行：输入工作区只读、输出目录隔离、命令与环境变量白名单、默认禁网，并限制时间、CPU、内存、进程和输出大小。
- 至少有一个可按需加载的需求评审 Agent Skill。
- Multi-Agent 必须保留单 Agent 基线，不能只把一个 Prompt 拆成多个 Prompt。
- 至少把一个已有责任定义为稳定契约，使它既可经本地 Delegation 执行，也可交给独立远程 Agent；远程路径必须让两个独立 A2A 实现完成真实互操作，并固定规范修订、SDK 和协议绑定，显式处理 Agent Card、鉴权、版本、任务状态和错误差异。
- A2A 不替代责任、权限、证据归属和最终结果责任人。
- Workflow 只处理确实需要显式状态与恢复的问题，不建设低代码画布。

## 8. 第二阶段垂直场景

固定切口映射到对象模型：Project 是一个电商 App；Requirement 是“售后入口”需求主题；第一阶段的 v1 由导入现有 Target Requirement fixture 得到并经人工批准成为基线。第二阶段的“售后接口 v2 与多端契约一致性评审”是同一 Requirement 的新 RequirementVersion，不是新 Requirement：

- 变更要求售后接口增加或收紧 `source_channel`，并要求 Web 与 Flutter 客户端采用一致的入口可见性规则。
- Agent 从基线派生新版本，以 `propose_requirement_patch` 提出条目级差异，经 Diff 确认后写入。
- MCP 读取外部需求系统中的 issue、验收条件或关联资料；具体服务可以替换，但必须是只读真实能力。
- Search 发现候选官方资料，Browser 打开并提取官方 SDK 文档、版本说明或接口规范，二者都要保留来源身份。
- File Tool 读取当前评审工作区中的 PRD、OpenAPI、客户端模型、配置和测试入口。
- Code Tool 运行允许的 Schema / OpenAPI 校验、字段一致性检查或项目已有定向测试，返回退出码、输出、耗时、超时和产物。
- 内部 RAG 继续提供现行订单、售后和客户端规则，项目检索池提供同项目其他已批准需求；外部 Tool Result 不能绕过 Citation 支持性与证据充分性检查。
- 只有问题需要多步外部搜索、来源比较或冲突处理时才启动 Deep Research。
- 影响分析结论落为 Finding，由人逐项 Decision；新版本经人工批准后导出增量交付包。File Write 只把中间产物写入运行级暂存区。

该场景必须保留固定 RAG 和单 Agent 基线，不能通过更换业务案例规避前后比较。

## 9. 状态与停止契约

运行至少表达：

- 任务与当前目标。
- 当前证据和工具结果。
- 当前步骤、累计成本和预算。
- 待补充信息或待人工确认事项。
- 状态变化与最终停止原因。

停止原因至少区分：正常完成、需要补充、等待确认、达到上限、工具失败、模型失败、安全阻止和用户取消。

## 10. 证据与记忆边界

- Run State 保存当前执行过程。
- Conversation 保存会话消息。
- 短期记忆负责窗口、摘要和预算，摘要必须能够回查原消息。
- 长期偏好记忆是第二阶段主线能力，只保存用户明确确认的跨会话偏好；每条记录保留来源、作用域、版本和更新时间。
- 产品必须允许用户查看、更新、删除和关闭长期偏好记忆；已删除或关闭的偏好不能继续注入模型 Context。
- 模型推断、会话摘要、PRD 事实和 Tool Result 不能自动写成长期偏好。
- PRD、接口规则和历史评审属于可引用知识，不能由记忆替代。
- Tool 结果和 Agent 推断只有经过来源与支持性检查后才能成为 Citation。
- 来源（provenance）、引用（citation）与决策（decision）三分：条目来源说明它怎样形成，Citation 证明外部事实，Decision 记录人的裁决；三者不能互相冒充，产品意图不因缺少 Citation 被拒绝，外部事实不因人的确认而免除 Citation。
- 项目内已批准需求以 `approved_requirement` 角色进入同项目检索池，是“项目内已批准的产品决定”，不自动覆盖现行业务规则；当前待评审版本与自身旧基线都不进入本轮候选。
- 每次 ReviewRun 钉住运行证据快照（需求修订、Brief 修订、`dataset_version`、可见的已批准需求版本集合），报告与验收都在该快照内解释；这是运行复现能力，不是产品基线能力。

## 11. 安全与错误

- 模型提出行动，应用负责校验和执行。
- 工具默认最小权限，读取与写入分开。
- 高风险或不可逆操作需要人工确认。
- 批准、导出与成员管理只能由人触发；Agent 以发起用户的身份和项目角色行动，没有独立角色，任何接口都不能让 Agent 绕过这些门。
- 正式需求写入只走 `propose_requirement_patch` → Diff → 人工确认 → `apply_requirement_patch`，不是文件写入；File Write 不能创建 DeliveryPackage。
- 文件路径、符号链接、命令、工作目录、环境变量、网络和输出产物必须由应用校验，不能信任模型生成值。
- 缺少 Key、鉴权失败、限流、超时和能力不支持必须真实暴露。
- 不允许静默降级到 Mock、假向量、内存检索或静态成功结果。

## 12. 可观察与可评估

关键运行至少关联输入、模型与策略身份、检索结果、Tool Call、状态变化、停止原因、Token、成本、延迟和错误。

比较基线包括：

- 直接 LLM、Lexical、Dense 与 RRF RAG。
- 固定 RAG 与单 Agent。
- 单 Agent 与 Multi-Agent。

质量结论必须能回到固定样例、运行记录、自动评估或人工判断，不能只凭单次主观观察。

## 13. 产品代码真源

```text
source/packages/                  可复用能力
source/apps/review_assistant/     唯一产品
source/demos/                     机制实验代码
```

产品安装、配置、启动、测试和部署由 `source/apps/review_assistant/README.md` 维护。

## 14. 完成标准

最终产品必须：

- 可运行、可测试、可观察、可评估。
- 能回查证据并在证据不足时拒绝强结论。
- 能解释模型、检索、工具、状态和 UI 的责任边界。
- 能对真实依赖失败给出可定位错误。
- 能用 File Tool 追踪接口与客户端资料来源，用受控 Code Tool 验证至少一项契约差异，并在失败或超时时保留真实结果。
- 能让用户确认并管理长期偏好，且证明关闭或删除后不会继续注入，同时不会把偏好当作 Citation。
- 能以同一责任契约对照本地 Delegation 与远程 A2A 路径；远程路径完成两个独立实现的真实互操作，并保留任务状态、证据归属、错误和最终责任。
- 能修改一个业务规则、工具或 Agent 责任并完成回归。

第一阶段验收契约（均为确定性测试，不依赖 LLM Judge）：

- 导入 PRD 后条目覆盖与未映射内容可见；导入条目能回到 SourceArtifact 的内容哈希与原文定位，原文改变后不能静默沿用旧映射。
- AI 生成或自动导入映射的条目保留来源和 `proposed` 状态；人直接写入和从基线原样派生的条目创建即 `confirmed`。
- 导入映射与人的直接输入永不产生 `external_fact`；人试图把条目升级为 `external_fact` 被拒绝；人编辑 `external_fact` 正文后条目自动降级为 `product_intent` 且 `citations` 清空。
- AI 草稿的 `external_fact` 条目：Citation 通过校验则 `citation_state=verified`；未通过则 `confirm_items` 拒绝确认，只能改类或删除。
- 用户直接提出的产品意图不因无 Citation 被拒；外部事实性条目缺 Citation 时不能伪装成已支持。
- Finding 不能指向当前 `requirement_version_id` 之外的条目或分区；内部缺失 / 矛盾 Finding 回到目标定位且不伪造 Citation；`external_fact_conflict` 缺 Citation 时被拒绝写入而不是降级为推断；`impact_inference` 允许无 Citation，但输出带推断标记，且未处理时阻止提交批准。
- `confirm_items` 不要求 Finding，能一次确认多个条目，不递增 `revision`；其余四类 Decision 缺少 Finding 时被拒绝。
- 替换活动 Decision：旧记录变为 `deactivated` 且可查，同一 Finding 任一时刻只有一条 `active`。
- 一轮评审后连续 `accept_suggestion` 多条 Finding：每条递增 `revision`，其余 Finding 仍可处理；目标条目被删除后该 Finding 的 `accept_suggestion` / `supplement` 被拒绝，`reject` / `waive` 仍允许。
- `accept_suggestion` 把 Finding 的已验证 Citation 写回条目，写回后 `citation_state=verified`；`accept_suggestion` / `supplement` 递增 `revision` 并使当前 ReviewRun 失去批准资格，`reject` / `waive` 不递增。
- 新一轮运行的 Finding 没有 Decision 即不能通过门禁，即使上一轮同目标同类 Finding 已有 Decision；“沿用”产生新的 Decision 记录。
- 门禁运行的 `proposed_count_at_start` 必须为 0：先评审再 `confirm_items` 的顺序无法通过批准门。
- 批准门拒绝未处理的任何 Finding、未确认的 `proposed` 条目、缺 Citation 的 `external_fact` 条目、过期需求修订或过期 Brief 修订；提交时预检与批准时复检使用同一规则；批准记录能回到对应 ReviewRun。
- Decision 能追踪到 Finding 与最终条目变化；条目级 Diff 能按 `item_key` 对齐并给出原因。
- 新版本批准前旧基线保持不变；批准时 `baseline_version_id` 原子切换，旧版本进入 `superseded`；同一 Requirement 存在 `draft | pending_approval` 版本时，派生新版本被拒绝。
- 批准事务成功而索引失败时：基线已切换、`index_state=index_failed`、可重试、批准不回滚；重试成功后新 ReviewRun 的快照才包含它。
- ReviewRun 固定 `requirement_version_id + revision`、`brief_revision`、`dataset_version` 与 `approved_requirement_version_ids`，并在运行记录和报告中可见；内容或 Brief 修改后旧运行不能用于批准。
- 派生版本的 ReviewRun 快照不包含本 Requirement 自身基线；包含同项目其他 Requirement 的 `indexed` 基线；`index_failed` 的基线不在快照内且在诊断中列出；`superseded` 版本的 Chunk 不出现在任何新 ReviewRun 的项目池候选中，无需重标角色。
- `pending_approval` 状态下的内容写入被拒绝；存在活跃 ReviewRun 时的内容写入被拒绝；乐观修订号能拒绝基于旧 `revision` 的覆盖写入，失败不留部分条目变更。
- Brief 修订历史 append-only：任一 ReviewRun 或 DeliveryPackage 钉住的 `brief_revision` 都能取回当时内容。
- DeliveryPackage 的 Markdown / JSON 与固定的已批准版本和 `approved_brief_revision` 一致（哈希可验）；草稿版本不能导出正式交付包，非正式预览带明确标记且不产生 DeliveryPackage 记录；`superseded` 版本可重新导出并标明已被替代。
- 任何接口（含第二阶段 Agent）无法绕过人工批准、导出和成员管理门禁；系统 admin 不能仅凭系统角色批准项目需求。
- 已有 Golden Set / 四路对照 / 检索指标契约不变，另加需求草稿引用正确性样例。
