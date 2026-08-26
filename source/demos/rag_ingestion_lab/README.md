# rag_ingestion_lab

这里保存文档解析与 Chunking 的机制探针，不维护课程正文或完整操作手册。

| 程序 | 实验篇 |
| --- | --- |
| `inspect_ingestion.py` | [真实文档解析与错误边界](../../../course/labs/document-loading-and-cleaning.md) |
| `inspect_chunking.py` | [Chunk 策略与 Metadata](../../../course/labs/chunking-and-metadata.md) |

实验 fixture 位于 `source/apps/review_assistant/fixtures/rag/ingestion/`。其中二进制 fixture 由 `build_binary_fixtures.py` 根据受控内容生成；它们用于观察真实文件格式和稳定失败，不代表生产资料分布或产品质量。
