# 步骤 13：Lexical + Dense + RRF

完成步骤 12 的真实依赖配置后运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --rrf-k 20
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --dense-mode hnsw
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --log-format json
```

实验保持同一批 Chunk、同一查询和 exact dense，只把 RRF 作为主要变化变量。观察每个候选的 lexical/dense route rank、倒数贡献、原生值和融合排名。任一路真实失败都会保留 `FAILED` 并返回非零状态，不把部分结果伪装成完整融合成功。
