# 步骤 14：固定 Retriever 控制与诊断

运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --lexical-candidate-k 2 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --dense-max-distance 0.35 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --final-top-k 1 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --knowledge-scope missing_scope
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --log-format json
```

输出按 `pre_filter → route_candidate_k → route_threshold → rrf → final_top_k` 记录数量变化，并区分可见范围为空、两路无匹配、全部低于阈值和真实路由失败。一次只改变一个变量；阈值是实验输入，不是项目永久最佳值。
