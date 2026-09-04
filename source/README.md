# source

`source/` 是全部真实代码的唯一根目录。

```text
source/
├── packages/                  通用能力唯一实现
├── demos/                     机制实验代码
├── apps/review_assistant/     唯一产品
└── python_base/               已完成的基础练习
```

## `packages/`

每个能力域只维护一个 package。核心算法、数据类型、错误契约和可复用服务进入 package；demo 和产品通过 import 复用。

## `demos/`

用于机制观察、策略对照和稳定失败复现，不承担最终产品逻辑。完整实验教材位于 `course/lessons/`；demo README 只维护代码入口、文件职责、测试和对应实验链接。

## `apps/review_assistant/`

唯一长期应用，负责产品 API、工作台、业务组合、fixtures、migration、测试、运行和部署。其他实验性 API 或页面进入 `demos/`，不形成第二个 app。

## 运行

全仓库使用根目录一个 uv 环境：

```bash
uv sync
uv run ...
```

依赖只维护在根 `pyproject.toml` 和 `uv.lock`。学习顺序由 [course/learning-path.md](../course/learning-path.md) 决定。
