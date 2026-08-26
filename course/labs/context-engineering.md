# 从 RetrievalResult 到 BuiltContext

配套机制：[Context Engineering](../mechanisms/context-engineering.md)。本实验调用真实 Retriever，再把同一个 `RetrievalResult` 适配为 Context Source，使用不同预算策略装配模型本轮可见材料。

本实验观察候选到 Context 的变化，不调用生成模型，也不证明某种 Context 策略会让最终回答更好。

## 1. 前置

完成 PostgreSQL、pgvector 和真实 Embedding 配置，并先跑通[固定 Retriever 实验](retriever-contract.md)。实验继续复用同一份需求、Chunk、知识范围和来源身份。

默认运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py
```

默认对同一个 `RetrievalResult` 比较 `evidence_first` 与 `tight_budget`。运行前预测：

- Retriever 的候选、排名和诊断是否保持相同。
- 两种策略各自优先保留什么。
- 哪些历史材料不是 Citation Candidate。
- Budget 收紧后哪些来源可能被丢弃。

## 2. 展开映射与预算

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --verbose
```

先读 RetrievalReport，再读每个 ContextBuildReport：

| 字段 | 要回答的问题 |
| --- | --- |
| retrieved candidates | Retriever 最终交付了哪些 Chunk |
| mapping decisions | 每个 Chunk 怎样变成 Context Source，locator 是否保留 |
| included / dropped | Builder 最终保留和丢弃了哪些来源 |
| citation candidates | 哪些来源允许被模型声明 |
| estimated / limit | 估算预算怎样消耗 |
| context block | 模型实际能够看到什么 |

候选存在但没有进入 Context 时，先查看 mapping 和 dropped reason，不回到数据库盲目调 Retriever。

## 3. 单变量对照

### 固定候选，只比较策略

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --policies full_context,evidence_first
```

### 只移除历史辅助材料

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --without-history
```

预测：`--without-history` 不应改变 RetrievalReport，因为历史材料在 Retriever 之后作为额外 Context Source 加入；它只应改变 Context 构建结果。

### 改变候选池

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --candidate-k 3 \
  --final-top-k 3
```

这次改变了上游 Retriever 输入。不要把它与“同一候选下比较 Context 策略”记录为同一单变量实验。

## 4. 来源与 Citation Candidate

检查每个检索 Chunk 的：

- `chunk_id` 是否继续成为稳定 source identity。
- 文档版本和 locator 是否保留。
- Lexical / Dense 路线诊断是否保存在 Metadata 或映射报告，而不是丢失。
- 历史材料是否保持 `history_review` 等角色。
- 只有具备证据资格的来源是否进入 Citation Candidate。

Context Source 被 included 不一定意味着它有业务证据资格；历史背景和当前证据必须继续分开。

## 5. JSON Lines 与失败

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --log-format json
```

| 表现 | 可能层次 | 验证方式 |
| --- | --- | --- |
| 缺少 `DATABASE_URL` | 实验准备 | 按产品 README 配置，不回退内存数据 |
| Embedding 或数据库失败 | 上游 Retriever | 保留真实错误，Context Builder 尚未开始 |
| source 没有 locator | Retrieval → Context 映射 | 检查候选来源契约，不伪造定位 |
| 候选被 dropped | Context 策略或预算 | 查看 dropped reason 和分区预算 |
| 历史材料成为 Citation Candidate | source role / eligibility 映射 | 检查额外来源构造和策略 |
| estimated tokens 超出直觉 | 估算器和保留规则 | 本节预算不是最终 Provider 的精确硬上限 |

## 6. 读码顺序

1. `inspect_rag_context.py`：真实 Retriever、额外 history 和策略怎样组合。
2. `rag_core` 的 Retrieval → Context 适配入口：候选身份与来源定位怎样映射。
3. `source/packages/llm_core/context/`：分区、去重、预算和报告。
4. Context policy 配置：不同策略的优先级和限制。
5. `source/packages/rag_core/tests/test_rag_context.py` 与 `llm_core/tests/test_context.py`：映射和构建不变量。

## 7. 修改与验证

选择一个 Context policy 预算参数或优先级，只改变这一项。先预测：

- 哪些 source 可能 included / dropped。
- RetrievalReport 为什么不应变化。
- Citation Candidate 资格为什么不能被预算策略篡改。
- 最终 Prompt 还有哪些额外 Token 开销。

运行：

```bash
uv run pytest source/packages/rag_core/tests/test_rag_context.py \
  source/packages/llm_core/tests/test_context.py -q
```

再用同一真实 Retriever 运行两种策略。Context 质量最终要在生成和固定数据集上验证，本实验只守住装配与来源边界。
