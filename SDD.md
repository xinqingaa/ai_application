# 需求评审助手系统设计说明

本文是需求评审助手的 Software Design Description，维护领域对象、稳定身份、状态机、业务不变量、证据与权限模型、核心流程、事务边界和接口事件等详细设计。产品目标与范围以 [SPEC.md](SPEC.md) 为准，代码结构与实现顺序以 [PLAN.md](PLAN.md) 为准；冲突时遵循 `SPEC → SDD → PLAN → 课程项目篇`，真实 Schema、OpenAPI、migration 和测试负责精确执行但不得悄悄改变上层契约。

## 1. 设计目标与核心不变量

系统设计围绕七条不变量展开：

1. Requirement 基线是产品闭环中心，基线只在 Requirement 粒度。
2. RequirementVersion 的持久状态只由人的显式动作迁移；ReviewRun、资料解析和索引状态不能自动改变它。
3. 来源、Citation 与 Decision 三分：来源说明内容怎样形成，Citation 支撑外部事实，Decision 记录人的裁决。
4. 当前需求和自身旧基线不能成为本轮外部证据；内部定位与外部 Citation 不混用。
5. 批准内容、Brief 修订、决策集合和被引用的外部引文快照形成不可变快照，后续导出不重新解释“批准时看到了什么”。
6. Agent 与 Tool 复用同一领域写入和批准门，不能建立旁路。
7. 真实依赖失败、证据不足和业务状态拒绝必须是不同结果。

## 2. 系统上下文与职责层次

```text
Web 工作台
  → review_assistant 产品服务
      → 需求领域模型 / 状态 / 权限 / API / SSE
      → llm_core：Provider、Prompt 版本、Structured Output、Context
      → rag_core：解析、Chunk、检索、可信生成、证据校验
      → agent_core（第二阶段）：框架适配、Tool Runtime、Run、事件与治理
      → PostgreSQL / pgvector / 外部 MCP 与 Tool
```

- `review_assistant` 拥有需求领域 Schema、Prompt、状态、权限、交付和产品交互。
- `llm_core` 与 `rag_core` 保持领域无关，不承载 Finding、Decision 或需求状态机。
- `agent_core` 组合 LangChain / LangGraph 等成熟框架，不重复实现框架运行时。
- 具体目录、package 和实施顺序由 PLAN 维护，本节只固定依赖方向。

## 3. 领域对象与稳定身份

### 3.1 对象主链

```text
Project → Requirement → RequirementVersion → RequirementItem
```

### 3.2 Project 与 Project Brief

Project 拥有成员、SourceArtifact 与 Project Brief。Brief 是 Project 上的独立字段集合，不伪装成 Requirement。

系统 member 创建 Project 后成为该 Project 的 owner。创建 Project 时系统建立 `brief_revision=0` 的初始 Brief；它可以只有项目名称等最小识别信息，其余字段允许为空。空 Brief 不阻止创建第一个 Requirement draft 或启动固定表单 / 导入流程，但 ReviewRun 与 Agent 必须把实际缺失的项目语境表达为可定位的内部缺口或追问，不能伪造默认事实。owner 后续编辑 Brief 时才产生递增修订。

Brief 最小字段：

- 产品或项目背景与业务域。
- 项目级目标与非目标。
- 目标平台与全局约束，包括 Web、Flutter、服务端范围以及合规、性能底线。
- 通用术语与业务主体。
- 项目级默认规则或成功标准。

Brief 只放跨 Requirement 稳定的信息；单个 Requirement 的 `problem / goals / non_goals / constraints` 只写本需求特有内容。`brief_revision` 单调递增，每次修订 append-only 持久化。ReviewRun、批准版本与 DeliveryPackage 钉住修订号即可复现当时语境。第一阶段不建独立 Brief 版本界面。

Brief 以“项目语境”进入 ReviewRun Context，不进入 Evidence 分区、不产生 Citation Candidate。条目与 Brief 冲突使用 `internal_conflict`，Finding 目标仍是 RequirementItem，依据另带 `brief_field` locator 并通过 ReviewRun 的 `brief_revision` 解析。

### 3.3 Requirement

Requirement 是可独立版本化、批准和交付的稳定需求容器，对应一个功能点或可独立交付的需求主题，不与单个条目混用。它持有 `baseline_version_id` 指向当前基线。

同一 Requirement 同时最多存在一个 `draft | pending_approval` 开放版本。全产品基线、Requirement 归档和并行开放分支不在当前范围。

editor 或 owner 创建 Requirement 是普通人工产品动作，不是 Agent Tool。创建者可只提供标题和一句自然语言种子，系统立即建立该 Requirement 的唯一 `draft` 版本；条目、分区状态和完整内容可随后由固定流程或第二阶段 Agent 协助形成。这个轻量容器动作提供稳定身份、Project 归属和写入授权，不等于人必须预先填写完整需求。

### 3.4 RequirementVersion

RequirementVersion 是一次可评审、可批准的内容快照，至少保留：

- `requirement_version_id`。
- `derived_from_version_id`。
- 只随内容变化递增的 `revision`。
- 持久状态。
- `approved_brief_revision`。
- `approval_review_run_id`。
- `approved_decision_ids`。
- `approved_decision_set_hash`，覆盖冻结的 Decision ID、类型、理由和关键内容。
- `index_state`。

已批准版本的内容和批准决策集合不可修改。

### 3.5 RequirementItem

RequirementItem 是需求正文最小单位，至少保留：

- `item_id`：当前版本实例身份。
- `item_key`：跨版本稳定业务身份。
- 可选 `derived_from_item_id`。
- `section_key`。
- `provenance`。
- `statement_kind`。
- `confirmation_state`。
- 已验证 `citations` 与 `citation_state`。
- 导入来源或 Decision 关系。

第一阶段固定 `section_key`：

```text
problem / target_users / goals / non_goals / scope
business_rules / functional_requirements / constraints
dependencies / acceptance_criteria / other
```

项目自定义分区是非目标。

### 3.5.1 分区处理与完整性

每个 RequirementVersion 对除 `other` 外的固定分区都必须暴露一种分区处理状态；它是版本完整性的一部分，不是模型输出的可选描述：

- `addressed`：该分区至少有一条 `confirmed` RequirementItem。
- `not_applicable`：人明确标记该分区不适用并留下理由。
- `needs_input`：当前缺少用户意图或必要事实；默认阻断批准。

`addressed` 可以由条目确认状态推导，`not_applicable` 必须保留操作者、理由和版本身份，二者不能在同一分区同时成立。具体表结构或 API 形状由实现阶段决定，但版本、分区、状态、人工不适用理由和审计关系是稳定领域契约。固定表单、导入映射和 Agent 草稿均可产生 `needs_input`，不得以模型默认值或无依据外部事实伪造 `addressed`。

### 3.6 SourceArtifact

导入 PRD 原文保存为 SourceArtifact，至少包含来源标识、文件名、格式、内容哈希、版本和 locator 契约。映射条目保留 `source_artifact_id`、`source_locator` 和 `mapping_method`；未映射内容进入诊断。

SourceArtifact 是被定义和评审的对象，可支撑内部结构与矛盾定位；它不因被导入而自动成为 Citation Candidate。

### 3.7 评审与交付对象

- ReviewRun：对某个 RequirementVersion 的确定修订和证据快照执行一次评审。
- Finding：固定到 `requirement_version_id + requirement_version_revision`，目标为 `item | section | document`。
- Decision：人对 Finding、待确认条目或第二阶段 Agent 补丁的处理记录。
- DeliveryPackage：从不可变版本导出的成功或失败记录，一个版本可以导出多次。

ReviewRun 是 Finding 的唯一生产者，也是 Decision 与批准门唯一承认的运行身份。它有两种执行模式：第一阶段的 `pipeline` 固定管道，以及第二阶段由 Agent 推进的 `agentic`。执行模式只决定运行怎样被推进，不改变运行身份、证据快照义务、持久终态集合和批准门资格；两种模式共用同一持久对象，不建立第二套评审运行表，也不为 Agent 建立第二条 Finding 生产路径。`agentic` 模式的绑定与停止映射见第 9.4 节。

## 4. 来源、陈述、Citation 与证据资格

### 4.1 来源、引用与决策三分

- `provenance` 至少区分用户输入、导入 PRD、AI 建议和派生自旧版本。
- 外部事实及引用外部规则、历史资料或已批准需求的 Finding 必须回到合格 Citation。
- 基于当前需求或 Brief 的缺失、结构和矛盾回到内部 locator，不伪造外部 Citation。
- 用户提出或批准的产品意图由用户输入或人的 Decision 提供权威来源，不因缺少 Citation 被拒绝。

### 4.2 条目字段与写入路径

`statement_kind`：

```text
product_intent / external_fact / constraint / acceptance_criterion
```

`confirmation_state`：

```text
proposed / confirmed
```

`citation_state`：

```text
verified / unverified / none
```

规则：

- `external_fact` 只能由系统赋予：AI 草稿携带并通过 Citation 校验，或 `accept_suggestion` 把 Finding 的已验证 Citation 写回。
- 导入映射和人的直接输入不产生 `external_fact`；导入条目默认 `product_intent`，按分区可以是 `constraint / acceptance_criterion`。
- 人可以把 `external_fact` 降级为 `product_intent` 并清空 Citation，不能反向升级。
- 人编辑 `external_fact` 正文会自动降级并清空 Citation，等待下次评审重新检验。
- AI 生成的 `external_fact` Citation 未通过时保留 `proposed + unverified`，不能被 `confirm_items` 确认，只能改类或删除。
- 人直接写入和从基线原样派生的条目创建即 `confirmed`；AI 生成和自动导入映射的条目为 `proposed`。
- 删除条目属于内容变化并递增 `revision`，不建立 `discarded` 状态。

### 4.3 证据登记簿与允许集合

“模型声明的来源必须属于本轮允许集合”这条成员资格检查在两个阶段语义相同，变化的只是允许集合怎样形成：第一阶段它等于一次检索的候选名单，第二阶段它是该 ReviewRun 的证据登记簿。

登记规则：

- 受治理的 Tool 调用是登记的唯一入口。任何来源必须先登记才可能成为 Citation Candidate，未登记来源一律判为越界声明。
- 每条登记至少保留来源类型、稳定来源身份、locator、获取时间、产生它的 `tool_call_id` 和证据资格。
- 稳定身份按来源类型确定：内部 Chunk 用 `chunk_id`；MCP 资源用资源 URI 与获取时间；网页用 URL、抓取时间与内容哈希；工作区文件用相对路径与内容哈希；执行结果用 `command_ref` 与输入哈希。
- 登记簿在一次运行内单调增长，只增不删。Checkpoint 恢复、重放和补检索都只向其追加，使成员资格判定在恢复后仍可解释。
- 内部类型登记必须落在该运行证据快照允许的 `dataset_version` 与 `approved_requirement_version_ids` 内；外部类型不受快照约束，但必须保留获取时间并标记为不可信输入。
- 登记只解决“是否属于允许集合”。Citation 支持性与按 `finding_kind` 的依据资格规则完全复用，不为 Tool 证据另立一套校验路径。

证据资格按来源性质区分，登记本身不赋予资格：

- 内部 Chunk、已批准需求、MCP 资源、网页和工作区文件承载外部陈述，可支撑 `external_fact` 与 `external_fact_conflict`。
- Code Tool 的执行结果是本地验证结果而不是外部陈述，只能支撑标为推断的 `impact_inference` 或作为 Finding 的诊断依据，不得成为 `external_fact` 的 Citation。退出码、日志和产物都不构成“外部规则如此规定”的证据。
- 外部来源成为 Citation 时必须同时持久化被引用片段的引文快照，见第 10 节。

## 5. Finding 与 Decision

### 5.1 Finding 类型

| `finding_kind` | 含义 | 目标 | 依据资格 | 阻断 |
| --- | --- | --- | --- | --- |
| `internal_gap` | 当前版本缺失 | section | 当前版本定位 | 否 |
| `internal_conflict` | 版本内部矛盾，或条目与 Brief 矛盾 | item | 当前版本定位；必要时附 `brief_field` locator | 是 |
| `external_fact_conflict` | 与外部规则或已批准需求冲突 | item / section | 必须有合格 Citation | 是 |
| `impact_inference` | Web / Flutter / 服务端影响推断 | item / section / document | 可无 Citation，必须标为推断 | 否 |
| `evidence_gap` | 证据不足形成的补充问题 | item / section | 当前版本定位 | 否 |

Finding 的目标必须属于该 RequirementVersion 当时修订的条目集合、固定分区或版本本身。缺 Citation 的 `external_fact_conflict` 拒绝写入，不降级为已支持结论。阻断级别影响严重度和 `waive` 理由强度；任何未处理 Finding 都阻止提交批准。

### 5.2 Decision 类型

第一阶段五类：

- `accept_suggestion`：采纳建议并修改条目；可写回已验证 Citation，递增 `revision`。
- `reject`：判定 Finding 不成立，内容不变。
- `waive`：Finding 成立但接受风险，必须留理由，内容不变。
- `supplement`：回答补充问题并新增或修改条目，递增 `revision`。
- `confirm_items`：不指向 Finding，可一次确认多个 `proposed` 条目，不写 Citation、不递增 `revision`。

第二阶段增加：

- `apply_patch`：人确认 Agent 补丁 Diff 后写入 `draft`，不指向 Finding，可影响多个条目；写入条目直接 `confirmed`，内容变化递增 `revision`，之后必须重新评审。

### 5.3 Decision 不变量

- 前四类指向本版本某次已完成 ReviewRun 的 Finding。
- `accept_suggestion / supplement` 要求目标仍存在；目标删除后被拒绝。
- `reject / waive` 不依赖目标，目标删除后仍允许。
- 同一 Finding 同时只有一条 `active` Decision；替换时旧记录进入 `deactivated` 并保留审计。
- Decision 只在 `draft` 可创建或替换；`pending_approval / approved / superseded` 下只读。
- Decision 可处理当前版本任何已完成运行的 Finding；新一轮运行产生新 Finding，旧 Decision 不自动迁移。
- 界面可以按 `(finding_kind, item_key)` 提示沿用旧决定，但沿用仍产生新的人工 Decision。

## 6. 身份、权限与人工门禁

### 6.1 两层角色

- 系统级：`admin / member`。
- 项目级：`owner / editor / viewer`。
- 权限取两层交集。系统 admin 未成为项目成员时不能查看或操作项目；成为项目成员后按项目角色行动。
- 系统 member 创建项目后成为 owner。

### 6.2 动作矩阵

| 动作 | viewer | editor | owner | 系统 admin |
| --- | --- | --- | --- | --- |
| 查看项目、需求、版本、Finding、Decision、诊断 | 是 | 是 | 是 | 仅成为项目成员后 |
| 创建 Requirement、导入 PRD | 否 | 是 | 是 | 按项目角色 |
| 编辑草稿、派生版本、确认条目 | 否 | 是 | 是 | 按项目角色 |
| 运行评审、取消自己发起的 ReviewRun | 否 | 是 | 是 | 按项目角色 |
| 取消任意 ReviewRun | 否 | 否 | 是 | 按项目角色 |
| 处理 Finding、形成 Decision | 否 | 是 | 是 | 按项目角色 |
| 提交批准 | 否 | 是，且必须由人触发 | 是，且必须由人触发 | 按项目角色 |
| 退回或撤回 | 否 | 否 | 是，且必须由人触发 | 按项目角色 |
| 批准版本 | 否 | 否 | 是，且必须由人触发 | 不自动获得 |
| 编辑 Project Brief | 否 | 否 | 是，且必须由人触发 | 不自动获得 |
| 正式导出不可变版本 | 否 | 是，且必须由人触发 | 是，且必须由人触发 | 按项目角色 |
| 生成草稿非正式预览 | 否 | 是 | 是 | 按项目角色 |
| 管理项目成员 | 否 | 否 | 是，且必须由人触发 | 不自动获得 |
| 重试已批准版本索引 | 否 | 是 | 是 | 按项目角色 |
| 管理全局知识资料 | 否 | 否 | 否 | 是 |

六类人工动作是：提交批准、退回或撤回、批准、正式导出、项目成员管理、编辑 Project Brief。后端路由和动作层都必须执行授权，前端隐藏按钮不是授权依据。

创建 Requirement 是 editor 或 owner 的普通人工产品动作，不是 Agent Tool；创建后形成目标 Requirement 的 draft 容器。它不属于六类人工门，但后续任何 Agent 草稿或补丁都必须绑定该容器。

## 7. RequirementVersion 生命周期与批准

### 7.1 持久状态

```text
draft → pending_approval        editor 人工提交，预检批准门
pending_approval → draft        owner 人工退回或撤回
pending_approval → approved     owner 人工批准，复检批准门
approved → superseded           同一 Requirement 的新版本被批准
```

派生展示状态：

- “评审中”：存在活跃 ReviewRun。
- “待补充”：门禁运行存在未处理 `evidence_gap / internal_gap`。
- “已交付”：存在成功 DeliveryPackage。

这些展示状态不持久化。Requirement 归档不预建。

### 7.2 编辑与并发

- 内容和 Decision 只在 `draft` 可写。
- 存在活跃 ReviewRun 时拒绝内容写入，必须先取消运行。
- `revision` 只随条目与分区内容变化递增；Decision 记录本身不递增，只有它引发的条目变化递增。
- 每次内容写入携带客户端持有的 `revision`，不匹配则整个请求拒绝且不留部分变更。
- 不建立单编辑者锁。
- 同一 Requirement 有开放版本时不能再派生另一开放版本。

### 7.3 Brief 修改与待批准版本

owner 修改 Brief 不自动改变 RequirementVersion 状态，但使项目内所有旧 `brief_revision` 的 ReviewRun 失去批准资格。

若版本已处于 `pending_approval`：

1. 显示“评审已过期”。
2. owner 必须先退回 `draft`。
3. 回到 `draft` 后重新评审、处理新 Finding 并重新提交。
4. `pending_approval` 状态不得创建可用于批准的新门禁运行。

### 7.4 批准门

提交时预检、批准时复检，使用同一规则：

- 门禁运行是当前 `revision` 上最近一次 `completed` ReviewRun，且 `brief_revision` 匹配当前 Brief。
- 门禁运行必须是完整评审：走完全部既定取证与校验步骤并以 `completed` 结束，且诊断中没有降级记录。降级至少包括某一路检索未成功执行、校验层未全部执行，以及第二阶段因步骤或预算上限提前停止。执行模式不影响这条判定。
- 门禁运行的 `evidence_decision` 不进入批准门条件：可回答、部分回答和拒答都有批准资格。
- `proposed_count_at_start = 0`，先确认条目再评审。
- 门禁运行的每条 Finding 都有活动 Decision，且只能是 `reject / waive`。
- 当前没有 `proposed` 条目。
- 除 `other` 外每个固定分区均为 `addressed`，或由人以有理由的 `not_applicable` 明确处理；任何 `needs_input` 都拒绝提交或批准。
- 每条 `external_fact` 条目 `citation_state = verified`。
- 任何内容或 Brief 变化都使旧运行失去资格。

`evidence_decision` 说明本次评审掌握的证据能支撑到什么程度，不说明需求版本是否完备，因此它不是批准资格的条件。证据不足是关于资料的结论，是否承担风险由人裁决，而这份权力已经由“每条 Finding 必须有活动 Decision、`waive` 必须留理由”承载，不需要第二套机制。反过来若拒答阻断批准，两个候选池都为空的新项目永远批不出第一个基线，项目检索池永远为空，第 8.3 节的项目级证据沉淀链断裂。

需要阻断的是运行本身残缺，而不是证据稀少，这由“完整评审”承担：检索零候选与过滤后空结果是合法取证结果，产生拒答但不是降级；某一路检索失败或校验层未跑完是降级，该运行即使以 `completed` 结束也不能用于批准。

拒答与部分回答必须在提交和批准界面显式呈现，owner 必须能在批准前看到本次评审是在证据不足的情况下完成的。批准记录通过 `approval_review_run_id` 回到当时的 `evidence_decision`，导出不重新解释。

提交批准后 Decision 集合只读。批准时把 `approval_review_run_id`、`approved_brief_revision`、`approved_decision_ids` 和 `approved_decision_set_hash` 写入不可变版本，并断言决策集合恰好覆盖门禁运行全部 Finding。

### 7.5 基线事务

以下操作在同一数据库事务内完成：

1. 新版本进入 `approved`。
2. Requirement 的 `baseline_version_id` 指向新版本。
3. 旧基线进入 `superseded`。
4. 写入批准人、ReviewRun、Brief 修订、Decision 快照和审计。

任一步失败全部回滚。索引不进入该事务。

## 8. ReviewRun、知识与证据快照

### 8.1 ReviewRun 状态与执行模式

`pipeline` 模式的执行阶段：

```text
submitted → retrieving → generating_unverified → validating
                                                    ↓
                              completed | failed | cancelled
```

`retrieving / generating_unverified / validating` 是 `pipeline` 模式的内部执行阶段，不是 ReviewRun 的通用状态。`agentic` 模式有自己的执行阶段（动态取证、Tool 执行、等待授权、预算判定），并按第 9.4 节映射回同一组终态。

以下契约与执行模式无关：

- 持久终态只有 `completed | failed | cancelled`，不因引入 Agent 而扩展。
- `completed` 携带整体 `evidence_decision`：可回答、部分回答或拒答。
- `failed` 携带结构化 `failure_reason`。
- 检索零候选是完成且拒答，不是系统失败。
- 取证或校验步骤的降级必须进入诊断，供第 7.4 节判定完整评审；零候选与过滤后空结果不属于降级。
- ReviewRun 结果不自动迁移 RequirementVersion 状态。
- SSE 断开是传输事件，不改变业务状态。

### 8.2 证据快照

首次取证之前固定（`pipeline` 模式即进入 `retrieving` 时，`agentic` 模式即第一次调用取证 Tool 之前）：

- `requirement_version_id + revision`。
- `brief_revision`。
- `dataset_version`。
- `approved_requirement_version_ids`，只含同项目已索引的当前基线并排除本 Requirement 自身基线。
- `proposed_count_at_start`。

之后的检索、生成、校验和报告均在该快照内解释。`agentic` 模式的动态补检索只能在同一快照内选择候选；外部来源经第 4.3 节的证据登记簿进入，不扩大内部快照。

### 8.3 两个检索池

全局知识库：

```text
admin 上传 → 解析 / Chunk / Embedding / 诊断 → staged
→ admin 发布 → 新 dataset_version → 成为候选
```

项目检索池：

```text
RequirementVersion 批准 → index_state=pending
→ Chunk / Embedding → indexed | index_failed
→ indexed 后以 approved_requirement 进入同 Project 候选
```

- 两个池子使用不同快照身份，互不替代：全局池是版本号 `dataset_version`，项目池是显式集合 `approved_requirement_version_ids`。
- 全局候选集合的任何变化都必须表达为新的 `dataset_version`，加入和移除都不例外。
- `approved_requirement` 表示项目内已批准决定，不自动覆盖更高资格的现行业务规则。
- 当前待评审版本和自身旧基线不进入候选，版本差异由 Diff 负责。
- `superseded` 版本因不在快照集合中自然离开候选，不重标角色。
- 诊断列出未进入候选的项目当前基线，包含 `requirement_version_id`、`index_state=pending | index_failed` 和不可见原因。
- 新 Project 可以同时没有可见全局资料和已索引项目基线；此时两个候选集合为空，ReviewRun 以 `completed + evidence_decision=refusal` 或等价的证据不足结果完成，而不是进入 `failed`。第一个批准且索引成功的 RequirementVersion 才开始为后续同项目运行提供 `approved_requirement` 候选。

### 8.4 知识资料生命周期

```text
uploaded → parsing → parse_failed
                   → staged → published → superseded
```

切分与向量化在 `staged` 前完成。发布是产生新 `dataset_version` 的唯一动作；上传与暂存不能直接改变全局候选池。

`dataset_version` 是全局候选池的一次完整快照，而不是累计发布次数，因此下架不是独立机制：admin 下架一份已发布资料，走的仍是发布路径，产生一个不包含该资料的新 `dataset_version`，该资料随之进入 `superseded`。这条规则由快照身份的唯一性逼出——若下架不推进版本号，下架前后两次运行会钉在同一个 `dataset_version` 上却看到不同候选集合，“这次运行看到了哪一版资料”就不再有唯一答案。项目检索池不需要同样的规则，因为它的快照身份是运行开始时逐一枚举的 `approved_requirement_version_ids`，删除天然被集合捕捉。

## 9. 第二阶段 Agent 写入与影响分析

### 9.1 Brief 追问

Agent 从模糊想法识别 Project Brief 与 Requirement 分区缺口，通过可恢复人工节点追问。运行开始前，editor 或 owner 已人工创建或选择目标 Requirement 的 `draft`；创建可以只包含标题与一句自然语言种子。Agent 不能创建正式 Requirement，只能建议标题或在该 draft 上提出内容补丁。用户回答保留为用户输入来源；Retriever、MCP、Search 和 Browser 结果只是候选证据。

Agent 只能生成 Brief 草案和需求草稿：

- Brief 草案存在 Run State 或运行级暂存区，不产生 `brief_revision`。
- owner 采纳草案仍是一次人工 Project Brief 编辑。
- 需求草稿必须走正式补丁写入门。

### 9.2 正式需求写入

```text
propose_requirement_patch
→ 条目级 Diff
→ 人工确认
→ apply_requirement_patch
→ apply_patch Decision
→ revision 递增
→ 重新 ReviewRun
```

补丁基于过期 `revision`、非 `draft` 版本或活跃 ReviewRun 时整体拒绝。重放、恢复和重复请求不能重复写入。此路径不能触发六类人工动作。

### 9.3 变更影响分析

变更影响分析在一次 `agentic` ReviewRun 内进行，产生的 Finding 属于该运行，与 `pipeline` 运行的 Finding 同受目标成员资格、依据资格、Decision 和批准门约束。

Agent 把条目级差异分别对照：

- RAG 中的现行业务规则。
- File Tool 读取的 OpenAPI、JSON Schema、客户端模型与配置。
- Code Tool 沙箱中的契约校验、静态检查或定向测试。

三类对照物的证据资格不同，按第 4.3 节判定：前两类承载外部陈述，可支撑 `external_fact_conflict`；Code Tool 的执行结果只能支撑 `impact_inference` 或作为诊断依据。与规则或契约冲突且证据合格时形成 `external_fact_conflict`；多端影响推断形成带推断标记的 `impact_inference`。分析结论不自动改需求，也不自动做 Decision；人工处理后重新评审、批准并人工导出增量交付包。

### 9.4 Agent Run、ReviewRun 绑定与停止

Agent Run 按目的分两类，只有一类开启 ReviewRun：

- **需求形成类**：追问、Brief 草案、`propose_requirement_patch`。它不产生 Finding，不开 ReviewRun，也不钉证据快照。
- **评审与影响分析类**：开启一个 `agentic` 模式的 ReviewRun，并在首次取证前钉住第 8.2 节的证据快照。

绑定是一对一：一次 `agentic` ReviewRun 由恰好一个 Agent Run 推进，ReviewRun 记 `agent_run_id`，Agent Run 记 `review_run_id`，两者对需求形成类运行均为空。Agent Run 可以多次 Checkpoint 与 Resume，运行身份不变，因此不产生一对多关系。

每次 Agent Run 至少保存：任务与当前目标、当前证据和 Tool Result、当前步骤、累计成本与预算、待补充信息或待人工确认事项、状态变化和最终停止原因。Checkpoint 恢复后必须沿用同一运行身份与幂等键，不能重复执行已经成功的副作用。

停止原因至少区分：正常完成、需要补充、等待确认、达到步骤或预算上限、工具失败、模型失败、安全阻止和用户取消。等待用户与恢复是显式状态，不用超时或异常伪装。

评审与影响分析类运行的停止原因确定性映射到 ReviewRun 终态：

| Agent Run 停止原因 | ReviewRun 终态 |
| --- | --- |
| 正常完成 | `completed`，带 `evidence_decision` |
| 需要补充 | `completed`，`evidence_decision` 为部分回答或拒答 |
| 达到步骤或预算上限 | `completed`，部分回答或拒答，诊断标 `budget_exhausted` |
| 等待确认 | 不是终态，运行保持活跃 |
| 工具失败、模型失败 | `failed`，带对应 `failure_reason` |
| 安全阻止 | `failed`，带安全阻止类 `failure_reason` |
| 用户取消 | `cancelled` |

达到上限不是依赖失败，因此不落 `failed`；但它按第 7.4 节没有批准资格，不能让预算耗尽变成“没有未处理 Finding”的批准捷径。

`agentic` ReviewRun 运行期间不得修改需求内容。第 7.2 节的“活跃 ReviewRun 期间拒写”对它同样生效，因此它的人工介入只能用于授权取证——批准访问某个工作区、确认调用某个 MCP 能力、确认执行一次沙箱验证——不能用于补充需求内容。内容补充仍走“运行结束 → Finding → `supplement` Decision”的第一阶段路径，避免运行自己拒绝自己触发的写入。

等待授权不得无限期阻塞 draft 写入：按第 6.2 节，发起者可取消自己发起的运行，owner 可取消任意运行；取消后 draft 恢复可写。

## 10. DeliveryPackage

DeliveryPackage 只能从 `approved / superseded` 版本导出，使用不可变版本中的：

- RequirementVersion 内容。
- `approved_brief_revision` 对应 Brief。
- `approved_decision_ids` 对应 Decision。
- `approved_decision_set_hash` 完整性校验。
- `compared_to_version_id` 对应差异。
- 验收条件、Citation 与证据快照身份。
- 门禁运行的 `evidence_decision`，使交付包能说明这条基线是在什么证据程度下被批准的。
- 外部来源 Citation 的引文快照。

外部来源会在批准之后变化或失效，因此外部来源成为 Citation 时必须同时持久化被引用片段的引文快照：引文正文、抓取时间与来源内容哈希。Citation 指向该快照而不是指向实时来源，导出与复查都使用快照；来源页面此后变化或不可访问不影响已批准版本的可复现性，只在诊断中标出来源已变化。内部 Chunk 的引文由 `dataset_version` 与 `chunk_id` 承担同样职责，不需要额外快照。

每次导出记录导出人、时间、格式、内容哈希与成功或失败。一个版本可导出多次。草稿非正式预览必须带明显标记，且不创建 DeliveryPackage 记录。

## 11. API、SSE 与错误边界

### 11.1 API 原则

- 身份来自后端认证会话，不接受前端自报角色。
- 路由授权和动作授权分别执行。
- 内容写入携带 `revision`。
- 业务状态拒绝、依赖失败和证据不足使用不同结果形状。
- 精确请求、响应和错误 Schema 由产品 OpenAPI 与测试维护。

### 11.2 第一阶段 SSE

第一阶段 SSE 只服务一次 ReviewRun 生成调用：

- 事件区分未校验增量与最终已校验结果。
- 事件带单调序号，消费端可丢弃重复或乱序事件。
- 生成期只写未校验分支；验证成功时用最终结果替换并清空草稿。
- 验证失败时显式撤回未校验内容并显示真实错误。
- 第一阶段不做 Tool 事件、完整运行轨迹和断线重连游标。

### 11.3 错误分类

至少区分：

- 文档解析、空内容、Embedding 和索引失败。
- Lexical / Dense 单路失败、检索零候选和过滤后空结果。
- Context 超预算。
- 模型鉴权、限流、超时和能力不支持。
- Structured Output、Citation、Finding 目标和依据资格校验失败。
- 乐观并发、非草稿写入、活跃运行期间写入和批准门拒绝。
- 用户取消。
- 第二阶段 Tool、沙箱、MCP、A2A 和安全阻止。

真实失败不能变成空候选、Mock 成功或静态成功结果。

## 12. Tool、安全与记忆设计

- Tool Runtime 统一执行 Schema、权限、确认、超时、取消、审计、幂等和结构化错误。
- Search 只发现候选来源，Browser 实际读取并保留 URL、标题、时间和定位。
- File Read 只访问本次运行批准的工作区，保留相对路径、版本、哈希和 locator。
- File Write 默认只访问 `run_id` 隔离暂存区，不修改正式需求或创建 DeliveryPackage。
- Code Tool 优先运行专用 Validator 或项目已有检查，不接受任意 Shell；输入只读、输出隔离、默认禁网、命令和环境白名单并限制资源。
- MCP 与 A2A 通过官方 SDK 或成熟适配器连接，仍须映射到内部权限、状态、错误、证据和审计。
- 产品至少消费一个真实、只读、可观察的 MCP 能力，不建设通用 MCP 市场。
- Search 发现的页面和所有 Tool Result 都是候选信息，必须先进入第 4.3 节的证据登记簿，再经支持性与证据资格校验才能成为 Citation；Code Tool 执行结果不得成为外部事实的 Citation。
- 至少提供一个按需加载的需求评审 Agent Skill；Skill 只能提供说明、资源和脚本，不能绕过 Tool Runtime。
- Multi-Agent 保留固定 RAG 和单 Agent 基线，按真实责任拆分，并显式处理委派、并行、失败隔离、证据合并和冲突裁决。
- 至少选择一个稳定责任契约，同时实现本地 Delegation 与远程 A2A 路径；远程路径由两个独立实现完成真实互操作，固定规范修订、SDK 和协议绑定，并处理 Agent Card、鉴权、版本、任务状态与错误差异。
- A2A 不改变权限、证据归属和最终结果责任人；Workflow 只用于确需显式状态、Checkpoint、恢复与人工介入的链路，不建设低代码画布。
- Conversation、Run State、短期摘要、长期偏好和业务知识分别建模。
- 长期偏好只保存用户明确确认的跨会话偏好，并提供查看、更新、删除和关闭；删除或关闭后不得继续注入。
- 模型推断、会话摘要、PRD 事实与 Tool Result 不能自动成为长期偏好，偏好不能成为 Citation。

关键运行记录至少关联输入身份、模型与策略版本、检索结果、Tool Call、状态变化、停止原因、Token、成本、延迟和结构化错误。质量比较必须在同一垂直切口与预算约束下覆盖固定 RAG、单 Agent 和 Multi-Agent，并能回到固定样例、运行记录、自动评估或人工判断。

## 13. 确定性验收不变量

第一阶段以下规则必须由确定性测试证明，不依赖 LLM Judge：

### 13.1 导入、条目与 Citation

- 导入 PRD 后条目覆盖和未映射内容可见；条目能回到 SourceArtifact 哈希和原文 locator，原文变化后不能静默沿用旧映射。
- AI 生成和自动导入条目保留来源并为 `proposed`；人写和从基线原样派生为 `confirmed`。
- 导入映射与人的直接输入不产生 `external_fact`；人不能升级为 `external_fact`，编辑外部事实正文会自动降级并清空 Citation。
- AI 外部事实 Citation 通过后为 `verified`；未通过时 `confirm_items` 拒绝，只能改类或删除。
- 产品意图不因无 Citation 被拒；外部事实缺 Citation 不能伪装成已支持。
- member 创建 Project 后成为 owner，初始空 Brief 与最小 Requirement draft 可启动冷启动路径；没有合格候选资料时必须产生证据不足结果，而不能伪造 Citation 或依赖失败。

### 13.2 Finding 与 Decision

- Finding 目标必须属于当前版本修订或固定分区；Brief 冲突 locator 必须解析到 ReviewRun 钉住的 Brief 修订。
- 内部 Finding 不伪造 Citation；外部事实冲突缺 Citation 时拒绝写入；影响推断允许无 Citation 但必须标记。
- `confirm_items` 不要求 Finding，可确认多条且不递增 `revision`；其余第一阶段 Decision 缺 Finding 时拒绝。
- 同一 Finding 只有一条活动 Decision，替换后旧记录可查。
- 目标删除后 `accept_suggestion / supplement` 拒绝，`reject / waive` 仍允许。
- 内容变化的 Decision 递增 `revision` 并使旧 ReviewRun 失去批准资格；`reject / waive` 不递增。
- 新运行的 Finding 必须重新 Decision，旧决定不会自动通过批准门。
- Decision 仅在 `draft` 可创建或替换。

### 13.3 批准、基线与交付

- 门禁运行 `proposed_count_at_start = 0`。
- 批准门拒绝未处理 Finding、`proposed` 条目、缺 Citation 外部事实、过期内容修订和过期 Brief。
- `evidence_decision = 拒答` 不阻断批准：两个候选池都为空的项目在全部 `evidence_gap` 被留理由 `waive` 后可以批准第一个基线。
- 诊断记录了取证或校验降级的运行被拒绝作为门禁运行，即使它以 `completed` 结束；零候选与过滤后空结果的运行仍有资格。
- 批准记录与 DeliveryPackage 能回到门禁运行当时的 `evidence_decision`。
- 提交预检与批准复检使用同一规则。
- Brief 修改使待批准版本过期后必须先退回 `draft`，不能直接以新运行批准。
- 批准记录能回到 ReviewRun、Brief 修订、`approved_decision_ids` 和 `approved_decision_set_hash`。
- 基线切换、旧版本 `superseded` 和批准审计原子完成；失败全部回滚。
- 同一 Requirement 有开放版本时拒绝再派生。
- DeliveryPackage 与不可变版本、Brief、Decision 集合和哈希一致；草稿不能生成正式包。
- 六类人工动作不能被 Agent、Tool 或系统管理员身份绕过。

### 13.4 索引、快照与并发

- 批准成功而索引失败时基线不回滚，`index_state=index_failed` 可重试。
- ReviewRun 固定需求修订、Brief 修订、`dataset_version`、可见已批准需求集合和开始时 `proposed` 数量。
- 派生版本不检索自身基线；只包含同项目其他 `indexed` 当前基线。
- `pending / index_failed` 基线不进入候选并在诊断中列明原因。
- `superseded` Chunk 不进入新 ReviewRun 候选。
- 下架一份已发布资料产生新的 `dataset_version`；同一 `dataset_version` 在任何时点解析出的全局候选集合完全相同。
- 非草稿写入、活跃 ReviewRun 期间写入和旧 `revision` 覆盖被拒绝且不留部分变化。
- Brief 修订历史 append-only，可按任何已钉住修订取回。

### 13.5 质量与真实依赖

- 直接 LLM、Lexical、Dense 和 RRF 使用同一输入、生成条件和预算比较。
- Golden Set 固定问题、期望来源、Finding 覆盖、无答案行为和数据版本。
- 真实模型、Embedding、PostgreSQL 和协议失败不会静默降级为 Mock。

## 14. 第二阶段验收契约

第二阶段除继续满足第 13 节外，还必须证明：

- 模糊想法经过可恢复追问形成 Brief 草案与需求补丁；Agent 不直接修改 Project Brief。
- `propose → Diff → 人确认 → apply` 对过期修订、重复请求、恢复重放和非草稿状态均安全，apply 后必须重新评审。
- `agentic` ReviewRun 产生的 Finding 与 `pipeline` 运行同受目标成员资格、依据资格、Decision 与批准门约束，不存在第二条 Finding 生产路径；需求形成类 Agent Run 不产生 Finding、不钉证据快照。
- 因步骤或预算上限提前停止的 ReviewRun 以 `completed` 结束但没有批准资格；停在等待授权的运行保持活跃、不可作为门禁运行，且可由发起者或 owner 取消后恢复 draft 写入。
- `agentic` ReviewRun 运行期间的人工介入只能授权取证，不能修改需求内容；内容补充经运行结束后的 `supplement` Decision 完成。
- 模型声明的来源必须属于本次运行的证据登记簿，未登记来源判为越界；登记簿在恢复与重放后仍单调增长且可解释。
- Code Tool 执行结果不能支撑 `external_fact` 或 `external_fact_conflict`，只能支撑标为推断的 `impact_inference` 或作为诊断依据。
- 外部来源 Citation 在来源页面变化或失效后仍能复现批准时的引文快照，导出结果不随外部来源漂移。
- 固定分区的 `addressed / not_applicable / needs_input` 状态可回查；`needs_input` 或无理由的 `not_applicable` 必须拒绝提交和批准，且不依赖模型是否报告对应 Finding。
- 从模糊想法启动的 Agent Run 只能绑定 editor 或 owner 已创建或选择的 Requirement draft；Agent 不创建正式 Requirement，也不绕过补丁确认门。
- File Read 能追踪接口与客户端资料来源；File Write 只写运行级暂存；受控 Code Tool 至少验证一项真实契约差异，并保留失败或超时结果。
- 用户能确认、查看、更新、删除和关闭长期偏好；关闭或删除后不再注入，偏好不成为 Citation。
- 同一责任契约可对照本地 Delegation 与远程 A2A；远程路径完成两个独立实现的真实互操作，并保留任务状态、证据归属、错误和最终责任。
- 固定 RAG、单 Agent 与 Multi-Agent 在相同业务切口上比较质量、成本、延迟和失败定位；增加 Agent 数量本身不算收益。
- 六类人工动作、正式需求写入门、证据规则和真实失败边界在 MCP、Tool、Skill、Multi-Agent、A2A 与恢复路径中均不能被绕过。
- 修改一个业务规则、工具或 Agent 责任后，能运行受影响的确定性测试、Golden Set 与端到端回归。

## 15. 固定垂直切口

验收 fixture 的 Project 为电商 App；主 Requirement 为“售后入口”。第一阶段 v1 从 Target Requirement fixture 导入并批准为基线。同项目存在“订单状态展示”Requirement 的已批准、已索引基线，使 `approved_requirement` 池主路径非空，并稳定支撑一条与售后入口规则冲突的样例。真实产品不绑定电商主题，新 Project 可以按第 3.2 节的冷启动路径从空 Brief 和空检索池开始。

第二阶段“售后接口 v2 与多端契约一致性评审”是同一主 Requirement 的新 RequirementVersion：

- `source_channel` 被增加或收紧。
- Web 与 Flutter 入口可见性需要一致。
- File Tool 读取 PRD、OpenAPI、客户端模型、配置和测试入口。
- Code Tool 运行允许的契约校验或定向测试。
- Agent 通过补丁 Diff 写入，影响结论形成 Finding，由人决策和批准后导出增量交付包。

该切口在固定 RAG、单 Agent 和 Multi-Agent 间保持不变，用于控制比较变量，不构成产品主题白名单。
