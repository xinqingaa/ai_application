# 固定 Retriever 控制与诊断实验

> 这是 [Top-k、阈值、Metadata Filter 与 Retrieval 诊断](../mechanisms/retriever-contract.md)的实验篇。它继续使用第 11–13 节的同一份售后资料和同一个主题问题，观察两个真实 Chunk 怎样经过 `pre-filter → candidate_k → route threshold → RRF → final_top_k`。

本文只回答：怎样在真实 PostgreSQL、真实 Embedding 和 pgvector 上固定输入，每次只改变一个 Retriever 控制，读出候选在哪一层被保留或淘汰？

本实验能证明当前环境中的真实候选变化，以及确定性测试守住的控制顺序、状态和错误契约。它不能证明示例阈值是产品最佳值，也不能用一次成功输出代替后续 Golden Set、Citation 支持性或生成质量验收。

## 1. 固定材料、问题和观察边界

第 14 节主实验始终固定：

```text
资料：source/apps/review_assistant/fixtures/rag/ingestion/order_rules.md
问题集：source/apps/review_assistant/fixtures/rag/retrieval/retrieval_queries.json
dataset_version：rag-retrieval-exploration-1.0.0
query_id：surface_match
query：申请售后
范围：after_sale + reference_knowledge + current_evidence
```

真实资料在本轮经当前 structure-aware Chunker 生成两个 Chunk：

| Chunk | 内容 |
| --- | --- |
| 当前订单状态规则 | 仅已支付且已完成的订单可申请售后；虚拟商品不进入售后流程 |
| 接口与客户端约束 | 售后接口 v2 必须提供 `source_channel`；Flutter 客户端使用相同入口可见性规则 |

本轮生成两个 Chunk，不代表复用数据库里一定只有两行。旧 Chunking 身份或其他同范围资料可能仍留在索引中；实验入口会显示当前两个 `chunk_id`，并在融合候选出现其他身份时给出 warning。出现 warning 时先解决数据准备差异，不能继续把候选变化归因于 top-k 或阈值。

不要为了让某个参数“看起来有效”而更换 Query 或补充第三份资料。真实 Provider 返回的 dense distance 可以变化；发生变化时记录实际模型和空间身份，不把正文中的手算数值当作真实输出。

## 2. 运行前准备

本实验承接 [pgvector Dense Retrieval 实验](vector-store-and-pgvector.md)和 [RRF 对照实验](multi-retrieval-and-rrf.md)。开始前确认：

- `DATABASE_URL` 指向第 11–13 节使用的同一个 PostgreSQL Database。
- `0001_create_rag_chunks.sql` 和 `0002_add_pgvector_embeddings.sql` 已执行。
- PostgreSQL 已启用 pgvector，两个目标表存在。
- `.env` 中的真实 Embedding key、endpoint 和 model 可以调用 embeddings 端点。
- RRF 真实实验可以正常完成；失败时不会回退到内存检索或假向量。

在仓库根目录检查数据库：

```bash
set -a && source .env && set +a
psql "$DATABASE_URL" -c "SELECT current_database(), current_user;"
psql "$DATABASE_URL" -c "\dt review_assistant.rag_chunks"
psql "$DATABASE_URL" -c "\dt review_assistant.rag_chunk_embeddings"
```

核对同一业务文档当前保留了哪些 Chunk 身份：

```bash
psql "$DATABASE_URL" -P pager=off -c "
SELECT chunk_id, document_id, document_version, left(content, 60) AS content
FROM review_assistant.rag_chunks
WHERE document_id = 'KR-ORDER-STATE'
ORDER BY document_version, chunk_id;
"
```

干净实验库应只保留本轮生成的两个身份。如果同一 `document_id` / `document_version` 出现内容重复但 `chunk_id` 不同的旧行，不要盲目删除产品资料；使用干净课程数据库，或先按文档更新策略明确处理旧 Chunk，再继续本节对照。

再确认入口和参数：

```bash
uv sync
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --help
```

实验会幂等写入固定 Chunk 和当前 Embedding 空间的向量；重复运行不会无限复制相同 Chunk。它不会自动执行 migration，也不会清空产品表。

## 3. 唯一主入口、默认值和退出状态

本节唯一主入口是：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --verbose
```

`--query-id surface_match` 是第 14 节的固定实验条件。CLI 不传 `--query-id` 时会运行共享问题集中的全部 Query，但那不是本节的主对照方式。

默认 Retriever 控制为：

| 参数 | 默认值 | 作用层次 |
| --- | ---: | --- |
| `--lexical-candidate-k` | `5` | lexical 路线候选深度 |
| `--dense-candidate-k` | `5` | dense 路线候选深度 |
| `--lexical-min-rank` | `None` | lexical 原生 rank 阈值；默认不设阈值 |
| `--dense-max-distance` | `None` | dense cosine distance 阈值；默认不设阈值 |
| `--rrf-k` | `60` | RRF 平滑常数，本节不把它作为主要变量 |
| `--final-top-k` | `3` | 融合后最终候选上限 |
| `--knowledge-scope` | `after_sale` | Metadata 业务范围 |
| `--query-id` | 未指定时运行全部 | 第 14 节始终显式指定 `surface_match` |

退出状态：

| 状态 | 含义 |
| ---: | --- |
| `0` | 真实准备和两路检索完成，且没有部分路线失败 |
| `1` | 缺少配置、真实依赖失败、输入契约错误，或至少一路检索失败 |

一路失败但另一路仍有候选时，报告会保留部分结果用于诊断，同时设置 `partial_failure=true` 并返回 `1`；不能把它当成完整成功。

## 4. 先预测，再运行真实基线

运行前先写下预测：

```text
本轮 fixture 仍生成两个售后 Chunk
Query 仍是“申请售后”
在干净实验库中，两路 visible 应为 2
默认两路 threshold 都是 None
final_top_k=3 不会把两个融合候选截成 0 条
```

Lexical 可能因为 OR 词项让两个 Chunk 都成为候选；dense 的顺序和 distance 由当前真实 Embedding 空间决定。不要在运行前写死 dense 数值。

运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --verbose
```

### 4.1 先核对运行身份

输出开头必须能看到：

| 字段 | 为什么先看它 |
| --- | --- |
| `dataset` | 确认仍是共享探索数据 `rag-retrieval-exploration-1.0.0` |
| `query` | 确认是 `surface_match=申请售后` |
| `embedding space` | 确认 Chunk 与 Query 使用同一空间 |
| `provider / model / dimensions / preprocessing` | 真实 Provider 或空间变化不能归因于 Retriever 参数 |
| `current fixture chunks` | 本轮 fixture 实际生成的两个稳定身份 |
| `retriever config` | 标识本轮 candidate、阈值、RRF、final 和 Metadata 控制 |
| `embedding latency` | 区分准备耗时与 Retriever 查询耗时 |

只有这些身份一致，且没有“意外候选身份” warning，后续单变量对照才可比较。`indexed` 或 `visible` 大于 2 时，先判断是否存在旧 Chunk 或其他同范围资料。

### 4.2 按控制顺序读汇总表

汇总行依次显示：

```text
Lexical execution/post_threshold
Dense execution/post_threshold
Fused
Final
Partial
No-result reason
Retriever latency
```

`success/success` 表示路线执行成功，阈值后仍有候选。`success/empty` 表示路线执行成功且曾形成候选，但当前阈值把候选全部淘汰。`failed/failed` 才表示路线没有正常完成。

不要把这些数量混成一个“结果数”：

```text
indexed → visible → matched（lexical only）→ candidate → passed
```

Dense 没有与 FTS `@@` 相同语义的 matched 集合，因此它显示 `matched=None` 是契约差异，不是漏记日志。

### 4.3 展开每条候选的去向

`--verbose` 会显示两张关键表：

- `Route threshold decisions`：路线、`chunk_id`、原生数值、方向和阈值决定。
- `RRF and final_top_k decisions`：融合排名、RRF 分数和最终选择原因。

默认阈值为 `None` 时，每条已有路线候选应显示 `no_route_threshold`。融合后没有选中的候选会显示 `dropped_by_final_top_k`；它已经通过前面所有阶段，不能回头解释成数据库没搜到。

### 4.4 保存结构化记录

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --log-format json
```

JSON Lines 中：

- `retrieval_contract.started` 保存数据集、Retriever 配置和 Embedding 空间身份。
- `retrieval_contract.query_observed` 保存两路执行/阈值后状态、各层数量、阈值决定、最终决定、部分失败和耗时。
- `retrieval_contract.completed` 表示本轮观察入口完成。

## 5. 四组单变量对照

每组都先运行第 4 节基线，再只运行本组命令。资料、Query、Provider、Embedding 空间和其他参数必须保持不变。

### 5.1 只减小 lexical 候选池

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --lexical-candidate-k 1 \
  --verbose
```

运行前预测：

- lexical `candidate_count` 最多为 1。
- dense 的 indexed、visible、candidate、原生 distance 和路线状态不应因为 lexical 参数改变。
- 排名第二的 lexical 候选若消失，是没有进入该路 candidate pool，不是被阈值删除。
- RRF 的路线贡献、重合数量和最终排名可能随输入变化。

这里必须使用 `1`，不能使用 `2`：真实 fixture 只有两个 Chunk，默认 `5 → 2` 通常不会产生可观察差异。

### 5.2 只增加 dense 距离阈值

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --dense-max-distance 0 \
  --verbose
```

本组只把 dense threshold 从 `None` 改为 `0`。运行前预测：

- dense 查询仍会先形成原始 candidate，`candidate_count` 不应因为阈值改变。
- `threshold_name` 从 `None` 变为 `dense_max_cosine_distance`。
- 非完全相同文本通常具有大于 0 的 cosine distance，因此真实候选通常会在阈值层被删除。
- 实际删除数量必须以当前 Provider 输出为准；课程不把某个真实 distance 写成永久常量。
- lexical 原始候选事实不应改变。

若需要稳定证明 `all_below_threshold` 分类，使用第 6 节确定性测试；不要把真实 Provider 输出改写成固定成功故事。

### 5.3 只减小最终结果数

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --final-top-k 1 \
  --verbose
```

运行前预测：

- lexical 与 dense 的 route report 不变。
- threshold decisions 不变。
- RRF 候选、分数和 fusion rank 不变。
- 只有最终选中数量和 `FinalSelectionDecision` 改变。
- `retriever_config_ref` 必须改变。

由于 `final_top_k` 必须大于 0，只要 `fused > 0`，`final` 就不可能是 0。若出现这种组合，应按契约缺陷处理，不是自然空结果。

### 5.4 只切换 Metadata 业务范围

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --query-id surface_match \
  --knowledge-scope missing_scope \
  --verbose
```

运行前预测：

```text
indexed > 0
visible = 0
candidate = 0
final = 0
no_result_reason = visible_scope_empty
```

这是同一份资料和同一个 Query 下的自然配置边界。系统忠实执行了调用者给出的范围，只是该范围没有资料；不要删除 Metadata Filter 来制造“有结果”。

## 6. 三类失败证据不能混用

### 6.1 自然边界：真实 `missing_scope`

第 5.4 节使用真实 PostgreSQL 和真实索引，只改变业务范围。它能证明应用可以区分“索引存在但当前范围不可见”，不能证明知识库在所有范围都没有答案。

### 6.2 真实依赖失败

| 表现 | 发生层次 | 应怎样记录 |
| --- | --- | --- |
| 缺少 `DATABASE_URL` | 实验配置 | 非零退出；不创建内存候选 |
| PostgreSQL 连接、鉴权或 migration 失败 | 入库或路线执行 | 保留结构化错误；不解释成 empty |
| Embedding key、404、限流或超时 | Query Embedding 准备 | Retriever 尚未开始，没有 `RetrievalReport` |
| 单路 PostgreSQL 查询失败 | Retriever route | `FAILED` route、错误码、`partial_failure` 和非零退出 |

不要为了得到绿色输出而替换成 Mock 或假向量。真实失败本身就是外部边界证据。

### 6.3 确定性契约失败

运行：

```bash
uv run pytest \
  source/packages/rag_core/tests/test_hybrid_retriever.py::test_all_candidates_below_route_threshold_has_structured_reason \
  source/packages/rag_core/tests/test_hybrid_retriever.py::test_failed_route_remains_visible_instead_of_becoming_empty \
  -q
```

这些测试继续使用“申请售后”和 `order_rules.md` 中的业务规则，但用受控路线结果稳定复现：

- 两路候选全部低于各自阈值。
- 一条路线返回结构化连接失败。

受控 Retriever 能证明 `all_below_threshold`、`route_failure`、状态和错误契约，不证明真实 PostgreSQL、真实 Embedding 或检索质量。

## 7. 按“表现 → 层次 → 验证”排查

| 表现 | 可能层次 | 验证方式 |
| --- | --- | --- |
| `query` 字段不是 `surface_match=申请售后` | 实验输入 | 检查 `--query-id surface_match` |
| Embedding space 前后不同 | 真实 Provider / 配置 | 对照 provider、model、dimensions、preprocessing 和 space ref |
| `indexed=0` | 词法配置或向量空间 | 检查 Chunk 入库、Embedding 空间和 migration |
| 出现意外候选身份 warning | 数据准备 / 旧 Chunk | 对照当前 fixture IDs，查询 `document_id` / `document_version`，使用干净课程数据库或先完成明确更新 |
| `indexed>0, visible=0` | Metadata / 空间过滤 | 核对 scope、source role、evidence eligibility 和空间身份 |
| lexical `matched=0` | 词法表示 | 查看 Query terms、资料词面和 PostgreSQL FTS |
| `candidate>0, passed=0` | route threshold | 查看原生值、方向、阈值名称和值 |
| `execution=success, post_threshold=empty` | 阈值后状态 | 不查数据库连接；先查 threshold decisions |
| 候选进入 RRF 但不在最终结果 | `final_top_k` | 查看 fusion rank 与 final selection reason |
| `partial_failure=true` | 单路真实失败 | 查看失败 route 的 code/message；不要只读剩余候选 |
| Embedding 失败且没有报告 | 实验准备 | 检查真实 key、endpoint、model、限流和超时 |
| `fused>0, final=0` | 实现违反契约 | 检查 `final_top_k > 0` 和最终截断实现 |

候选在哪一层第一次消失，就从该层输入开始排查；不要从最熟悉的参数开始盲调。

## 8. 从 demo 进入公共契约和测试

按下面顺序读代码：

1. [`inspect_retrieval_contract.py`](../../source/demos/rag_retrieval_lab/inspect_retrieval_contract.py)：固定 Query、真实入库、Embedding、CLI 参数、输出和退出状态。
2. [`rag_core/__init__.py`](../../source/packages/rag_core/__init__.py)：产品与 demo 可依赖的公共导出，不从内部文件绕过契约。
3. [`retrieval/hybrid.py`](../../source/packages/rag_core/retrieval/hybrid.py)：`HybridRetrieverConfig`、`FixedHybridRetriever.retrieve`、阈值、RRF、最终截断和报告组装。
4. [`retrieval/postgres_fts.py`](../../source/packages/rag_core/retrieval/postgres_fts.py)：lexical 在 SQL 排序和 `LIMIT` 前应用可见范围。
5. [`retrieval/postgres_dense.py`](../../source/packages/rag_core/retrieval/postgres_dense.py)：dense 空间、Metadata、distance 和候选查询。
6. [`retrieval/fusion.py`](../../source/packages/rag_core/retrieval/fusion.py)：第 13 节已经学过的统一候选和 RRF，不负责 route threshold 或 `final_top_k`。
7. [`test_hybrid_retriever.py`](../../source/packages/rag_core/tests/test_hybrid_retriever.py)：同一业务材料下的确定性顺序、空结果、部分失败和配置身份。

读码时始终追踪同一个 `surface_match`：demo 怎样选择它、怎样生成 Query Embedding、怎样进入两路、怎样形成报告。不要把这一节变成对全部 `rag_core` 的逐行导览。

## 9. 修改任务：扩大 final 上限但不改变上游事实

打开 [`test_hybrid_retriever.py`](../../source/packages/rag_core/tests/test_hybrid_retriever.py) 中的 `test_final_top_k_only_changes_the_final_selection`。它已经比较 `final_top_k=1` 与 `2`。

增加第三组：

```text
资料：仍是 order_rules.md 的两个 Chunk
Query：仍是“申请售后”
final_top_k：3
```

写代码前先预测：

- `route_reports`、`threshold_decisions` 和 `fusion_diagnostics` 与 `final_top_k=2` 完全相同。
- 只有两个 fused candidates，因此 `final_top_k=3` 仍只返回两个，不会制造第三条候选。
- 所有已有候选都应为 `selected_by_final_top_k`。
- `retriever_config_ref` 必须与 `final_top_k=2` 不同，即使最终候选内容相同。
- `no_result_reason` 仍为 `None`。

验证：

```bash
uv run pytest \
  source/packages/rag_core/tests/test_hybrid_retriever.py::test_final_top_k_only_changes_the_final_selection \
  -q
```

再运行真实基线和 `--final-top-k 1` 对照。确定性测试证明配置身份和截断契约；真实运行观察当前 Provider 下的真实候选。二者都不能证明 `1`、`2` 或 `3` 哪个具有最佳业务质量。

## 10. 完成检查点

完成本实验时，应能做到：

- 始终使用 `order_rules.md` 和 `surface_match=申请售后` 完成主对照。
- 确认当前 fixture 的两个身份与候选一致，没有把旧 Chunk 混入参数对照。
- 先核对数据集、Query、Embedding 空间和 Retriever 配置，再比较候选。
- 区分 indexed、visible、matched、candidate、passed、fused 和 final。
- 解释 `execution_status` 与 `post_threshold_status` 为什么不能合并。
- 完成四组单变量对照，并指出哪些事实应变、哪些不应变。
- 区分自然 `missing_scope`、真实依赖失败和确定性契约失败。
- 从 demo 找到公共入口、核心控制步骤和测试。
- 完成 final 上限修改题，并说明测试不能证明真实检索质量。

完成后回到[机制正文](../mechanisms/retriever-contract.md)，用真实输出核对两个 Chunk 在五层控制中的实际去向，再由[标准学习路径](../learning-path.md)进入 Context Engineering。
