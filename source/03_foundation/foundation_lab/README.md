# foundation_lab

`foundation_lab` 是 `03_foundation` 阶段的独立基础实验项目，用来把文档里已经固定的抽象和工程边界落成最小代码骨架。

当前版本重点是：

- 固定 `config / llm / prompts / chains / retrievers / tools / services / observability` 分层
- 同时保留 native 与 langchain 两套入口
- 提供 `mock_retriever`、`mock_tool`、`qa_service` 的最小占位实现
- 为后续真正接入模型、FastAPI、LangChain 留出稳定扩展点

## 当前状态

当前项目还是骨架版，不追求完整功能，而是先保证：

- 目录结构稳定
- 模块职责清晰
- 文档里的 Phase 1 文件已经落地
- 在没有外部依赖和真实模型配置时，也能通过 mock 路径演示最小流程

## 目录结构

```plain
foundation_lab/
  app/
    config.py
    main.py
    schemas.py
    llm/
    prompts/
    chains/
    retrievers/
    tools/
    services/
    observability/
  scripts/
  tests/
```

## 第一入口

建议先看：

1. `app/services/qa_service.py`
2. `app/chains/qa_chain.py`
3. `app/retrievers/mock_retriever.py`
4. `app/tools/mock_tools.py`

如果你要对照文档继续补实现，回看：

- [docs/03_foundation/04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
- [docs/03_foundation/05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
- [docs/03_foundation/06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
- [docs/03_foundation/07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

## 运行方式

进入项目目录后，可先运行脚本：

```bash
cd source/03_foundation/foundation_lab
python scripts/demo_native.py
python scripts/demo_langchain.py
python scripts/compare_native_vs_lc.py
python -m unittest discover -s tests
```

如果后续安装了 `fastapi` 和 `uvicorn`，可以再尝试：

```bash
uvicorn app.main:app --reload --port 8000
```

## 当前边界

当前故意不做这些事情：

- 真实向量数据库
- 真正的 LangChain 依赖接入
- 真正的 Agent 循环
- 复杂多步工作流
- 生产级配置、日志和部署

这些内容分别留到后续 Phase 和后续阶段继续补齐。
