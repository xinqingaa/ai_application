# Chunk 策略与 Metadata 对照实验

配套机制：[Chunking、父子块与 Metadata](../mechanisms/chunking-and-metadata.md)。本实验固定文档，只改变 Chunk 策略或预算。

```bash
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py --policy fixed --max-tokens 32 --overlap-tokens 6
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py --policy parent-child --verbose
```

运行前预测边界、重叠、父子关系和 locator 怎样变化。观察 Chunk 数量、Token、稳定 ID、标题路径、父子身份和来源定位；不要用“切得更多”代替检索质量结论。

读码顺序：`inspect_chunking.py` → `rag_core/chunking`。修改一个预算参数，运行 chunking 测试并解释哪些 Chunk 身份需要变化。
