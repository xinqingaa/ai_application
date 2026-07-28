# 需求评审助手

`review_assistant/` 是需求评审助手的可运行产品真源，从阶段一 V0 开始逐步演进。

它负责产品代码、API、测试、配置、运行和部署，不承担课程概念教学。

## 产品目标

需求评审助手围绕 PRD、业务规则、接口文档、客户端规则和历史评审记录，逐步完成：

```text
真实文档解析与 PostgreSQL FTS / pgvector 检索
→ 应用侧 RRF 多路召回与 Retrieval 诊断
→ 最小评审工作台
→ 结构化评审与证据引用
→ 可信证据界面
→ 评估、bad case 和质量工作台
→ 经评估达到准入门槛的检索增强
→ 带短期记忆和用户确认偏好/约束长期记忆的单 Agent 补检索、追问和运行界面
→ Workflow 与人工审核
→ 多 Agent 协作
→ 工作台整合、部署与产品化
```

两个阶段怎样进入学习与项目实现，见 [标准学习路径](../course/learning-path.md)。

这里的“检索增强”不预设额外技术栈。V0 固定采用 PostgreSQL 全文检索、pgvector 和应用侧 RRF；Reranker 等候选能力只有在固定评估集上证明收益大于延迟、成本和维护复杂度后，才进入后续产品版本。

## 与课程的边界

```text
course/project/       项目篇教材：组合任务、设计选择、失败题和版本验收
review_assistant/     产品真源：代码、API、测试、配置、运行和部署
```

本 README 只维护产品事实：

- 如何安装和配置。
- 如何启动产品。
- 如何运行测试和评估。
- 产品入口、模块和依赖是什么。
- 当前实现具备哪些实际能力。
- 常见运行失败如何排查。

课程原理、设计题和学习自检不在这里重复维护；学习者从 [课程首页](../course/README.md) 进入。

## 代码关系

- 通用 LLM、RAG、Agent 和 Eval 能力来自 `source/packages/`。
- 产品通过根 `pyproject.toml` 的 editable package 配置 import 复用。
- 不在本目录 copy 平行 `*_core`。
- `source/apps/` 可以用于学习期组合实验，但不与本目录长期维护两份产品。

## 目标职责

产品按真实版本需要逐步形成以下职责：

```text
review_assistant/
├── app/            # FastAPI、业务服务和运行时
├── workbench/      # AI Native Web 工作台
├── tests/          # 产品级测试
├── fixtures/       # 固定业务资料和评估样例
└── infra/          # 数据库、迁移、Docker 与部署
```

这是一张职责地图，不授权预建空目录。只有对应版本的文档、代码和运行入口同时落地时才创建实际目录。

当前产品只维护 Web 工作台，不建设或并行维护 Flutter App。课程中的 Flutter 仍可作为业务影响范围和学习者既有经验出现，但不是 V0–V6 的产品入口或验收项。

## 当前运行说明

当前目录尚未形成独立产品运行入口。已有通用能力和学习期实验分别位于：

- `source/packages/llm_core/`
- `source/packages/rag_core/`（当前已实现文档加载、清洗和来源定位）
- `source/demos/`
- `source/apps/llm_streaming_api/`

V0 受控格式对照 fixtures 已经位于 `fixtures/v0/ingestion/`，供 `rag_ingestion_lab` 观察 TXT、Markdown、DOCX、文本型 PDF 和稳定失败路径。这些是模拟业务内容和真实文件格式，不是生产资料；资料存在也不表示产品入库、检索 API 或工作台已经完成。

产品入口落地后，本节应替换为真实的安装、配置、启动、测试和验证命令，不保留占位命令或模拟成功结果。

## 真实调用规则

- 产品主路径使用真实模型和真实外部服务。
- 缺少 key、供应商失败和模型能力不支持应清晰暴露。
- 不允许静默降级到 Mock。
- Mock 只用于产品单元测试、离线排查或明确标注的稳定失败复现。
