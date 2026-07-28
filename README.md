# AI Application Learning Workspace

这是一个面向前端、Flutter 和跨端开发者的 AI 应用开发学习与项目实践仓库。

本仓库不以转向纯算法、纯 AI Infra 或纯后端平台为目标，而是通过唯一主项目“需求评审助手”，补齐 LLM、RAG、Agent、Workflow、FastAPI、评估观测和 AI Native 产品能力，形成完整 AI 应用闭环。

## 唯一主项目

需求评审助手从可信 RAG + 单 Agent 演进为多 Agent + Workflow 评审系统。

项目分为两个阶段：

1. 可信 RAG + 单 Agent：先完成可用、可信、可评估的需求评审助手。
2. Workflow + 多 Agent：再增加显式流程、人工介入、多角色协作和产品化能力。

V0–V6 是唯一项目里程碑，学习时由 [标准学习路径](course/learning-path.md) 依次接入。

## 学习方式

课程内容由项目版本反推，学习者则按照标准学习路径正向进入，不从项目规格倒着读，也不按 LLM、RAG、Agent 目录机械通关：

```text
项目愿景建立方向
→ 读取当前版本的业务契约与非目标
→ 按认知前置阅读概念篇与机制篇
→ 通过真实实验观察机制
→ 回到同一项目篇将能力组合进产品
→ 主动制造失败并定位
→ 用评估证明改动
→ 完成版本验收
```

课程正文分为三类：

- 概念篇：解释是什么、为什么需要和边界在哪里。
- 机制篇：解释内部数据流、为什么有效和失败时如何定位。
- 项目篇：定义当前版本的业务目标、设计选择、实现任务和验收。

“真实问题 → 基础原理 → 最小实现 → 主流框架 → 失败边界”是全课程的认知方法，不是每篇文档的固定模板。

开始学习时不需要先读仓库设计规范，直接进入 [课程首页](course/README.md)。

## 目录职责

```text
.
├── docs/                 # 长期战略与规范真源
├── course/               # 概念篇、机制篇、项目篇和集中知识清单
├── source/
│   ├── packages/         # 通用能力唯一实现
│   ├── demos/            # 机制实验、对照和失败复现
│   ├── apps/             # 学习期组合实验
│   └── python_base/      # 已完成的 Python 基础练习
├── review_assistant/     # 从阶段一开始演进的可运行产品真源
├── other/                # RAGFlow、MaxKB 等项目拆解材料
├── archive/              # 历史课程资料，当前主线不依赖
├── pyproject.toml        # Python 依赖和 editable package 真源
└── uv.lock               # 精确依赖锁定
```

项目相关目录不是重复实现：

```text
course/project/       项目篇教材：组合任务、设计选择、失败题和版本验收
review_assistant/     产品真源：安装、运行、测试、API 和部署
```

通用能力沉淀到 `source/packages/`，产品通过 import 复用，不复制平行实现。

## 学习入口

1. [课程首页](course/README.md)：先理解项目目标、文档和代码分别负责什么。
2. [标准学习路径](course/learning-path.md)：按照唯一课表进入概念、机制、实验和项目。
3. 完成核心前置后进入当前项目篇，再阅读对应 package README 和产品 README。

## 维护与 AI 协作

`docs/`、[AGENTS.md](AGENTS.md) 和 `skills/` 面向课程维护者与 AI Agent，规定长期定位、写作规范、代码组织和协作边界，不是学习者的课程前置。

## 真实调用规则

LLM、RAG、Agent 和 Eval 的学习主路径使用真实模型或真实外部服务：

- 缺少 API key、鉴权失败、限流、超时和模型不支持应清晰暴露。
- 不在真实调用失败后静默返回 fake 或 mock 结果。
- Mock 仅用于单元测试、离线排查、稳定失败复现或明确标注的对照实验。
- Mock 结果不能作为真实模型质量或项目效果的主要证据。
