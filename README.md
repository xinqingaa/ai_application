# AI Application Learning Workspace

这是一个围绕 AI 应用开发转型搭建的学习与项目工作区。

当前主线：

- 课程主线：`01_python -> 02_llm -> 03_foundation -> 04_rag -> 05_agent -> 06_application`
- 系统课程参考：[course/llmops.md](course/llmops.md)
- 当前综合应用方向：[course/06_application/outline_v2.md](course/06_application/outline_v2.md)

## 目录结构

```plain
.
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── docs/
│   ├── README.md
│   ├── writing.md
│   └── course-template.md
├── course/
│   ├── 01_python/
│   ├── 02_llm/
│   ├── 03_foundation/
│   ├── 04_rag/
│   ├── 05_agent/
│   ├── 06_application/
│   ├── ai_trategy.md
│   └── llmops.md
└── source/
    ├── 01_python/
    ├── 02_llm/
    ├── 03_foundation/
    ├── 04_rag/
    ├── 05_agent/
    └── 06_application/
```

## 目录职责

### docs/

仓库治理文档，只放“怎么写、怎么协作、怎么检查质量”。

- [docs/README.md](docs/README.md)
- [docs/writing.md](docs/writing.md)
- [docs/course-template.md](docs/course-template.md)

### course/

课程正文与学习路线。

- 阶段大纲
- 章节文档
- 项目规划
- 学习方法论

### source/

课程配套代码与资源。

- 示例代码
- 练习代码
- 测试
- 数据集与评估集
- prompt 和项目资源

## 规范入口

仓库内文档与代码质量规范统一以 [docs/writing.md](docs/writing.md) 为准。

后续新增课程章节或代码 README 时，优先参考 [docs/course-template.md](docs/course-template.md)。
