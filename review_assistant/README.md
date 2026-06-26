# 需求评审助手（review_assistant）

`07_projects` 起的**可部署产品真源**。学习阶段在 `source/packages/` 积累能力；本目录 import 共享包并组装 API、工作台与 infra。

## 结构（逐步填充）

```text
review_assistant/
├── app/            # FastAPI 等服务入口
├── workbench/      # Vue / Flutter 工作台
└── infra/          # docker-compose、迁移脚本等
```

## 依赖

- Python 包来自 `source/packages/`（`llm_core`、`rag_core` 等），通过根 `pyproject.toml` path 依赖引入。
- 学习期串联见 `source/apps/review_assistant/`；07/00 起新功能以本目录为准。

## 项目版本

V0–V6 路线见 [course/07_projects/outline.md](../course/07_projects/outline.md)。
