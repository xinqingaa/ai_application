# 04. 向量数据库

## 1. 本章目标

- 能解释向量数据库在 RAG 中的职责
- 能把 chunk 和 embedding 写入向量存储
- 能做基础相似度查询
- 能理解持久化、删除和 metadata 过滤

## 2. 本章在 04_rag 中的位置

本章负责把向量化结果变成可检索索引，是后续 Retriever 的基础。

## 3. 学习前提

- 已完成文档切分
- 已完成 Embedding Provider 的最小接入

## 4. 本章边界

本章默认先使用轻量向量存储，不展开 Milvus、Pinecone、Weaviate 等生产级系统的完整运维。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“四、向量数据库”
2. 再进入 `phase_4_vector_databases`
3. 先写入少量文档块
4. 再查询并观察返回结果
5. 最后验证删除和 metadata 过滤

## 6. 核心知识点

- Vector Store 的职责
- ANN 和精确搜索的差异
- 持久化目录
- metadata 过滤
- 文档更新和删除一致性
- `as_retriever` 的工程意义

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| 向量存储适配 | `source/04_rag/labs/phase_4_vector_databases/app/vectorstores/` | 主示例 |
| 索引构建 | `source/04_rag/labs/phase_4_vector_databases/app/indexing/` | 工程骨架 |
| 写入脚本 | `source/04_rag/labs/phase_4_vector_databases/scripts/build_index.py` | 第一运行入口 |
| 查询脚本 | `source/04_rag/labs/phase_4_vector_databases/scripts/search_vectors.py` | 验证入口 |

## 8. 实践任务

1. 把第二章的 chunk 写入向量库
2. 查询一个问题并打印 Top-K 文档
3. 使用 metadata 过滤限定来源
4. 删除某个 document_id 并验证召回结果变化

## 9. 完成标准

- 能完成写入、查询和删除
- 能解释向量库和 Embedding Provider 的职责差异
- 能为第五章 Retriever 提供稳定检索基础
