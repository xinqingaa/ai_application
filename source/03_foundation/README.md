# 03 Foundation 学习资源与代码

本目录用于承载 `03_foundation` 阶段的独立基础实验项目与学习资源，例如：

- LangChain 核心抽象实验
- 原生 SDK 与 LangChain 对照代码
- 最小问答服务骨架
- `mock_retriever` 与 `mock_tool`

## 当前状态

当前目录下已经创建 `foundation_lab` 的第一版空骨架，`03_foundation` 现在进入“结构已固定、实现逐步补齐”的阶段。

当前项目目录：

```plain
foundation_lab/
```

## 第一入口

当前如果你要看项目骨架，第一入口建议是：

- `foundation_lab/README.md`
- `foundation_lab/app/services/qa_service.py`

如果你要继续对照设计文档补实现，再回到阶段文档：

- [docs/03_foundation/README.md](../../docs/03_foundation/README.md)

建议优先阅读：

- [docs/03_foundation/04_langchain_core_abstractions.md](../../docs/03_foundation/04_langchain_core_abstractions.md)
- [docs/03_foundation/05_langchain_engineering.md](../../docs/03_foundation/05_langchain_engineering.md)
- [docs/03_foundation/06_foundation_lab_design.md](../../docs/03_foundation/06_foundation_lab_design.md)
- [docs/03_foundation/07_foundation_lab_tasks.md](../../docs/03_foundation/07_foundation_lab_tasks.md)

## 对应关系

| 文档 | 当前角色 | 未来代码关系 |
|------|----------|--------------|
| `docs/03_foundation/README.md` | 阶段导航 | 上位入口 |
| `04_langchain_core_abstractions.md` | 抽象设计 | 对应 `foundation_lab/app/prompts/`、`app/chains/`、`app/llm/` |
| `05_langchain_engineering.md` | 工程骨架设计 | 对应 `foundation_lab/app/` 分层、`main.py`、`logger.py` |
| `06_foundation_lab_design.md` | 项目设计 | 对应 `foundation_lab/` 目录和主数据流 |
| `07_foundation_lab_tasks.md` | 实施顺序 | 对应当前骨架之后的继续实现清单 |
