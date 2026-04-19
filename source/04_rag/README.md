# 04 RAG 代码导航

> 这份 README 只负责一件事：告诉你当前 `04_rag` 应该从哪里开始学，哪些代码已经落地，哪些章节还只有正文文档。

---

## 当前学习原则

```text
先按独立章节理解每一层；第九章才把这些能力收口成完整项目。
```

- 第一章到第六章已经是独立目录
- 第七章到第九章当前只有正文文档，代码尚未创建
- `rag_lab/` 是第九章后的最终项目收口点，不是当前入口

## 目录结构

```text
source/04_rag/
├── README.md
├── 01_rag_basics/
├── 02_document_processing/
├── 03_embeddings/
├── 04_vector_databases/
├── 05_retrieval_strategies/
├── 06_rag_generation/
└── rag_lab/
```

当前仓库里没有 `labs/` 目录。

第七章到第九章的正文仍然在：

- [07_rag_optimization.md](/Users/linruiqiang/work/ai_application/docs/04_rag/07_rag_optimization.md)
- [08_advanced_rag.md](/Users/linruiqiang/work/ai_application/docs/04_rag/08_advanced_rag.md)
- [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md)

## 当前实现状态

| 章节 | 学习入口 | 当前状态 | 第一命令 |
|------|----------|----------|----------|
| 1 | [01_rag_basics](/Users/linruiqiang/work/ai_application/source/04_rag/01_rag_basics/README.md) | 独立章节已完成 | `python 01_why_rag.py` |
| 2 | [02_document_processing](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/README.md) | 独立章节已完成 | `python 01_discover_and_load.py` |
| 3 | [03_embeddings](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/README.md) | 独立章节已完成 | `python 01_embed_chunks.py` |
| 4 | [04_vector_databases](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/README.md) | 独立章节已完成 | `python 01_index_store.py --reset` |
| 5 | [05_retrieval_strategies](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/README.md) | 独立章节已完成 | `python 01_compare_retrievers.py` |
| 6 | [06_rag_generation](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/README.md) | 独立章节已完成 | `python 01_inspect_prompt.py` |
| 7 | [07_rag_optimization.md](/Users/linruiqiang/work/ai_application/docs/04_rag/07_rag_optimization.md) | 正文已完成，代码待创建 | 暂无 |
| 8 | [08_advanced_rag.md](/Users/linruiqiang/work/ai_application/docs/04_rag/08_advanced_rag.md) | 正文已完成，代码待创建 | 暂无 |
| 9 | [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md) | 正文已完成，整合代码待创建 | 暂无 |

## 当前正确入口

如果你现在开始 `04_rag`，按这个顺序：

1. [docs/04_rag/outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)
2. [docs/04_rag/01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
3. [source/04_rag/01_rag_basics/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/01_rag_basics/README.md)

## 当前可运行命令

```bash
cd source/04_rag/01_rag_basics
python 01_why_rag.py
python 02_rag_pipeline.py
python 03_solution_decision.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/02_document_processing
python 01_discover_and_load.py
python 02_split_and_inspect.py
python 03_build_chunks.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/03_embeddings
python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/04_vector_databases
python 01_index_store.py --reset
python 02_search_store.py
python 03_delete_document.py trial
python -m unittest discover -s tests
```

```bash
cd source/04_rag/05_retrieval_strategies
python 01_compare_retrievers.py
python 02_review_bad_cases.py
python 03_query_demo.py --strategy similarity
python -m unittest discover -s tests
```

```bash
cd source/04_rag/06_rag_generation
python 01_inspect_prompt.py
python 02_query_demo.py
python 03_refusal_demo.py
python -m unittest discover -s tests
```

第七章到第九章当前还没有对应代码目录，所以也没有可运行命令。

## 文档和代码如何分工

- `docs/04_rag/0N_*.md`
  负责讲清本章概念、边界、输入输出和观察重点。
- `source/04_rag/01_rag_basics/` 到 `source/04_rag/06_rag_generation/`
  是已经落地的独立章节学习入口。
- `docs/04_rag/07_rag_optimization.md` 到 `docs/04_rag/09_rag_project.md`
  当前先承担后续三章的正文说明，代码后续再补。
- `source/04_rag/rag_lab/`
  是第九章后的最终完整项目占位目录。

## 当前规则

1. 先读正文，再进入对应章节代码目录
2. 后续新章节如果补代码，继续采用独立章节目录，而不是恢复已删除的旧目录结构
3. `rag_lab` 只在第九章后承担最终项目收口
