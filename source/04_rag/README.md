# 04 RAG 学习资源与代码

本目录用于承载 `04_rag` 阶段的代码、学习快照和最终项目。

本阶段代码采用三层结构：

```plain
source/04_rag/
  README.md
  labs/
    phase_1_scaffold/
    phase_2_document_processing/
    phase_3_embeddings/
    phase_4_vector_databases/
    phase_5_retrieval_strategies/
    phase_6_rag_generation/
    phase_7_rag_optimization/
    phase_8_advanced_rag/
    phase_9_project_integration/
  rag_lab/
```

## 当前状态

当前已经完成：

- `labs/phase_1_scaffold/` 骨架快照
- 九个 phase 目录占位
- 最终 `rag_lab/` 占位 README

当前还没有完成：

- Phase 2 及后续真实代码
- 最终完整 `rag_lab`

## 这份 README 和主文档的关系

如果你要理解学习顺序，先看：

- [docs/04_rag/README.md](/Users/lrq/work/ai_application/docs/04_rag/README.md)
- [docs/04_rag/outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md)

如果你要理解项目结构，先看：

- [docs/04_rag/rag_lab_design.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_design.md)
- [docs/04_rag/rag_lab_tasks.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_tasks.md)

一句话说：

- `docs/04_rag/*.md` 负责告诉你怎么学
- `source/04_rag/labs/*` 负责承载每章代码快照
- `source/04_rag/rag_lab` 负责承载最终完整项目

## 九章代码映射

| 章节 | 文档 | 代码入口 | 当前状态 |
|------|------|----------|----------|
| 1 | `01_rag_basics.md` | `labs/phase_1_scaffold/` | 已完成骨架 |
| 2 | `02_document_processing.md` | `labs/phase_2_document_processing/` | 占位 |
| 3 | `03_embeddings.md` | `labs/phase_3_embeddings/` | 占位 |
| 4 | `04_vector_databases.md` | `labs/phase_4_vector_databases/` | 占位 |
| 5 | `05_retrieval_strategies.md` | `labs/phase_5_retrieval_strategies/` | 占位 |
| 6 | `06_rag_generation.md` | `labs/phase_6_rag_generation/` | 占位 |
| 7 | `07_rag_optimization.md` | `labs/phase_7_rag_optimization/` | 占位 |
| 8 | `08_advanced_rag.md` | `labs/phase_8_advanced_rag/` | 占位 |
| 9 | `09_rag_project.md` | `labs/phase_9_project_integration/` | 占位 |

最终完整项目：

- `rag_lab/`

## 当前第一代码入口

当前已经可看的代码入口是：

- `labs/phase_1_scaffold/README.md`
- `labs/phase_1_scaffold/app/config.py`
- `labs/phase_1_scaffold/app/schemas.py`
- `labs/phase_1_scaffold/app/services/rag_service.py`

当前可运行命令：

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/build_index.py
python3 scripts/inspect_chunks.py
python3 scripts/query_demo.py
python3 -m unittest discover -s tests
```

## 后续推进规则

后续每次只推进一个 Phase。

例如开始第二章时，只修改：

- `docs/04_rag/02_document_processing.md`
- `source/04_rag/labs/phase_2_document_processing/`

不要提前把后面章节的向量数据库、RAG Chain、评估系统都塞进 Phase 2。
