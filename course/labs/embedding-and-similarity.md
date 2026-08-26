# 真实 Embedding 相似度实验

配套机制：[Embedding 表示与向量相似度](../mechanisms/embedding-and-similarity.md)。本实验只观察句对表示，不执行整库检索。

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --log-format json
```

运行前预测同义表达、相近主题和无关文本的相似度方向。观察 Provider、模型、维度、metric、分数方向、成本和真实错误。切换 metric 时先确认“越大越近”还是“越小越近”。

读码顺序：`inspect_embedding.py` → `rag_core/embedding` → `llm_core/client`。改变一组句对而不更换模型，运行 embedding 测试并说明该实验不能证明最终召回质量。
