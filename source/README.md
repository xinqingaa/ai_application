# source

`source/` 保存可复用 AI 能力、机制实验和学习期组合入口。

它不是课程目录的镜像，也不是最终产品的平行实现。

## 当前结构

```text
source/
├── packages/
│   └── llm_core/              # 模型调用、契约、上下文与调用治理
├── demos/
│   ├── llm_invoke_lab/        # SDK 对照、Provider、Prompt、Structured
│   ├── llm_reliability_lab/   # Reliability 与可见降级
│   ├── llm_context_lab/       # Context Builder（等待 RAG 前置）
│   └── llm_regression_lab/    # Harness、成本、延迟与缓存
├── apps/
│   └── llm_streaming_api/     # 按需：FastAPI + SSE 学习期组合入口
└── python_base/               # 已完成的 Python 基础练习
```

demo 按标准学习路径的观察段落组织，使用语义名称，不携带课程章节编号。相近观察合并进同一 lab；不为每篇文档新建目录。

## 目录职责

### `packages/`

- 保存通用能力的唯一实现。
- 每个能力域全仓库只有一个 package 实例。
- demo、app 和 `review_assistant/` 都通过 import 复用。
- 核心算法、数据类型、错误边界和可复用服务进入 package。
- package 职责增多时按能力子目录组织，不在根目录持续堆单文件。

### `demos/`

- 用于机制实验、策略对照和稳定失败复现。
- 不承担最终产品逻辑。
- 优先复用已有 lab；只有新的观察维度确实无法承载时才增加目录。
- 每个 lab README 标明课表位置、跑序和允许的调用面。
- Mock 只允许用于确定性测试或明确标注的故障对照，真实模型仍是主路径。

### `apps/`

- 用于学习期组合多个 package，例如验证 API、SSE 或交互协议。
- 可以短期承载集成实验，但不能和 `review_assistant/` 长期维护两份产品。
- 成熟能力进入产品后，产品入口和运行事实以 `review_assistant/` 为准。

### `python_base/`

- 保存已完成的 Python 基础练习。
- 默认不主动重构，除非用户明确要求。

## 与课程和产品的关系

```text
course/concepts/      解释概念
course/mechanisms/    解释机制并引用 package / demo
course/project/       定义阶段项目学习、检查点与验收
source/packages/      实现通用能力
source/demos/         观察和验证机制
source/apps/          学习期组合实验
review_assistant/     组合能力形成可运行产品
```

课程文档可以引用这里的真实代码，但不要求每篇文档都改变 `source/`。

## 运行与依赖

全仓库统一使用根目录 uv 环境：

```bash
uv sync
uv run ...
```

依赖只维护在根 `pyproject.toml` 和 `uv.lock`。具体 package、demo 和 app 的入口、配置与观察方式由各自 README 维护。

学习者先按 [标准学习路径](../course/learning-path.md) 确定当前机制，再进入对应 package、demo 或 app README。
