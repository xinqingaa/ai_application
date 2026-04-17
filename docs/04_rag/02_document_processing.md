# 02. 文档处理

## 1. 本章目标

- 能加载至少一种本地文档格式
- 能把原始文本切分成可检索的 chunk
- 能为每个 chunk 注入稳定 metadata
- 能生成稳定的 `document_id / chunk_id`

## 2. 本章在 04_rag 中的位置

文档处理是 RAG 的知识入口。

如果文档加载、切分和 metadata 设计不稳定，后面的 Embedding、向量数据库和检索优化都会失去基础。

## 3. 学习前提

- 已完成 [01_rag_basics.md](/Users/lrq/work/ai_application/docs/04_rag/01_rag_basics.md)
- 已理解 LangChain `Document` 的基本含义

## 4. 本章边界

本章不追求支持所有文档格式，也不展开 OCR、复杂表格解析和企业级知识库后台。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“二、文档处理”
2. 再进入 `phase_2_document_processing`
3. 先实现 TXT / Markdown，再考虑 PDF
4. 最后记录不同切分参数的观察结果

## 6. 核心知识点

- Loader 的职责
- 文本清洗的边界
- `chunk_size / chunk_overlap`
- metadata 字段设计
- `document_id / chunk_id`
- 增量更新和删除一致性的前置意识

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| 文档加载 | `source/04_rag/labs/phase_2_document_processing/app/ingestion/` | 主示例 |
| 文本切分 | `source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py` | 主示例 |
| metadata 注入 | `source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py` | 主示例 |
| ID 生成 | `source/04_rag/labs/phase_2_document_processing/app/indexing/` | 工程骨架 |
| 切分调试 | `source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py` | 第一运行入口 |

## 8. 实践任务

1. 准备一份 Markdown 或 TXT 示例文档
2. 加载文档并打印原始文本长度
3. 用不同 `chunk_size` 切分同一文档
4. 打印每个 chunk 的 metadata
5. 验证重复运行时 `document_id / chunk_id` 是否稳定

## 9. 完成标准

- 能稳定加载至少一种文档格式
- 能解释不同切分参数对检索的影响
- 能说明 metadata 为什么影响来源引用和权限过滤
- 能为后续向量化阶段提供稳定 chunk 列表
