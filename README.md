# AI Application Learning Workspace

这是一个围绕 AI 应用开发转型搭建的学习与项目工作区。

当前主线分为两部分：

- 学习主线：`01_python -> 02_llm -> 03_foundation -> 04_rag -> 05_agent -> 06_application`
- 系统课程参考：`docs/llmops.md`

## 规范入口

仓库内文档与代码规范统一以以下两份文件为准：

- [文档与代码质量规范.md](/Users/linruiqiang/work/ai_application/文档与代码质量规范.md)
- [文档与代码质量规范实施计划.md](/Users/linruiqiang/work/ai_application/文档与代码质量规范实施计划.md)

说明：

- `文档与代码质量规范.md` 是唯一真源，负责定义通用质量标准。
- `文档与代码质量规范实施计划.md` 负责记录规范建设进度、试点计划与后续回修路径。

## 仓库结构

```plain
.
├── CLAUDE.md
├── README.md
├── 文档与代码质量规范.md
├── 文档与代码质量规范实施计划.md
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

## 规范说明

根 `README.md` 只承担仓库导航和规范入口职责，不重复展开完整质量要求。

具体的文档结构、代码质量、映射规则、完成定义和阶段适配要求，请直接查看：

- [文档与代码质量规范.md](/Users/linruiqiang/work/ai_application/文档与代码质量规范.md)
- [文档与代码质量规范实施计划.md](/Users/linruiqiang/work/ai_application/文档与代码质量规范实施计划.md)
