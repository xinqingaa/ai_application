# Docs

`docs/` 只存放仓库治理类文档，不再存放课程正文。

课程正文统一放在 `course/`，课程配套代码和资源统一放在 `source/`。

## 文档入口

- [writing.md](./writing.md)：文档与代码质量规范，当前唯一真源
- [course-template.md](./course-template.md)：课程、章节、代码 README 写作模板

## 放置规则

应该放在 `docs/`：

- 如何写课程文档
- 如何写章节文档
- 如何写代码 README
- 文档与代码质量规范
- 协作约定、模板和检查清单
- 后续如果整理 skill，也放在这里

不应该放在 `docs/`：

- Python、LLM、RAG、Agent 等课程正文
- 某一章的学习笔记正文
- 某一章的配套代码

对应关系：

```plain
course/   # 课程正文
source/   # 课程配套代码和资源
docs/     # 写作规范、协作规范、模板和检查清单
```
