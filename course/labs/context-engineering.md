# 从 RetrievalResult 到 BuiltContext

> 这是 [检索名单怎样变成模型本轮 Context](../mechanisms/context-engineering.md)的实验篇。它直接接住[固定 Retriever 控制与诊断实验](retriever-contract.md)的真实 `RetrievalResult`，继续使用 `order_rules.md` 和 `surface_match=申请售后`，不更换材料制造更理想的 Context。

本文只回答：怎样在真实 PostgreSQL、真实 Embedding 和固定 Retriever 上保持候选不变，只改变 Evidence 分区预算，观察同一条来源为什么 included、dropped，或者不再成为 Citation Candidate？

本实验能证明当前环境中的真实 Retrieval → Context 链，以及确定性测试守住的身份、位置、预算和证据资格契约。它不能证明某个预算具有最佳生成质量，也不调用 Chat 模型验证模型是否会使用证据。

## 1. 固定材料、问题和观察边界

本实验主路径始终固定：

```text
资料：source/apps/review_assistant/fixtures/rag/ingestion/order_rules.md
问题集：source/apps/review_assistant/fixtures/rag/retrieval/retrieval_queries.json
dataset_version：rag-retrieval-exploration-1.0.0
query_id：surface_match
query / requirement_text：申请售后
范围：after_sale + reference_knowledge + current_evidence
```

当前 structure-aware Chunker 产生两个真实 Chunk：

| Chunk | 内容 |
| --- | --- |
| 当前订单状态规则 | 仅已支付且已完成的订单可申请售后；虚拟商品不进入售后流程 |
| 接口与客户端约束 | 售后接口 v2 必须提供 `source_channel`；Flutter 客户端使用相同入口可见性规则 |

主路径不读取 `source/demos/llm_context_lab/context_cases.json`，也不加入历史评审、Agent Summary 或另一段长 PRD。资料不足以稳定展示压缩时，第 7 节使用明确标记的确定性机制假设；该假设不参与真实检索质量证明。

## 2. 运行前准备

本实验承接[固定 Retriever 控制与诊断实验](retriever-contract.md)。开始前确认：

- `DATABASE_URL` 指向第 11–14 节使用的 PostgreSQL Database；
- FTS 与 pgvector migration 已执行；
- `.env` 中真实 Embedding key、endpoint 和 model 可以调用；
- 前置的 `surface_match` Retriever 基线能够完成；
- 不会在真实依赖失败后回退到内存候选、Mock 或假向量。

在仓库根目录检查：

```bash
set -a && source .env && set +a
psql "$DATABASE_URL" -c "SELECT current_database(), current_user;"
psql "$DATABASE_URL" -c "\dt review_assistant.rag_chunks"
psql "$DATABASE_URL" -c "\dt review_assistant.rag_chunk_embeddings"
```

再核对当前业务文档的 Chunk 身份：

```bash
psql "$DATABASE_URL" -P pager=off -c "
SELECT chunk_id, document_id, document_version, left(content, 60) AS content
FROM review_assistant.rag_chunks
WHERE document_id = 'KR-ORDER-STATE'
ORDER BY document_version, chunk_id;
"
```

干净课程数据库应只保留当前两个身份。若同一 `document_id` / `document_version` 存在重复内容和旧 `chunk_id`，不要盲目删除产品数据；使用干净课程数据库，或先按明确文档更新策略处理旧 Chunk。demo 会显示当前 fixture IDs，出现其他候选时给出 warning 并返回退出状态 `1`，避免把脏数据去重误解成 Context 策略效果。

准备环境并检查入口：

```bash
uv sync
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --help
```

入口会幂等写入当前两个 Chunk 和当前 Embedding 空间的向量。它不执行 migration、不清空表，也不调用 Chat 模型。

## 3. 唯一主入口、默认值和退出状态

本节唯一主入口是：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --query-id surface_match \
  --policy full_context \
  --verbose
```

上游 Retriever 固定为前置实验的基线：

| 控制 | 固定值 |
| --- | ---: |
| lexical `candidate_k` | `5` |
| dense `candidate_k` | `5` |
| 两路 threshold | `None` |
| `rrf_k` | `60` |
| `final_top_k` | `3` |
| `knowledge_scope` | `after_sale` |

本实验不提供这些上游参数作为主变量。要研究候选池和最终截断，应回到[固定 Retriever 控制与诊断实验](retriever-contract.md)；这里从已经固定的 `RetrievalResult` 开始。

Context 参数为：

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `--query-id` | `surface_match` | 从共享问题集选择固定问题；本节仍显式传入 |
| `--policy` | `full_context` | 选择 Context Policy 基线 |
| `--evidence-budget` | 未覆盖 | 只覆盖所选 Policy 的 Evidence 分区预算 |
| `--log-format` | `compact` | 可切换 `verbose`、`json` 或 `quiet` |
| `--verbose` | 关闭 | 展开最终 `BuiltContext` |

`full_context` 当前有效配置是：

```text
total token budget        2200
requirement section        600
evidence section          1000
history section            300
agent_summary section      220
other section               80
allow_compression        false
max_source_tokens          None
```

主路径只有 Requirement 与 Evidence；其他分区保持空。demo 会根据全部有效字段计算 `context_policy_ref`，只要 Evidence budget 改变，身份也必须改变。

退出状态：

| 状态 | 含义 |
| ---: | --- |
| `0` | 真实准备、两路检索和 Context 构建完成，没有部分路线失败或意外候选身份 |
| `1` | 配置/输入错误、真实依赖失败、Retriever 部分失败，或数据库候选包含非当前 fixture 身份 |

Evidence 因预算被正常丢弃仍返回 `0`：这是成功执行的 Context 策略结果，不是程序故障。

## 4. 先预测，再运行真实基线

运行前写下预测：

```text
资料仍是 order_rules.md
问题仍是 surface_match=申请售后
Retriever 配置身份与本节所有 Context 对照保持相同
干净数据库中 RetrievalResult 最终包含两个当前 Chunk
full_context 的 Evidence budget=1000，足以保留两个短 Chunk
两条 included Evidence 都会成为 Citation Candidate
```

运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --query-id surface_match \
  --policy full_context \
  --verbose
```

### 4.1 先核对运行身份

先看：

| 字段 | 要确认什么 |
| --- | --- |
| `dataset` | 是 `rag-retrieval-exploration-1.0.0` |
| `query` | 是 `surface_match=申请售后` |
| `retriever config` | 所有 Context 对照中完全相同 |
| `embedding` | Provider、model、dimensions、preprocessing 和 space 未变化 |
| `current fixture chunks` | 当前真实生成的两个稳定身份 |
| `retrieval` | 没有 `partial_failure` |
| `context policy` | Policy 名称和有效配置身份 |

Embedding distance 可以随真实 Provider 输出产生小幅差异；Context 对照前仍要确认候选身份和融合顺序没有变化。

### 4.2 再确认上游事实

`RetrievalReport · upstream facts` 显示 lexical 与 dense 的：

```text
execution_status
post_threshold_status
visible
candidate
passed
```

本节不会根据 Context budget 重新运行另一套 Retriever 逻辑。后续对照中这些字段、`retriever_config_ref`、最终候选 IDs 和 mapping decisions 都应该相同。

### 4.3 沿同一身份进入 Mapping

`RetrievalResult → ContextSource` 表中检查：

- `Chunk / source` 是否继续使用同一个 `chunk_id`；
- `Mapping` 是否为 `mapped`；
- `Type` 是否为 `evidence`；
- `Reason` 是否为 `mapped_as_current_evidence`；
- locator 是否能回到 `order_rules.md` 的真实标题和行位置。

候选在这里失败时，不能用增加 Evidence budget 修复。

### 4.4 最后读 Context 决定

按以下顺序读取：

```text
Context controls
→ section budget 的 Used / Budget
→ included
→ Dropped sources / Compressed sources
→ citation candidates
→ Context warning
→ BuiltContext model-visible block
```

当前格式化会把 source metadata 一起放进 Context，因此预算消耗不只等于业务正文长度。真实基线中两个 Source 的 Evidence 估算合计应低于 1000；精确数字以当前 tokenizer 与格式化结果为准。

## 5. 单变量对照：只减少 Evidence 分区预算

先重新运行第 4 节基线，再运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --query-id surface_match \
  --policy full_context \
  --evidence-budget 350 \
  --verbose
```

这组只把 Evidence section 从 `1000` 改为 `350`。总预算、Requirement、压缩开关、Retriever、Query、资料和 Embedding 空间都不变。

运行前预测：

- `retriever_config_ref` 不变；
- 两路状态、最终候选 IDs 和 mapping decisions 不变；
- `context_policy_ref` 改变；
- 当前融合第一的订单状态 Chunk 进入 Evidence；
- 接口与客户端 Chunk 因 Evidence 剩余空间不足被标记为 `token_budget_exceeded`；
- 总预算仍有空间，证明真正生效的是 Evidence 分区预算；
- Citation Candidate 从两条变为一条；
- `source_channel` 不再出现在最终 model-visible block。

在当前格式化和 tokenizer 下，两个 Source 约占 `302` 与 `293` tokens，因此 `350` 可以稳定暴露这一边界。若升级 tokenizer、metadata 或格式化实现导致数字改变，应先记录实际值并更新固定对照，不能临时换 Query 或资料来迁就旧预测。

这次运行仍应退出 `0`。Builder 成功执行了策略，只是明确放弃了第二条 Evidence。

## 6. 自然边界：Evidence 分区被关闭

继续保持其他输入不变：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --query-id surface_match \
  --policy full_context \
  --evidence-budget 0 \
  --verbose
```

运行前预测：

```text
RetrievalResult 仍有两个候选
mapping 仍把两条映射为 evidence
两条 dropped reason 都是 section_disabled
included Evidence = 0
Citation Candidate = 0
Requirement “申请售后”仍保留
warning 包含 section_disabled 和 no_evidence_included
```

这是成功执行的自然配置边界，退出状态仍为 `0`。它能证明应用区分“Retriever 没找到”和“Context Policy 不允许 Evidence”，不能证明知识库没有答案，也不能证明后续模型一定会拒答。

## 7. 压缩只用明确假设做确定性验证

当前两个真实 Chunk 很短，不应追加假材料来制造一次看似精彩的真实压缩。运行确定性测试：

```bash
uv run pytest \
  source/packages/llm_core/tests/test_context.py::test_context_builder_compresses_assumed_expanded_order_rules_with_stable_id \
  -q
```

该测试仍使用 `order_rules.md` 的真实售后事实，并明确加入“同主题扩展段落”作为机制假设，使 Source 足够长以稳定触发抽取式压缩。它验证：

- 压缩前后 `source_id` 不变；
- Source 仍然 included；
- 报告出现 compressed 决定；
- Evidence block 标记 `compressed=true`。

它不能证明真实 `order_rules.md` 在本轮发生了压缩，也不能证明压缩后所有关键语义仍然完整。真实业务是否允许压缩，需要生成质量和证据支持性评估。

## 8. 保存结构化记录

基线：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --query-id surface_match \
  --policy full_context \
  --log-format json
```

预算对照：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --query-id surface_match \
  --policy full_context \
  --evidence-budget 350 \
  --log-format json
```

JSON Lines 中：

- `rag_context.started`：数据集、Query、Retriever 与 Embedding 身份、当前 fixture IDs；
- `rag_context.retrieval_observed`：两路状态、最终候选、部分失败和意外身份；
- `rag_context.built`：有效 Policy、mapping、included/dropped/compressed、分区用量、warning、Citation Candidate 和最终 Context block；
- `rag_context.completed`：干净运行完成；
- `rag_context.completed_with_warning`：存在部分路线失败或意外候选，进程返回 `1`。

`--log-format json` 始终输出 JSON Lines；即使同时传入 `--verbose`，也不会切回终端表格。

## 9. 三类边界证据不能混用

### 9.1 自然边界：Evidence budget 为 350 或 0

这些命令仍调用真实 PostgreSQL 和 Embedding。它们能证明当前真实候选怎样受 Context Policy 控制，不能证明某个预算是产品最佳值。

### 9.2 真实依赖失败

| 表现 | 发生层次 | 正确处理 |
| --- | --- | --- |
| 缺少 `DATABASE_URL` | 实验配置 | 返回 `1`，不创建静态候选 |
| PostgreSQL 连接、鉴权或 migration 失败 | 入库 / Retrieval | 保留结构化错误，Context 不伪装成功 |
| Embedding key、404、限流或超时 | Query 准备 | 没有可信 RetrievalResult，不使用假向量 |
| Retriever 单路失败 | 上游检索 | 保留 partial failure，Context 结果不能算干净基线 |
| 出现旧 Chunk 身份 | 数据准备 | 输出 warning 并返回 `1`，不把去重归因于预算 |

真实失败本身就是依赖边界证据。不要为了得到绿色输出而换成 Mock。

### 9.3 确定性契约失败

运行：

```bash
uv run pytest \
  source/packages/rag_core/tests/test_rag_context.py::test_candidate_without_source_span_cannot_enter_traceable_context \
  source/packages/rag_core/tests/test_rag_context.py::test_additional_source_cannot_shadow_retrieved_chunk_id \
  -q
```

它们稳定证明：

- 缺少 locator 的候选不能进入可追踪 Context；
- 额外来源不能覆盖检索 Chunk 身份。

这些测试不证明真实数据库、Embedding 或 Context 质量。

历史资格边界使用：

```bash
uv run pytest \
  source/packages/rag_core/tests/test_rag_context.py::test_historical_context_is_not_a_citation_candidate \
  -q
```

其中历史内容明确标记为“确定性机制假设，不是当前资料事实”，只证明 history 即使 included 也不能成为 Citation Candidate。

## 10. 按“表现 → 层次 → 验证”排查

| 表现 | 可能层次 | 验证方式 |
| --- | --- | --- |
| Query 不是 `surface_match=申请售后` | 实验输入 | 检查 `--query-id surface_match` |
| Embedding space 变化 | Provider / 配置 | 对照 provider、model、dimensions、preprocessing |
| 出现意外候选身份 | 数据准备 / 旧 Chunk | 对照 fixture IDs，查询 `KR-ORDER-STATE` 当前行 |
| Retrieval 最终少于两个当前 Chunk | 固定 Retriever 上游 | 查看两路状态、阈值、RRF 和 final selection |
| 候选有 ID 但 mapping 失败 | Retrieval → Context 契约 | 检查 locator、证据资格和冲突 |
| mapping 成功但 Source dropped | Context Policy | 查看 reason、section Used/Budget 和处理顺序 |
| 总预算有空间但 B 被丢弃 | Evidence section | 对照 Evidence 剩余，而不是只看 total |
| included Source 不是 Citation Candidate | source type / eligibility | 确认是否为当前 Evidence |
| `compressed=true` 但关键句消失 | 压缩边界 | 检查最终 Context block，不只看 source ID |
| Context 只有 Requirement | Evidence section | 检查 `section_disabled` 与 `no_evidence_included` |
| Context 完整但模型仍漏答 | Prompt / 模型 / Eval | 交给后续可信生成与评估，不再盲调预算 |

候选在哪一层第一次消失，就从该层输入和决定开始排查。

## 11. 从 demo 进入公共契约和测试

按下面顺序读代码：

1. [`inspect_rag_context.py`](../../source/demos/rag_retrieval_lab/inspect_rag_context.py)：固定问题、真实 Retriever、Policy 单变量、输出和退出状态。
2. [`rag_core/__init__.py`](../../source/packages/rag_core/__init__.py)：demo 和产品可依赖的公共入口。
3. [`context/adapter.py`](../../source/packages/rag_core/context/adapter.py)：候选身份、locator、证据资格和路线诊断怎样映射。
4. [`llm_core/context/builder.py`](../../source/packages/llm_core/context/builder.py)：过滤后的 Source 怎样进入分区、预算、压缩和报告。
5. [`llm_core/context/ranking.py`](../../source/packages/llm_core/context/ranking.py)：类型、去重、稳定排序和 dropped reason。
6. [`llm_core/context/compression.py`](../../source/packages/llm_core/context/compression.py)：确定性抽取式压缩及其边界。
7. [`test_rag_context.py`](../../source/packages/rag_core/tests/test_rag_context.py)：同一材料下的映射、预算、资格和失败不变量。
8. [`test_context.py`](../../source/packages/llm_core/tests/test_context.py)：通用 Builder 的分区、去重、压缩和 warning。

始终追踪同一个 `surface_match` 和两个 Chunk。不要把这条读码路径扩成对全部 `llm_core` 或 `rag_core` 的逐行导览。

## 12. 修改任务：关闭 Evidence，但不改变上游与 Mapping

打开 [`test_rag_context.py`](../../source/packages/rag_core/tests/test_rag_context.py) 中的 `test_context_report_can_explain_retrieved_but_budget_dropped_source`。测试已经比较：

```text
full_context → 两条 Evidence included
受限预算     → 第一条 included，第二条 token_budget_exceeded
```

在同一个测试中增加第三个 Policy：只把 `section_budgets["evidence"]` 改为 `0`。

写代码前预测：

- `retrieval` 对象没有变化；
- 三次 `mapping` 完全相同；
- 两条 Source 都以 `section_disabled` 被 dropped；
- included 与 Citation Candidate 都为空；
- warning 同时包含 `section_disabled` 和 `no_evidence_included`；
- Requirement 仍是 `申请售后`；
- 关闭 Evidence 不会制造 Retriever failure。

验证：

```bash
uv run pytest \
  source/packages/rag_core/tests/test_rag_context.py::test_context_report_can_explain_retrieved_but_budget_dropped_source \
  -q
```

再运行真实 `--evidence-budget 0` 对照。确定性测试证明 Context 契约；真实运行证明当前 PostgreSQL 与 Embedding 候选确实经过同一控制。二者都不能证明后续模型会正确拒答。

## 13. 完成检查点

完成本实验时，应能做到：

- 始终使用 `order_rules.md` 和 `surface_match=申请售后`；
- 确认只有当前两个 fixture Chunk，没有把旧身份混入 Context 对照；
- 分清 Retrieval Candidate、ContextSource、BuiltContext 和 Citation Candidate；
- 用同一 `source_id` 回查 locator、mapping 和最终去向；
- 证明 `--evidence-budget 350` 只改变 Context Policy，不改变 Retriever；
- 解释总预算有空间时第二条 Evidence 为什么仍会被丢弃；
- 区分正常预算边界、真实依赖失败和确定性契约失败；
- 说明压缩测试中的扩展段落是假设，不是新的业务事实；
- 知道本节不调用 Chat 模型，也不证明 Citation 支持性或证据充分性。

做到这些，Context Engineering 才真正把固定 Retriever 的结果交付成可诊断的模型输入。
