# source/

扁平化的学习与共享代码根目录。历史按课程编号镜像的结构已废弃；回溯请用 Git tag。

## 结构

```text
source/
├── packages/          # *_core 全仓库单实例，02_llm/00 起在此创建与扩展
├── demos/             # {课号}_{名称}，如 02_first_chat、03_minimal_rag
├── apps/
│   └── review_assistant/   # 学习期应用壳（约 V0 起）
└── python_base/       # 已完成 Python 基础练习
```

可部署产品（`07_projects` 起）在仓库根 [review_assistant/](../review_assistant/)，**import** 本目录 `packages/`，不 copy。

## 约定

- 每门课 **00**：在 `packages/` 创建或扩展本课 `*_core` + `demos/{课号}_*` 第一个 demo。
- 每节 **01+**：在同一 package 上增量修改；demo 命名保留课号前缀。
- 安装：根目录 `pip install -e .`（见 `pyproject.toml`）。

详见 [docs/learning-guide.md](../docs/learning-guide.md) §6.4、§10。
