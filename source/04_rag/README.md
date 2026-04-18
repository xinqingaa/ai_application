# 04 RAG 代码入口

> 这份 README 只回答一个问题：当前 `04_rag` 的代码到底应该从哪里开始看。

---

## 先记住代码学习原则

```text
只看当前章节对应的 phase 代码，不提前跳到后面，不先打开最终 rag_lab。
```

`source/04_rag/` 的职责不是一次性放出完整项目，而是承载九个章节的代码快照。

也就是说：

- `labs/phase_*` 才是按章学习的主入口
- `rag_lab/` 是最终整合目录，不是现在的第一入口

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

## 当前真实状态

当前真正有代码内容的有：

- [labs/phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- `labs/phase_1_scaffold/app/*`
- `labs/phase_1_scaffold/scripts/*`
- `labs/phase_1_scaffold/tests/*`
- [labs/phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
- `labs/phase_2_document_processing/app/*`
- `labs/phase_2_document_processing/data/*`
- `labs/phase_2_document_processing/scripts/*`
- `labs/phase_2_document_processing/tests/*`

当前还只是占位的目录：

- `phase_3_embeddings/`
- `phase_4_vector_databases/`
- `phase_5_retrieval_strategies/`
- `phase_6_rag_generation/`
- `phase_7_rag_optimization/`
- `phase_8_advanced_rag/`
- `phase_9_project_integration/`
- `rag_lab/`

所以如果你现在打开 `source/04_rag/`，正确动作不是到处翻目录，而是：

- 先进入 [labs/phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- 学完第一章后，再进入 [labs/phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)

## 代码和章节的对应关系

| 章节 | 文档入口 | 代码入口 | 当前状态 |
|------|----------|----------|----------|
| 1 | [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) | `labs/phase_1_scaffold/` | 可读 |
| 2 | [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md) | `labs/phase_2_document_processing/` | 可读 |
| 3 | [03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md) | `labs/phase_3_embeddings/` | 占位 |
| 4 | [04_vector_databases.md](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md) | `labs/phase_4_vector_databases/` | 占位 |
| 5 | [05_retrieval_strategies.md](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md) | `labs/phase_5_retrieval_strategies/` | 占位 |
| 6 | [06_rag_generation.md](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md) | `labs/phase_6_rag_generation/` | 占位 |
| 7 | [07_rag_optimization.md](/Users/linruiqiang/work/ai_application/docs/04_rag/07_rag_optimization.md) | `labs/phase_7_rag_optimization/` | 占位 |
| 8 | [08_advanced_rag.md](/Users/linruiqiang/work/ai_application/docs/04_rag/08_advanced_rag.md) | `labs/phase_8_advanced_rag/` | 占位 |
| 9 | [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md) | `labs/phase_9_project_integration/` | 占位 |

## 当前第一代码入口

建议按这个顺序进入 `Phase 1`：

1. [labs/phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
2. `app/config.py`
3. `app/schemas.py`
4. `app/indexing/index_manager.py`
5. `app/chains/rag_chain.py`
6. `app/services/rag_service.py`
7. `scripts/inspect_chunks.py`
8. `scripts/query_demo.py`

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

当前最值得优先跑的是：

- `Phase 1 / build_index.py`
  验证骨架目录和配置入口已经存在。
- `Phase 1 / query_demo.py`
  提前看到“retriever -> prompt -> answer result”的占位链路。
- `Phase 2 / build_index.py`
  看到真实文档发现和 chunk 数量统计。
- `Phase 2 / inspect_chunks.py`
  看到 chunk 的字符范围、来源和预览内容。
- `unittest`
  验证当前阶段的最小稳定性检查存在。

## 这份代码 README 和课程文档的关系

如果你想知道：

- 为什么这一章先做骨架
- 为什么现在不直接写完整 RAG
- 这一章应该先理解哪些概念

先回到：

- [docs/04_rag/README.md](/Users/linruiqiang/work/ai_application/docs/04_rag/README.md)
- [docs/04_rag/outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)
- [docs/04_rag/01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)

如果你要知道：

- 现在具体该打开哪些文件
- 命令怎么跑
- 代码应该怎么读

就留在当前 `phase` 目录的 README。

## 后续推进规则

后续每推进一章，都必须同步满足这四点：

1. 当前 `phase_*` 有真实代码快照。
2. 当前章节文档能对着这份代码读。
3. 当前 `phase_*` README 能指导运行和阅读。
4. 本 README 的状态表被更新。

如果某个 Phase 只有 README 占位，就不应该被当成已完成实现。
