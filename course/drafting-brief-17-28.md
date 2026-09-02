# 第 17–28 节起草基准（临时）

> **临时文档。** 本文只服务于第 17–28 节的起草过程。第 28 节完成、`learning-path.md` 与 `knowledge-map.md` 的对应条目更新后即删除，不进入长期文档集。
>
> **使用方式。** 起草 17–28 期间，课程编号、切分、交付和非目标以本文为准；写完一节再把该节的最终介绍同步回 `learning-path.md`，起草过程中不改动它。若本文与 `SPEC.md` 冲突，以 `SPEC.md` 为准并在此处修正。对象、状态与枚举的规格在 `SPEC.md` 第 4 节，本文只记切分与起草决定，不复制规格。

## 这一段课程要回答什么

第 7–16 节已经交付固定 RAG 核心链，终点是“模型声明的来源属于本轮允许集合”。第 17–28 节把它变成能批准、能交付、能迭代的产品：

```text
Citation 成员资格（已完成，第 16 节）
→ Citation 支持性
→ 证据充分性 / Refusal / 补充问题
→ 需求对象模型与三分（来源 / 引用 / 决策）
→ 结构化需求草稿（固定表单补全 / 导入 PRD 映射）
→ Finding 定位、Decision、条目级 Diff
→ 不确定性表达
→ 身份
→ 两层产品 RBAC
→ 知识资料 API、资料生命周期、approved_requirement 与两个检索池
→ 需求版本生命周期、批准门、基线切换、事务后索引、交付包
→ ReviewRun、Review API、证据快照与 SSE
→ Web 工作台联调
```

三层可信边界必须严格保持，任何一节都不许越界：

| 节 | 回答 |
| --- | --- |
| 16 | 模型声称的来源是否属于本轮允许集合？ |
| 17 | 来源片段是否支持该声明？ |
| 18 | 所有已支持的声明是否足以支撑当前结论？ |

第 19–21 节再把这些结论落到需求对象上；第 21 节的“目标成员资格校验”与第 16 节的“来源成员资格校验”是同一编程技巧的两次领域应用，正文要点明这一点，但不为它在 `rag_core` 建通用能力。

## 两个检索池 + 两条入口

产品有两个检索池和两条需求入口，语义各不相同，任何一节都不能把它们混写：

```text
【全局知识库】系统 admin 上传知识资料
→ 解析、清洗、Chunk、Embedding、诊断
→ staged
→ admin 发布
→ 新 dataset_version
→ 之后才成为 Retriever 候选

【项目检索池】owner 批准 RequirementVersion
→ 批准事务：baseline_version_id 切换 + 旧基线 superseded + 审计
→ 事务后独立步骤：Chunk、Embedding → index_state = pending | indexed | index_failed
→ indexed 后以 approved_requirement 角色进入同 Project 候选

【入口 A】固定表单创建
→ 人写条目（confirmed）→ 检索 → 固定生成补全草稿（proposed）

【入口 B】导入 PRD（粘贴 / 上传）
→ SourceArtifact（哈希、locator）→ 映射为 proposed 条目 + 未映射诊断

两条入口汇入同一条循环：
处理 proposed → ReviewRun → Finding → Decision → 再评审
→ 最后一轮只剩 reject / waive → 提交 → 批准 → 事务后索引 → 导出
```

四条硬约束：

- 当前需求版本是被评审对象，不进入 Retriever 候选池，不能成为 Citation Candidate；派生版本评审时排除自身旧基线。
- 上传本身不改变全局候选池；只有发布动作产生新的 `dataset_version`。这条规则不约束项目检索池。
- 项目检索池由 `approved_requirement_version_ids` 按版本身份过滤；`superseded` 版本因不在集合内自然离开，不做角色重标。
- 导入映射与人的直接输入永不产生 `external_fact`；它只由系统赋予（AI 草稿携带已校验 Citation，或 `accept_suggestion` 写回）。

## 已确定的决定

起草时直接采用，不重新讨论。

1. **25 与 27 按生命周期切分**：25 归知识资料流（含 `approved_requirement` 角色与两个池子的说明），27 归评审流（ReviewRun 单一生命周期）。26 单独承担版本生命周期与批准门，不并入 27——ReviewRun 与 RequirementVersion 是两个独立状态机，合写会让一节承载两条生命周期。
2. **ReviewRun 终态只有三个**：`completed / failed / cancelled`。证据充分性是业务结论，作为 `completed` 上的 `evidence_decision` 字段承载，不提为终态。失败原因作为 `failure_reason` 枚举，不扩成更多状态。ReviewRun 结果不驱动任何版本状态迁移。
3. **知识资料在暂存时完成切分与向量化**，发布是一次廉价的版本翻转。已批准版本的索引则在批准事务之后执行，失败落 `index_failed`、可重试、不回滚批准；两者都不需要队列（第一阶段不引入 Redis）。
4. **第 17 节做两段校验**：确定性引文定位在前，模型支持性判断在后。只做前者会让 17 退化成第 16 节的加强版，失去独立核心问题。
5. **第 28 节新建文件**，位于 `course/project/stage-1-rag-application/`，与 `rag-review-assistant.md` 并列。理由是学习路径的状态标记按编号对应文件；28 可写而 33 等待前置，共用一个文件无法标状态。
6. **认证使用 Cookie Session，不用 Bearer Token。** 原生 `EventSource` 无法设置请求头，Bearer 方案会迫使 token 进 query string（进访问日志）或放弃 `EventSource` 自行解析流。单一同源 Web 工作台、无移动端，Bearer 的好处一个都用不上。这条决定属于第 23 节，并向第 27 节的传输实现传导，正文中要说明这层传导关系。
7. **两层角色、权限取交集**：系统 admin / member 与项目 owner / editor / viewer；系统 admin 不因系统角色获得项目批准权。动作矩阵以 `SPEC.md` 第 2 节为准，第 24 节只解释规则与两层授权决定，不复制矩阵。
8. **`revision` 只随内容变化递增**，Decision 不递增；它同时是乐观并发判据与“旧 ReviewRun 是否仍可用于批准”的判据。不建单编辑者锁。
9. **批准门在提交时预检、批准时复检，同一规则**：门禁运行 = 当前 `revision` 上最近一次 `completed` 且 `brief_revision` 匹配的运行，`proposed_count_at_start=0`，全部 Finding 的活动 Decision 只能是 `reject` / `waive`。正文要讲清 `accept_suggestion` / `supplement` 递增 `revision` 如何逼出“最后一轮零内容变更”。
10. **DeliveryPackage 只作导出记录**，不写第四套生命周期；只从 `approved` / `superseded` 导出，草稿只能生成带标记的非正式预览。
11. **前端选型**（第 28 节联调使用，25/26/27 只写契约不写前端）：

   | 关注点 | 选择 | 理由 |
   | --- | --- | --- |
   | 服务端状态 | TanStack Query | 本应用状态几乎全是服务端状态 |
   | 客户端状态 | 页面级 `useReducer`，不建全局 store | SSE 流是页面级的；跨路由续跑是产品决定而非前端决定，出现后再引入 Zustand |
   | 路由 | React Router | 够用；TanStack Router 的 `beforeLoad` 更贴合路由级守卫，但不值得为它换栈 |
   | API 类型 | 从 FastAPI OpenAPI 生成 | 让 25/26/27 的契约被强制而非被描述，漂移在类型检查阶段暴露 |
   | 组件库 | 无样式可访问类（Radix / shadcn） | 条目来源与确认状态、Finding 支持状态、Diff、部分回答都无现成组件；重样式库会挡路，且需控制到 ARIA 层 |
   | 表单与上传 | react-hook-form + zod | schema 镜像后端错误契约，固定表单、导入 PRD 与知识资料上传在类型层面分开 |

## 跨节共享契约

只在指定的一节定义，其余节引用，不重复解释。

### 对象主链与三分（第 19 节定义）

`Project → Requirement → RequirementVersion → RequirementItem`；`item_key` 跨版本稳定、`revision` 只随内容递增、`brief_revision` 单调递增且 append-only。来源（`provenance`）、引用（`citations`）、决策（Decision）三分：产品意图不因缺 Citation 被拒，外部事实不因人的确认免除 Citation。固定 `section_key` 枚举与 `statement_kind` / `confirmation_state` / `citation_state` 的取值以 `SPEC.md` 第 4 节为准。

### 条目字段写入路径（第 20 节定义）

`external_fact` 只由系统赋予；人只能降级不能升级，编辑正文自动降级并清空 Citation；`confirmation_state` 在创建时确定，人写与原样派生即 `confirmed`，AI 与导入为 `proposed`。第 21 节的 `accept_suggestion` 写回 Citation 是这条路径的第二个入口，由第 20 节预留、第 21 节使用。

### Finding 与 Decision（第 21 节定义）

五类 `finding_kind` 的目标与依据资格、阻断规则；五类 `decision_type`，同一 Finding 只有一条 `active` Decision、可替换并保留 `deactivated`；`confirm_items` 不指向 Finding、不递增 `revision`。第 26 节的批准门直接消费本节的“活动 Decision”与“门禁运行”定义。

### 版本状态机与批准门（第 26 节定义）

```text
draft → pending_approval → approved → superseded
pending_approval → draft（owner 退回 / 撤回）
```

派生状态“评审中 / 待补充 / 已交付”由查询得出。编辑规则、乐观修订号、单开放版本、Brief 修改的失效效果、批准事务与事务后索引都在本节定义；第 27 节只引用“活跃 ReviewRun 期间拒写”。

### ReviewRun 状态机（第 27 节定义）

```text
submitted → retrieving → generating_unverified → validating
                                                    ↓
                              completed | failed | cancelled
```

- `completed` 携带 `evidence_decision`：可回答 / 部分回答 / 拒答。
- `failed` 携带 `failure_reason`：鉴权失败 / 限流 / 超时 / 能力不支持 / 结构化校验失败 / 内部失败。
- `validating` 内部依次执行第 16 节成员资格、第 17 节支持性、第 18 节充分性、第 21 节目标成员资格与依据资格四层校验，结果进诊断字段。**状态机不镜像机制链**——后续增加校验层不改状态机。
- 检索零候选是“完成且拒答”，不是 `failed`。
- 取消只在 `retrieving` 与 `generating_unverified` 期间可请求；进入 `validating` 后按完成处理。
- SSE 连接断开是传输层事件，不改变任何业务状态。

### 知识资料生命周期（第 25 节定义）

```text
uploaded → parsing → parse_failed
                   → staged → published → superseded
```

- `parsing` 失败必须落到 `parse_failed` 并暴露明确错误，不能停在 `parsing`。
- 同一 `document_id` 的新版本发布后，旧版本进入 `superseded`。
- 切分与向量化在进入 `staged` 前完成。
- 一次发布动作产生一个 `dataset_version`，覆盖该次发布的文档集合；`dataset_version` 是快照身份，文档是它的成员。
- `approved_requirement` 来源角色与 `index_state` 在本节定义，触发时机在第 26 节；两个池子、两个快照身份在本节说明。

### 证据快照与运行的绑定（第 25 / 26 节定义规则，第 27 节定义绑定时机）

ReviewRun 在进入 `retrieving` 时钉住 `requirement_version_id + revision`、`brief_revision`、`dataset_version`、`approved_requirement_version_ids`（只含 `indexed`，排除自身基线）与 `proposed_count_at_start`，之后全部检索与校验都在该快照内进行，报告中带上它。

不做这条绑定的后果：admin 发布、其他 Requirement 批准与本次评审并发时，中途变化会改变候选池，Citation 无法复现，批准门无法判断旧运行是否仍有效，冻结的 acceptance Golden Set 失去意义。

`course/mechanisms/retriever-contract.md` 中 `dataset_version` 目前只是实验运行身份；第 25 节要说明它在产品中升级为 Metadata Filter 的一部分，参与“两路检索前应用过滤”这一步，`approved_requirement_version_ids` 按 `document_version` 集合过滤是同一步的第二个过滤条件。

### SSE 事件契约（第 27 节定义）

- 事件必须区分“未校验分支的增量”与“最终已校验结果”，后者是替换语义而非合并语义。
- 事件带单调递增序号，允许消费端幂等丢弃乱序或重复事件。第一阶段不做断线重连游标（第 74 节的责任），但序号本身成本极低。
- 客户端把未校验草稿与已校验 Finding 放在两个独立字段：生成期只写前者；`validating` 成功时写后者并清空前者；失败时清空前者并写失败。**撤回等于丢弃一个分支，不存在反向补偿逻辑**，也就不可能出现未校验内容残留在界面上。

## 逐节起草基准

每节固定：类型、核心问题、学习者已有输入、交付、非目标。实验篇的单变量在此登记，起草时直接沿用。

### 17 Citation 支持性校验

- **类型**：机制篇 + 实验篇
- **核心问题**：Citation ID 合法之后，来源中的那段内容是否真的支持对应结论？
- **已有输入**：第 16 节交付的结构化结论与成员资格检查结果。
- **交付**：`VerifiedCitation`——声明、证据片段、原文定位、支持档位、理由。
- **两段校验**：
  1. 确定性定位。模型在声明 `source_id` 的同时必须给出逐字引文；应用把引文拿回对应 chunk 原文做归一化后精确匹配，成功才产生 locator。失败直接判定，不进入第二段。这一段零成本挡住编造引文，并顺带产出原文定位。
  2. 模型判断。引文确实存在时，判断它是否支持该声明。这一步无法用程序替代。
- **支持档位必须含“无法判定”**，且该档在结果中可见。校验器自身失败不得默认算作支持——这是“不静默降级”在本节的具体形态。
- **它是业务校验器，不是评估 Judge。** 固定 Prompt 版本与 Schema，结果进业务结果。LLM-as-Judge 的人工校准在第 108 节、第二阶段，本节正文要有一句显式区分。
- **成本**：一次 run 的所有声明合并为一次调用，Token 与成本进诊断。
- **对第 16 节的扩展**：本节把生成 Schema 从“声明 source_id”升级为“声明 source_id + 逐字引文”。由本节承担这次扩展并解释为什么现在才加（第 16 节时还没有支持性概念，加了也无人消费）；`course/mechanisms/trusted-generation.md` 末段已有一句向后指引。
- **实验单变量**：冻结上游，只替换证据片段。四个 fixture——真支持 / 引文真实但与声明无关 / 引文与声明矛盾 / 引文根本不存在。最后一个由第一段拦下，前三个走到第二段，顺带让学习者看清两段各自能证明什么。
- **非目标**：不判断整份结论的充分性；不做 Refusal 决策；不设计界面；不引入产品对象术语。
- **代码落点**：`source/packages/rag_core/`

### 18 证据充分性、Refusal 与补充问题

- **类型**：机制篇 + 实验篇
- **核心问题**：若若干 Citation 都成立，是否足以支撑当前结论？缺什么？
- **已有输入**：第 17 节交付的 `VerifiedCitation` 集合及其支持档位。
- **交付**：`EvidenceDecision`——可回答 / 部分回答 / 拒答，以及结构化 gap。
- **补充问题是 gap 的输出形式，不是独立生成链。** 先有结构化 gap（缺哪类事实、哪个来源角色本应覆盖它、影响哪几条结论），问题是 gap 的渲染。本节若长出第二条生成流水线就是切分失败，应停下重新划界。
- **本节仍用 Claim 与 EvidenceDecision 表达**，不提前使用 Finding / Decision 术语；第 21 节把 gap 映射为 `evidence_gap` Finding。
- **实验单变量**：冻结一切，只从 `knowledge_scope` 移除一份关键文档，观察决策从“可回答”滑向“证据不足”。
- **非目标**：不定义运行状态；不设计界面；不做补充答案的回填闭环（回填由第 21 节的 `supplement` Decision 承担）。
- **代码落点**：`source/packages/rag_core/`

### 19 需求对象模型：项目、需求、版本、条目与基线

- **类型**：概念篇
- **核心问题**：评审结论要挂在什么上面、由谁批准、怎样交付？
- **已有输入**：第 18 节的结论与 gap；第一阶段项目篇的业务场景。
- **交付**：对象主链、基线指针、稳定身份三件（`item_key`、`revision`、`brief_revision`）、来源 / 引用 / 决策三分的判据。
- **必须讲清的两个“为什么不”**：为什么 Brief 是 Project 上的字段集合而不是特殊 Requirement；为什么基线只在 Requirement 粒度、全产品基线是非目标。
- **必须讲清的一个死锁**：若允许人把条目标为 `external_fact` 或允许导入器产生它，批准门会在“缺 Citation 的外部事实”上卡死；这是第 20 节写入路径的动机。
- **非目标**：不讲实现、不定义 API、不画状态机（状态机在第 26 节）、不讨论 Agent 写入。
- **代码落点**：无；本节是第 20、21、26 节的概念前置。

### 20 结构化需求草稿：从固定表单或已有 PRD 到条目

- **类型**：机制篇 + 实验篇
- **核心问题**：用户手里只有一份 PRD 或几个表单字段，怎样变成有分区、有来源、可评审的条目？
- **已有输入**：第 19 节对象模型；第 7–16 节固定 RAG；第 5 节 Structured Output。
- **交付**：第二个 Prompt 族（补全草稿）的 Schema 与校验；导入映射器（SourceArtifact → 条目 + 未映射诊断）；条目字段写入路径。
- **两条入口共享一条循环**，本节要画清汇合点：无论入口 A 还是 B，产出都是 `draft` 版本上的 `proposed` 条目，下一步都是处理 `proposed`。
- **固定步骤，不是对话式 Agent**：补全草稿是“检索 → 一次生成 → 校验”，没有追问循环；模糊想法与追问属于第 52 节。
- **实验单变量**：冻结检索与模型，只改变输入来源——同一需求分别走固定表单与导入 PRD，比较条目的 `provenance`、`statement_kind`、`confirmation_state`、`citation_state` 与未映射诊断；再加一个 fixture 让 AI 草稿携带不可验证 Citation，观察条目停在 `proposed + unverified` 且 `confirm_items` 拒绝。
- **非目标**：不做 Finding；不做 Decision；不做批准；不建独立的 Brief 编辑界面。
- **代码落点**：`source/apps/review_assistant/`（领域 Schema、migration 在本节首次落地，先于 API 与认证，由脚本与确定性测试驱动）

### 21 Finding 定位、决策记录与条目级差异

- **类型**：机制篇 + 实验篇
- **核心问题**：第 18 节的缺口与结论要落在需求的哪个位置、由谁处理、处理后需求怎样变化？
- **已有输入**：第 18 节 EvidenceDecision 与 gap；第 20 节的条目与写入路径。
- **交付**：Finding（五类、目标成员资格、按类型依据资格、阻断规则）；Decision（五类、活动替换、`confirm_items`）；按 `item_key` 对齐的条目级 Diff；批准门预检所需的“门禁运行”定义。
- **目标成员资格校验与第 16 节是同一技巧**：正文点明，但不在 `rag_core` 建通用能力。
- **实验必须覆盖七种场景**：无 Finding 的 `confirm_items`；有 Finding 的四类 Decision；替换活动 Decision（旧记录 `deactivated`）；`accept_suggestion` 递增 `revision` 并把已验证 Citation 写回条目；同一轮连续接受多条建议后一次重跑（新运行产生新 Finding，界面按 `(finding_kind, item_key)` 提示沿用但仍是新 Decision）；对目标已删除的 Finding 做 `accept_suggestion` / `supplement` 被拒绝、`reject` / `waive` 仍允许；门禁只统计门禁运行的 Finding（上一轮同目标的 Decision 不算）。
- **非目标**：不做批准动作本身（第 26 节）；不做 API（第 27 节）；不做 UI。
- **代码落点**：`source/apps/review_assistant/`

### 22 AI Native 界面与不确定性表达

- **类型**：概念篇
- **核心问题**：用户如何在需求正文旁区分生成内容、已验证结论、推断、证据不足和真实系统失败？
- **交付**：UI 表达原则与结果层级。本节同时是第 27 节状态机与第 28 节联调必须满足的需求来源。
- **核心原则：可信状态是逐条的，不是整份的。** 三层表达——版本顶部一句话说明本次评审能支撑到什么程度；每条条目自带来源与确认状态、每条 Finding 自带支持状态与推断标记；每个补充问题挂到对应 gap 与受影响的条目。
- **部分回答的设计要求**：partial 的本质是“有些结论现在就能用，有些还差一个具体答案”，界面必须同时回答这两件事。只显示一条“证据不足，请谨慎参考”的警告条不合格——它把判断责任推回给用户。
- **Decision 是界面的一等对象**：用户在 Finding 旁直接做决定，看到决定引起的条目变化；不把决策藏在报告末尾的按钮里。
- **不确定性不得只靠颜色和图标承载，必须有文字。** 既是可访问性，也因为后续 bad case 讨论依赖截图与运行记录。
- **非目标**：不写具体组件、不定义运行状态名、不建设通用 AI 工作台。
- **可验收判据（交给第 28 节执行）**：给一个 partial 的 run，用户在不打开诊断区的前提下，能说出哪几条 Finding 可直接 `reject` / `waive`、回答哪个问题能把剩下的补齐。

### 23 用户身份与认证

- **类型**：机制篇；验证并入第 25 节实验
- **核心问题**：登录、凭证校验、会话签发、失效和登出如何形成后端可依赖的身份事实？
- **交付**：后端可依赖的 principal，而不是前端自报角色。
- **使用 Cookie Session**，理由见“已确定的决定”第 6 条。
- **正文要讲清一层传导**：认证方式的选择会实质约束 API 与传输实现——原生 `EventSource` 无法设置请求头，因此第 23 节的选择直接决定第 27 节的 SSE 能否用标准浏览器 API。这是“身份机制不是孤立的”的一个真实例子，比抽象讲 token 生命周期更有说服力。
- **非目标**：不做注册审批、找回密码、多因子、OAuth、第二阶段 Tool 权限。
- **代码落点**：`source/apps/review_assistant/`

### 24 系统角色与项目成员角色：产品 RBAC 与 Tool 权限的区别

- **类型**：机制篇；验证并入第 25 节实验
- **核心问题**：系统 admin / member 与项目 owner / editor / viewer 分别能看什么、做什么？为什么取交集？
- **交付**：路由级与动作级两层授权决定；“只能由人触发”的动作清单（批准、导出、成员管理、编辑 Brief）。
- **必须显式对照第 39 节**：本节回答“界面上谁能点什么”，第 39 节回答“模型能执行什么”。两者概念独立，不能相互替代或合并实现；Agent 以发起者的项目角色行动，没有独立角色。
- **必须讲清一个反直觉**：系统 admin 不能批准项目需求，除非先成为项目 owner；理由是全局知识治理与项目决策是两种责任。
- **非目标**：不做可配置审批链、委托与通知；不做两层之外的权限模型；不做多租户。
- **代码落点**：`source/apps/review_assistant/`

### 25 知识资料 API 与资料生命周期

- **类型**：机制篇 + 实验篇
- **核心问题**：资料怎样从上传变成可检索候选？已批准需求怎样成为另一种候选？
- **交付**：知识资料 API 的请求、响应、错误形状；资料生命周期状态；`dataset_version` 的产生规则；`approved_requirement` 来源角色与 `index_state` 的定义；两个池子、两个快照身份。
- **本节第一次引入 FastAPI**：这条流确定性、无流式、无模型调用，认知负担最小，适合建立请求/响应/错误分层与依赖注入。它也符合真实数据依赖顺序——没有发布过 `dataset_version`，评审根本检索不到东西。
- **解析诊断的归属**：诊断对象的形状是 `rag_core` 从第 8 节起就有的输出，本节只负责存储与暴露，不重新定义。
- **`rag_core` 只扩两处**：`SourceRole.approved_requirement`、Metadata pre-filter 按 `document_version` 集合过滤。正文说明为什么只扩这两处。
- **实验**：合并承担第 23、24 节的验证——真实登录取得会话，系统 admin 与非成员 member、项目 owner / editor / viewer 分别调用发布端点、批准端点与导出端点，观察 403 同时出现在路由层与动作层，并观察系统 admin 在未加入项目时批准被拒。授权缺陷只在真实请求里现形，但为它单开两个薄实验不划算。
- **非目标**：不写评审流的 API；不写 SSE；不写前端；不实现批准事务（第 26 节）。
- **代码落点**：`source/apps/review_assistant/`

### 26 需求版本生命周期、人工批准、基线切换与交付语义

- **类型**：机制篇
- **核心问题**：一个版本什么时候可以被批准、批准后发生什么、交付包从哪里来？
- **已有输入**：第 19 节对象模型；第 21 节 Finding / Decision 与门禁运行定义；第 25 节 `index_state` 与项目检索池。
- **交付**：四个持久状态与三个派生状态；编辑规则、乐观修订号、单开放版本；批准门不变量（预检 = 复检）；批准事务边界与事务后索引；派生新版本；DeliveryPackage 导出语义。
- **只跟踪一条主流**：草稿 → 提交 → 批准 → 基线切换 → 事务后索引 → 从不可变版本导出。退回 / 撤回、Brief 修改的失效效果、索引失败重试作为主流上的分支写，不另起小节。
- **必须讲清两个边界**：为什么索引不在批准事务内（索引是外部服务调用，失败不应回滚一个已完成的人工决定）；为什么派生版本评审时排除自身基线而交给 Diff（否则检索会制造“与旧版本冲突”的噪声）。
- **验证**：本节的规则全部由确定性测试证明（`SPEC.md` 第 14 节第一阶段验收契约中与状态、并发、批准门、索引、导出相关的条目），不依赖模型；测试在第 28 节联调前已存在。
- **非目标**：不做 ReviewRun 状态（第 27 节）；不做 UI；不做可配置审批链；不做归档。
- **代码落点**：`source/apps/review_assistant/`

### 27 ReviewRun、Review API 与 SSE 事件契约

- **类型**：机制篇 + 实验篇
- **核心问题**：一次评审此刻处于什么状态，客户端据此显示什么？
- **交付**：Review API 契约、ReviewRun 状态机、证据快照绑定时机、SSE 事件契约、增量撤回语义。错误形状复用第 25 节已建立的分层。
- **含未校验增量的撤回语义**：它是状态迁移在客户端的投影，属于状态语义而非 UI 实现细节，因此归本节而不归第 22 或 28 节。
- **与第 26 节的接口**：只引用“活跃 ReviewRun 期间拒写”与“`accept_suggestion` / `supplement` 使当前运行失去批准资格”，不重讲批准门。
- **实验单变量**：同一请求，分别制造正常完成、证据不足、结构化校验失败和用户取消，观察四种情况下的事件序列与终态差异；再加一个 fixture 在运行中修改 Brief，观察运行照常完成但失去批准资格。
- **非目标**：不做心跳、断线重连游标、Tool 事件、多步骤运行轨迹（全部属于第 71–74 节）；不写前端实现。
- **代码落点**：`source/apps/review_assistant/`

### 28 需求工作台集成检查点

- **类型**：项目篇，新建文件于 `course/project/stage-1-rag-application/`
- **核心问题**：怎样把需求创建 / 导入、评审、决策、批准、导出与知识管理接入同一 Web 工作台？
- **交付**：最小真实前后端联调与验收证据。
- **必须显式声明的非目标**：不做 Golden Set、不做四路对照、不设质量门槛、不做需求变更题——全部属于第 33 节。本节只验证闭环能真实跑通。
- **引用纪律**：只引用 `SPEC.md` 中与联调相关的几条（两层角色、上传暂存发布、两条入口、批准门、增量流式与最终校验、导出），质量门槛部分一个字不碰，直接指向第 33 节。
- **至少包含的验收项**：
  - 系统 admin 上传 → 查看解析诊断 → 暂存 → 发布 → 产生新 `dataset_version`，且发布前候选池不变。
  - editor 走固定表单与导入 PRD 两条入口，得到同一形态的 `draft` 版本与 `proposed` 条目；导入条目能回到原文定位，未映射内容可见。
  - 处理 `proposed` → 运行评审 → 增量流式 → 最终校验替换 → Finding 挂在条目 / 分区 / 版本上；校验失败时未校验增量被显式撤回，界面无残留。
  - 对 Finding 做 Decision，`accept_suggestion` 后 `revision` 递增、旧运行失去批准资格、界面提示需重新评审。
  - 最后一轮只剩 `reject` / `waive` → editor 提交 → owner 批准 → 基线切换 → 索引状态可见 → 导出 DeliveryPackage；草稿导出只得到带标记的非正式预览。
  - 从基线派生新版本，Diff 按 `item_key` 对齐；派生版本评审的快照不含自身基线。
  - viewer 看不到也调不到编辑、评审、批准、导出动作；未加入项目的系统 admin 看不到该项目的批准动作。
  - 第 22 节的 partial 判据：不打开诊断区即可说出哪些 Finding 可处理、回答哪个问题能补齐剩下的。

## 需要同步修改的既有文档

写作过程中逐项完成，完成后在此打勾；全部完成即可删除本文。

- [ ] `course/learning-path.md` 第 28 条目：链接指向新建的项目篇文件。
- [ ] `course/learning-path.md` 第 17–28 条目：每节写完后按最终交付重写介绍（当前介绍是起草前基准）。
- [ ] `course/knowledge-map.md`：各节正文落地后把对应节点的“学习入口”从“待编写”改为实际链接。
- [ ] `course/project/stage-1-rag-application/rag-review-assistant.md`：第 28 节文件建立后，在“分段实现顺序”第 12 步加一句指向它。

## 冻结规则

- **不新增课程编号。** 17–28 是固定的十二个编号，起草期间不许插节、不许拆节。若某节确实装不下，先回本文调整切分，再动笔。
- **不扩展知识地图。** 除上方清单里的调整外，起草 17–28 期间不向 `knowledge-map.md` 增加节点。新出现的知识先判断能否合并进已有条目。
- **不复制 SPEC。** 枚举、字段、验收契约以 `SPEC.md` 第 4 节与第 14 节为准，正文引用、不抄写；发现 SPEC 有误先改 SPEC。
- **超出范围的想法记在这里，不写进正文。** 起草中冒出的扩展能力（Reranker、文档删除与 Citation 失效、可配置审批链、Requirement 归档、自定义分区、Brief 版本界面、跨版本知识治理、断线重连、Agent 写入）一律不进第一阶段，它们在知识地图里已有“扩展”“非目标”或第二阶段的位置。
- 本文只记决定，不记进度、不记讨论过程。第 28 节完成且上方清单清空后删除本文。
