# phase_1_scaffold

`phase_1_scaffold` 是 `04_rag` 第一章的代码快照。

对应文档：

- [docs/04_rag/01_rag_basics.md](/Users/lrq/work/ai_application/docs/04_rag/01_rag_basics.md)

它的作用不是实现完整 RAG，而是先建立后续章节会逐步扩展的项目骨架。

## 当前状态

当前项目是 `Phase 1` 骨架版，不追求完整功能，而是先保证：

- 目录结构稳定
- 模块职责清晰
- 基础数据结构存在
- 占位脚本可以运行
- 最小测试可以通过

当前真实进度应理解为：

- `Phase 1` 已完成骨架
- `Phase 2-9` 还没有完成

## 这份 README 和主文档的关系

如果你要理解“为什么项目要这样设计”，应该先回到主文档：

- [docs/04_rag/README.md](/Users/lrq/work/ai_application/docs/04_rag/README.md)
- [docs/04_rag/rag_lab_design.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_design.md)
- [docs/04_rag/rag_lab_tasks.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_tasks.md)

如果你要知道“当前代码已经做到哪一步”，优先看这份 README。

## 目录结构

```plain
phase_1_scaffold/
  app/
    config.py
    schemas.py
    ingestion/
    indexing/
    embeddings/
    vectorstores/
    retrievers/
    prompts/
    chains/
    services/
    evaluation/
    api/
    observability/
  scripts/
  tests/
  evals/
  data/
```

## 第一入口

建议先看：

1. `app/config.py`
2. `app/schemas.py`
3. `app/services/rag_service.py`
4. `app/chains/rag_chain.py`

## 当前可运行内容

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/inspect_chunks.py
python3 scripts/build_index.py
python3 scripts/query_demo.py
python3 -m unittest discover -s tests
```

这些命令目前的意义是：

- 验证项目骨架已建立
- 验证最小模块可以导入
- 验证下一步任务入口清楚

## 下一步

下一步不是继续在本目录里写完整 RAG。

开始第二章时，应进入：

- [docs/04_rag/02_document_processing.md](/Users/lrq/work/ai_application/docs/04_rag/02_document_processing.md)
- `source/04_rag/labs/phase_2_document_processing/`
