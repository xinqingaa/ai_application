# 固定 Retriever 控制与诊断实验

配套机制：[Top-k、阈值、Metadata Filter 与 Retrieval 诊断](../mechanisms/retriever-contract.md)。本实验复用真实 PostgreSQL、Embedding、Lexical、Dense 和 RRF，只改变一个 Retriever 控制参数，观察候选在哪个阶段被保留或淘汰。

阈值和 Top-k 是本轮实验输入，不是项目永久最佳值。

## 1. 前置

完成产品 README 中的 PostgreSQL、pgvector migration 和真实 Embedding 配置。实验会幂等写入固定 Chunk，不会自动执行 migration，也不会回退到内存候选或假向量。

先运行默认基线：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py
```

确认输出的控制顺序是：

```text
pre_filter
→ route_candidate_k
→ route_threshold
→ rrf
→ final_top_k
```

## 2. 展开诊断报告

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --verbose
```

先读本轮身份和控制参数，再按每条路线查看：

- 数据库中有多少索引记录。
- Metadata Filter 后有多少可见记录。
- `candidate_k` 取了多少候选。
- threshold 保留和淘汰多少。
- 路线状态是 success、empty 还是 failed。
- RRF 收到多少路线记录和多少不同 Chunk。
- `final_top_k` 最终保留哪些候选。

## 3. 四次单变量对照

### 只减小 Lexical 候选池

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --lexical-candidate-k 2 \
  --verbose
```

预测：只有 Lexical 进入阈值和融合的候选数量直接受影响；Dense 的原始候选事实不应改变。

### 只收紧 Dense 距离阈值

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --dense-max-distance 0.35 \
  --verbose
```

预测：Dense candidate 仍可能被找到，但更多候选在 route threshold 层被淘汰；不要把它误判为数据库无记录。

### 只减小最终结果数

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --final-top-k 1 \
  --verbose
```

预测：两路候选和 RRF 事实保持不变，只有融合后的最终选择改变。

### 切换到不存在的业务范围

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --knowledge-scope missing_scope
```

这应形成“当前可见范围为空”的真实结果，而不是数据库故障或 Retriever 异常。

## 4. 输出与空结果

| 结果 | 含义 |
| --- | --- |
| visible=0 | 当前 Metadata 范围没有可参与检索的资料 |
| candidates=0 | 路线没有产生候选，可能是词面或距离边界 |
| passed=0 | 候选存在，但全部被当前路线阈值淘汰 |
| fused>0、final=0 | 最终控制或输入契约需要检查 |
| partial_failure=true | 至少一路真实执行失败；不能按普通空结果处理 |

使用 JSON Lines 观察结构化记录：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py \
  --log-format json
```

## 5. 失败时按控制链定位

1. 当前资料属于 `knowledge_scope` 和允许的 source role 吗？
2. 它成为 Lexical 或 Dense candidate 了吗？
3. 它通过对应路线自己的阈值了吗？
4. 两路候选是否使用同一稳定 `chunk_id` 汇合？
5. RRF 后排第几？
6. 是否只被 `final_top_k` 截断？
7. 某一路是否真实失败而不是返回 empty？

数据库、Embedding 或 migration 失败发生在实验准备或路线执行层，不能通过放宽阈值修复。

## 6. 读码顺序

1. `inspect_retrieval_contract.py`：CLI 参数怎样形成 `HybridRetrieverConfig`。
2. `rag_core` 的 Retriever 公共入口：控制顺序和结果契约。
3. Lexical / Dense 适配：每路原生分数与 threshold 怎样保留。
4. RRF：统一候选怎样融合。
5. Retrieval report 模型：route、fusion、no-result 和 partial failure。
6. `source/packages/rag_core/tests/test_hybrid_retriever.py`：确定性控制顺序和诊断不变量。

## 7. 修改与验证

新增或调整一个 Retriever 参数时，先写下它位于哪一层、只应改变哪些计数、哪些路线原始事实不应变化。不要把策略参数散落在 SQL、demo 和产品多个位置。

运行：

```bash
uv run pytest source/packages/rag_core/tests/test_hybrid_retriever.py \
  source/packages/rag_core/tests/test_rrf.py -q
```

再对固定真实问题运行默认基线和单变量对照。测试证明控制契约，不证明当前阈值具有最佳业务质量。
