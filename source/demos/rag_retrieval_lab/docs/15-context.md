# 步骤 15：从 RetrievalResult 到 BuiltContext

继续复用真实 Retriever，将最终候选接入 `llm_core.context`：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --without-history
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --policies full_context,evidence_first
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --log-format json
```

默认对同一个 `RetrievalResult` 比较 `evidence_first` 与 `tight_budget`。观察每条 Chunk 的 locator、映射、预算去向和最终 Evidence block；历史材料变化不应改变 RetrievalReport，也不能冒充 Citation Candidate。主路径调用真实 PostgreSQL 与 Embedding，缺少配置时失败。
