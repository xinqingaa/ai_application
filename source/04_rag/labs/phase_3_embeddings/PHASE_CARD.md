# PHASE_CARD

## Phase

- 名称：`phase_3_embeddings`
- 对应章节：[03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md)

## 本章目标

- 把 `SourceChunk[]` 变成 `EmbeddedChunk[]`
- 建立 provider 抽象
- 区分 query/document 两条向量化入口

## 上一章输入契约

- 稳定 `SourceChunk[]`
- 稳定 `chunk_id / document_id / metadata`

## 输出契约

- `EmbeddedChunk[]`
- `EmbeddingProvider`
- `embed_documents()`
- `embed_query()`
- 最小相似度计算能力

## 本章新增

- `app/embeddings/providers.py`
- `app/embeddings/vectorizer.py`
- `app/embeddings/similarity.py`
- `EmbeddedChunk`
- `embed_documents.py`
- `compare_similarity.py`

## 本章可忽略

- 真实向量数据库
- 检索策略优化
- 完整 RAG 生成

## 第一命令

```bash
python3 scripts/embed_documents.py
```

## 建议阅读顺序

1. `app/config.py`
2. `app/embeddings/providers.py`
3. `app/schemas.py`
4. `app/embeddings/vectorizer.py`
5. `app/embeddings/similarity.py`

## 完成标准

- 能解释为什么第三章只是当前章节增量
- 能说明 `EmbeddedChunk` 为什么保留 `SourceChunk`
- 能区分 query/document 两条入口

## 下一章

- 把 `EmbeddedChunk[]` 写入向量存储
- 支持 Top-K 查询、过滤和删除
