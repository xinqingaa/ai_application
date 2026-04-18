# 04 RAG 代码导航

> 这份 README 只负责一件事：告诉你当前 `04_rag` 的代码应该从哪里开始看、现在做到哪里、下一章该去哪里。

---

## 学习原则

```text
只看当前章节对应的 phase 快照，不提前跳到后面，不先打开最终 rag_lab。
```

- `labs/phase_*` 是按章学习入口
- `rag_lab/` 是最终完整项目占位，不是当前入口

## 目录结构

```text
source/04_rag/
├── README.md
├── labs/
│   ├── phase_1_scaffold/
│   ├── phase_2_document_processing/
│   ├── phase_3_embeddings/
│   ├── phase_4_vector_databases/
│   ├── phase_5_retrieval_strategies/
│   ├── phase_6_rag_generation/
│   ├── phase_7_rag_optimization/
│   ├── phase_8_advanced_rag/
│   └── phase_9_project_integration/
└── rag_lab/
```

## 当前实现状态

| 章节 | 代码入口 | 当前状态 | 第一命令 |
|------|----------|----------|----------|
| 1 | [phase_1_scaffold](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md) | 已实现 | `python3 scripts/query_demo.py` |
| 2 | [phase_2_document_processing](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md) | 已实现 | `python3 scripts/build_index.py` |
| 3 | [phase_3_embeddings](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/README.md) | 已实现 | `python3 scripts/embed_documents.py` |
| 4 | [phase_4_vector_databases](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/README.md) | 占位 | 暂无 |
| 5 | [phase_5_retrieval_strategies](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/README.md) | 占位 | 暂无 |
| 6 | [phase_6_rag_generation](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/README.md) | 占位 | 暂无 |
| 7 | [phase_7_rag_optimization](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_7_rag_optimization/README.md) | 占位 | 暂无 |
| 8 | [phase_8_advanced_rag](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_8_advanced_rag/README.md) | 占位 | 暂无 |
| 9 | [phase_9_project_integration](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_9_project_integration/README.md) | 占位 | 暂无 |

## 当前正确入口

如果你现在开始 `04_rag`，按这个顺序：

1. [docs/04_rag/outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)
2. [docs/04_rag/01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
3. [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)

## 当前可运行命令

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/build_index.py
python3 scripts/inspect_chunks.py
python3 scripts/query_demo.py
python3 -m unittest discover -s tests
```

```bash
cd source/04_rag/labs/phase_2_document_processing
python3 scripts/build_index.py
python3 scripts/inspect_chunks.py
python3 scripts/inspect_chunks.py data/faq.txt
python3 -m unittest discover -s tests
```

```bash
cd source/04_rag/labs/phase_3_embeddings
python3 scripts/build_index.py
python3 scripts/embed_documents.py
python3 scripts/compare_similarity.py
python3 -m unittest discover -s tests
```

## 文档和代码如何分工

- `docs/04_rag/0N_*.md`
  负责讲清本章概念、边界、主线和为什么这样设计。
- `source/04_rag/labs/phase_*/README.md`
  负责告诉你命令怎么跑、代码按什么顺序读、重点看什么。
- `PHASE_CARD.md`
  负责压缩每章增量上下文，方便快速回顾和给 AI 提供稳定上下文。

## 后续推进规则

每推进一章，都必须同步满足：

1. 当前 `phase_*` 有真实代码
2. 当前 `phase_*` 有 `PHASE_CARD.md`
3. 当前章节正文能对着代码读
4. 当前 phase README 能指导运行和阅读

如果某个 phase 只有占位 README，就不要把它当成已完成实现。
