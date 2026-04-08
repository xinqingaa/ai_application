# AI Application Learning Workspace

这是一个围绕 AI 应用开发转型搭建的学习与项目工作区。

当前主线分为两部分：

- 学习主线：`01_python -> 02_llm -> 03_foundation -> 04_rag -> 05_agent -> 06_application`
- 系统课程参考：`docs/llmops.md`

## 仓库结构

```plain
.
├── CLAUDE.md
├── README.md
├── docs/
│   ├── 01_python/
│   ├── 02_llm/
│   ├── 03_foundation/
│   ├── 04_rag/
│   ├── 05_agent/
│   ├── 06_application/
│   └── llmops.md
├── source/
│   ├── 01_python/
│   ├── 02_llm/
│   ├── 03_foundation/
│   ├── 04_rag/
│   ├── 05_agent/
│   └── 06_application/
└── 学习材料改造规范.md
```

## 目录约定

### docs/

存放每个阶段的：

- 学习大纲
- 实施方案
- 学习笔记
- 架构设计
- 项目规划

### source/

存放每个阶段的代码和资源。

其中：

- `03_foundation` 对应独立基础实验项目
- `04_rag` 对应独立 RAG 项目
- `05_agent` 对应独立 Agent 项目
- `06_application` 对应金融 AI 主项目

## 文档质量标准

每一篇正式阶段文档应尽量包含：

- 本节目标
- 学习目标
- 预计学习时间
- 本节在整体学习路径中的重要性
- 本节学习边界
- 与前后章节的衔接关系
- 分层展开的正文，而不是只列结论
- 必要的表格、示例、最小代码或对照说明
- 常见误区或边界提醒
- 本节学完后“能做什么、能判断什么”的明确说明

不接受的文档形态包括：

- 只有结论，没有推导过程
- 只有概念解释，没有工程落点
- 只有大纲扩写，没有章节级教学结构
- 与前后阶段没有边界说明

一句话要求：

- 文档要能用于学习、复习、实施，而不只是留档

