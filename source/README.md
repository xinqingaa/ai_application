# source/

扁平化的学习与共享代码根目录。历史按课程编号镜像的结构已废弃；回溯请用 Git tag。

## 当前结构（实物清单）

```text
source/
├── packages/
│   └── llm_core/          # 02_llm/00–03
├── demos/
│   ├── 02_first_chat/     # 02_llm/00
│   └── 02_provider_switching/   # 02_llm/01–03（含 structured_risk.py）
└── python_base/           # 已完成 Python 基础练习
```

可部署产品（`07_projects` 起）在仓库根 [review_assistant/](../review_assistant/)，**import** 本目录 `packages/`，不 copy。

## 约定

- 目录规范与禁止占位：见 [docs/learning-guide.md](../docs/learning-guide.md) §6.4、§10。
- 每门课 **00**：在 `packages/` 创建或扩展本课 `*_core` + 第一个 demo（若当节正文要求）。
- 每节 **01+**：优先在同一 package 上增量修改；demo 仅在需要新观测方式时新增或扩展。
- 安装：根目录 `pip install -e .`（见 `pyproject.toml`）。

**本文件**仅在 `source/` 顶层增删目录时更新一行；各课 `outline.md` 不维护文件树。
