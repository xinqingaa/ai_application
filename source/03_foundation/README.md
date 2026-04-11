# 03 Foundation 学习资源与代码

本目录用于承载 `03_foundation` 阶段的独立基础实验项目与学习资源，例如：

- LangChain 核心抽象实验
- 原生 SDK 与 LangChain 对照代码
- 最小问答服务骨架
- `mock_retriever` 与 `mock_tool`

## 当前状态

当前目录下还没有正式创建 `foundation_lab` 代码，`03_foundation` 目前仍处于“文档先行、代码后落地”阶段。

后续真正开始编码时，建议在该目录下创建：

```plain
foundation_lab/
```

## 第一入口

当前第一入口不是代码，而是阶段文档：

- [docs/03_foundation/README.md](../../docs/03_foundation/README.md)

如果你准备开始落实项目，优先阅读：

- [docs/03_foundation/04_langchain_core_abstractions.md](../../docs/03_foundation/04_langchain_core_abstractions.md)
- [docs/03_foundation/05_langchain_engineering.md](../../docs/03_foundation/05_langchain_engineering.md)
- [docs/03_foundation/06_foundation_lab_design.md](../../docs/03_foundation/06_foundation_lab_design.md)
- [docs/03_foundation/07_foundation_lab_tasks.md](../../docs/03_foundation/07_foundation_lab_tasks.md)

## 对应关系

| 文档 | 当前角色 | 未来代码关系 |
|------|----------|--------------|
| `docs/03_foundation/README.md` | 阶段导航 | 上位入口 |
| `04_langchain_core_abstractions.md` | 抽象设计 | 对应 `app/prompts/`、`app/chains/`、`app/llm/` |
| `05_langchain_engineering.md` | 工程骨架设计 | 对应 `app/` 分层、`main.py`、`logger.py` |
| `06_foundation_lab_design.md` | 项目设计 | 对应 `foundation_lab/` 目录和主数据流 |
| `07_foundation_lab_tasks.md` | 实施顺序 | 对应未来编码阶段的执行清单 |
