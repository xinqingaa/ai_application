# source/

扁平化的学习与共享代码根目录。历史按课程编号镜像的结构已废弃；当前主线按 **package 能力域 + 少量 demo lab + 学习期 app** 组织。

## 当前结构（实物清单）

```text
source/
├── packages/
│   └── llm_core/              # 02_llm 的可复用模型调用底座
├── demos/
│   ├── 02_llm_basics/         # 02_llm/00：SDK 最小调用
│   ├── 02_model_contracts/    # 02_llm/01–03：provider / prompt / structured
│   ├── 02_context_lab/        # 02_llm/05：context builder 观察
│   └── 02_call_ops_lab/       # 02_llm/06–08：reliability / harness / cost-latency
├── apps/
│   └── 02_llm_streaming_api/  # 02_llm/04：FastAPI SSE
└── python_base/               # 已完成 Python 基础练习
```

可部署产品（`07_projects` 起）在仓库根 [review_assistant/](../review_assistant/)，**import** 本目录 `packages/`，不 copy。

## 约定

- 目录规范与禁止占位：见 [docs/learning-guide.md](../docs/learning-guide.md) §6.4、§10。
- `source/packages/*_core` 是能力沉淀主战场；同一能力域只维护一个 package 实例。
- `source/demos` 不按课程节号镜像创建；相近能力合并到已有 lab，只有出现新的观察维度时才新增 lab。
- package 内能力增长到多个职责时，应目录化为子包，不在 package 根目录持续堆单文件模块。
- 安装 / 同步：根目录 `uv sync`（见 `pyproject.toml` 与 `uv.lock`）。

**本文件**仅在 `source/` 顶层目录或 demo lab 职责变化时更新；各课 `outline.md` 不维护完整文件树。
