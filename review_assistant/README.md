# 需求评审助手（review_assistant）

`07_projects` 起的**可部署产品真源**。学习阶段在 `source/packages/` 积累能力；本目录 import 共享包并组装 API、工作台与 infra。

## 结构（逐步填充）

```text
review_assistant/
├── app/            # FastAPI 等服务入口（07 起创建）
├── workbench/      # Vue / Flutter 工作台
└── infra/          # docker-compose、迁移脚本等
```

子目录在 `07_projects` 当节正文落地时创建，**不预建占位**。

## 依赖

- Python 包来自 `source/packages/`（如 `llm_core`），通过根 `pyproject.toml` editable 安装引入。
- 学习期串联可在 `source/apps/` 建应用壳（当节正文要求时）；`07_projects` 起新功能以本目录为准。

## 项目版本

V0–V6 路线见 [course/07_projects/outline.md](../course/07_projects/outline.md)。
