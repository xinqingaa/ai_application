# 步骤 16：结构化生成与 Citation Candidate

运行真实检索、Context 和 chat 模型：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py --variants rag_evidence
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py --structured-mode json_object
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py --log-format json
```

需要真实 `DATABASE_URL`、Embedding 配置和 `OPENAI_API_KEY`。输出应展示风险、claimed source ID 和候选集合检查结果；结构化解析失败或未知 source ID 返回非零状态，不静默降级。

本步骤只检查 Citation Candidate membership，不证明引用内容支持结论，也不实现证据充分性、Refusal 或追问闭环。对照材料位于 [`fixtures/v0/generation`](../../../../review_assistant/fixtures/v0/generation/)。
