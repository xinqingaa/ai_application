# AI Application Learning Workspace

这是一个面向前端、Flutter 和跨端开发者的 AI 应用开发学习与项目实践仓库。

本仓库不以转向纯算法、纯 AI Infra 或纯后端平台为目标，而是通过唯一主项目“需求评审助手”，补齐 LLM、RAG、Agent、Workflow、FastAPI、评估观测和 AI Native 产品能力，形成完整 AI 应用闭环。

## 唯一主项目

需求评审助手从可信 RAG + 单 Agent 演进为多 Agent + Workflow 评审系统。

项目分为两个阶段：

1. 可信 RAG + 单 Agent：先完成可用、可信、可评估的需求评审助手。
2. Workflow + 多 Agent：再增加显式流程、人工介入、多角色协作和产品化能力。

V0–V6 是唯一项目里程碑。完整定义见 [docs/strategy.md](docs/strategy.md)。

## 学习方式

学习由项目版本反推，不要求依次学完 LLM、RAG、Agent 等能力域：

```text
当前项目版本提出问题
→ 按需阅读概念篇与机制篇
→ 通过真实实验观察机制
→ 将能力组合进项目
→ 主动制造失败并定位
→ 用评估证明改动
→ 完成版本验收
```

课程正文分为三类：

- 概念篇：解释是什么、为什么需要和边界在哪里。
- 机制篇：解释内部数据流、为什么有效和失败时如何定位。
- 项目篇：定义当前版本的业务目标、设计选择、实现任务和验收。

“真实问题 → 基础原理 → 最小实现 → 主流框架 → 失败边界”是全课程的认知方法，不是每篇文档的固定模板。

详细规则见 [docs/learning-guide.md](docs/learning-guide.md)。

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
course/project/       项目篇教材：为什么做、学什么、怎样判断和验收
review_assistant/     产品真源：安装、运行、测试、API 和部署
```

通用能力沉淀到 `source/packages/`，产品通过 import 复用，不复制平行实现。

## 阅读顺序

1. [docs/strategy.md](docs/strategy.md)：目标、阶段和 V0–V6。
2. [docs/learning-guide.md](docs/learning-guide.md)：学习、文档、代码和运行规则。
3. [docs/ai-coding-mastery.md](docs/ai-coding-mastery.md)：怎样判断真正掌握。
4. `course/` 的当前项目篇及其链接的概念篇、机制篇。
5. 对应 package README 和产品 README。

AI Agent 协作规则见 [AGENTS.md](AGENTS.md) 和 [docs/agent-skill.md](docs/agent-skill.md)。

## 真实调用规则

LLM、RAG、Agent 和 Eval 的学习主路径使用真实模型或真实外部服务：

- 缺少 API key、鉴权失败、限流、超时和模型不支持应清晰暴露。
- 不在真实调用失败后静默返回 fake 或 mock 结果。
- Mock 仅用于单元测试、离线排查、稳定失败复现或明确标注的对照实验。
- Mock 结果不能作为真实模型质量或项目效果的主要证据。

## 依赖管理

全仓库统一使用 uv：

```bash
uv sync
uv run ...
```

依赖只维护在根 `pyproject.toml` 和 `uv.lock`。密钥与外部服务配置使用 `.env` / `.env.example`，不提交真实密钥。
