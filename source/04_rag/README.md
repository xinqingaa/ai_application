# 04 RAG 代码导航

> 这份 README 只负责一件事：告诉你当前 `04_rag` 应该从哪里开始学，哪些目录是当前主入口，哪些目录只是迁移期备份。

---

## 当前学习原则

```text
第九章之前，每章优先保持独立闭环；不要把项目工程结构提前压到学习入口上。
```

- 第一章到第六章已经切换到独立目录
- `labs/phase_1_scaffold/` 仅作为迁移期旧版本备份，不再是第一章主入口
- `rag_lab/` 仍然是第九章后的完整项目收口点，不是当前入口

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
├── labs/
│   ├── phase_1_scaffold/          ← 旧版第一章，迁移期保留
│   ├── phase_2_document_processing/  ← 旧版第二章，迁移期保留
│   ├── phase_3_embeddings/        ← 旧版第三章，迁移期保留
│   ├── phase_4_vector_databases/  ← 旧版第四章，迁移期保留
│   ├── phase_5_retrieval_strategies/ ← 旧版第五章，迁移期保留
│   ├── phase_6_rag_generation/    ← 旧版第六章，迁移期保留
│   ├── phase_7_rag_optimization/
│   ├── phase_8_advanced_rag/
│   └── phase_9_project_integration/
└── rag_lab/
```

## 当前实现状态

| 章节 | 代码入口 | 当前状态 | 第一命令 |
|------|----------|----------|----------|
| 1 | [01_rag_basics](./01_rag_basics/README.md) | 新版独立章节 | `python 01_minimum_eval.py` |
| 2 | [02_document_processing](./02_document_processing/README.md) | 新版独立章节 | `python 01_discover_and_load.py` |
| 3 | [03_embeddings](./03_embeddings/README.md) | 新版独立章节 | `python 01_embed_chunks.py` |
| 4 | [04_vector_databases](./04_vector_databases/README.md) | 新版独立章节 | `python 01_index_store.py --reset` |
| 5 | [05_retrieval_strategies](./05_retrieval_strategies/README.md) | 新版独立章节 | `python 01_compare_retrievers.py` |
| 6 | [06_rag_generation](./06_rag_generation/README.md) | 新版独立章节 | `python 01_inspect_prompt.py` |
| 7 | [phase_7_rag_optimization](./labs/phase_7_rag_optimization/README.md) | 占位 | 暂无 |
| 8 | [phase_8_advanced_rag](./labs/phase_8_advanced_rag/README.md) | 占位 | 暂无 |
| 9 | [phase_9_project_integration](./labs/phase_9_project_integration/README.md) | 占位 | 暂无 |

## 当前正确入口

如果你现在开始 `04_rag`，按这个顺序：

1. [docs/04_rag/outline.md](../../docs/04_rag/outline.md)
2. [docs/04_rag/01_rag_basics.md](../../docs/04_rag/01_rag_basics.md)
3. [source/04_rag/01_rag_basics/README.md](./01_rag_basics/README.md)

## 当前可运行命令

```bash
cd source/04_rag/01_rag_basics
python 01_minimum_eval.py
python 02_why_rag.py
python 03_rag_pipeline.py
python 04_solution_decision.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/02_document_processing
python -m pip install -r requirements.txt
python 01_discover_and_load.py
python 02_split_and_inspect.py
python 03_build_chunks.py
python 04_loader_extensions.py
python 05_document_pipeline.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/labs/phase_2_document_processing
python scripts/build_index.py
python scripts/inspect_chunks.py
python scripts/inspect_chunks.py data/faq.txt
python -m unittest discover -s tests
```

```bash
cd source/04_rag/03_embeddings
python -m pip install -r requirements.txt
python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python 04_real_embeddings.py
python 05_semantic_search.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/labs/phase_3_embeddings
python scripts/build_index.py
python scripts/embed_documents.py
python scripts/compare_similarity.py
python -m unittest discover -s tests
```

```bash
cd source/04_rag/04_vector_databases
python -m pip install -r requirements.txt
python 01_index_store.py --reset
python 02_search_store.py
python 03_delete_document.py trial
python 04_chroma_crud.py --reset
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --reset
python 07_vector_store_manager.py --backend chroma "如何申请退费？"
python -m unittest discover -s tests
```

```bash
cd source/04_rag/labs/phase_4_vector_databases
python -m pip install -r requirements.txt
python scripts/index_chroma.py --reset
python scripts/search_chroma.py
python scripts/delete_document.py faq.txt
python scripts/query_demo.py
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

## 文档和代码如何分工

- `docs/04_rag/0N_*.md`
  负责讲清本章概念、边界、输入输出和观察重点。
- `source/04_rag/01_rag_basics/`
  是第一章新的独立学习入口。
- `source/04_rag/02_document_processing/`
  是第二章新的独立学习入口。
- `source/04_rag/03_embeddings/`
  是第三章新的独立学习入口。
- `source/04_rag/04_vector_databases/`
  是第四章新的独立学习入口。
- `source/04_rag/05_retrieval_strategies/`
  是第五章新的独立学习入口。
- `source/04_rag/06_rag_generation/`
  是第六章新的独立学习入口。
- `source/04_rag/labs/phase_*`
  当前仍承载第 7-9 章的旧结构实现，以及前六章的迁移期备份。

## 迁移规则

接下来逐章改造时，按这三个规则执行：

1. 新版章节优先做成独立目录，不复用旧 phase 作为学习入口
2. 旧 phase 只在迁移期临时保留，等前六章替换完后统一删除
3. 第九章才重新收口成完整 RAG 项目
