# foundation_lab

`foundation_lab` 是 `03_foundation` 阶段的独立基础实验项目，用来把文档里已经固定的抽象和工程边界落成最小代码骨架。

这份 README 的定位不是再讲一遍完整原理，而是承担三件事：

1. 说明当前代码已经做到哪里
2. 指出当前最应该阅读和修改的入口
3. 作为 `Phase 1 -> Phase 6` 的项目实施入口文档

当前版本重点是：

- 固定 `config / llm / prompts / chains / retrievers / tools / services / observability` 分层
- 同时保留 native 与 langchain 两套入口
- 提供 `mock_retriever`、`mock_tool`、`qa_service` 的最小占位实现
- 为后续真正接入模型、FastAPI、LangChain 留出稳定扩展点

## 当前状态

当前项目还是骨架版，不追求完整功能，而是先保证：

- 目录结构稳定
- 模块职责清晰
- 文档里的 Phase 1 文件已经落地
- 在没有外部依赖和真实模型配置时，也能通过 mock 路径演示最小流程

当前真实进度应理解为：

- `Phase 1` 已完成
- `Phase 2-6` 还没有完成

也就是说，这个项目现在已经不是“还没开始”，但也远远不是“已经做完”。

## 这份 README 和主文档的关系

如果你要理解“为什么项目要这样设计”，应该先回到主文档：

- [docs/03_foundation/05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
- [docs/03_foundation/06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
- [docs/03_foundation/07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

如果你要知道“当前代码已经做到哪一步”，优先看这份 README。

一句话说：

- `docs/03_foundation/*.md` 负责约束项目应该长成什么样
- 本 README 负责说明项目现在实际长成什么样

## 目录结构

```plain
foundation_lab/
  app/
    config.py
    main.py
    schemas.py
    llm/
    prompts/
    chains/
    retrievers/
    tools/
    services/
    observability/
  scripts/
  tests/
```

## 当前阶段映射

| Phase | 当前状态 | 当前含义 |
|-------|----------|----------|
| `Phase 1` 项目骨架 | 已完成 | 目录、模块、脚本、测试骨架已经存在 |
| `Phase 2` 原生 SDK 最小能力 | 基础版已完成 | `client_native.py` 已支持 mock 回退、兼容端点普通调用、结构化示例和最小流式读取 |
| `Phase 3` LangChain 等价版本 | 未完成 | `client_langchain.py` 仍然是 mock 占位 |
| `Phase 4` 检索与工具边界验证 | 部分完成 | `mock_retriever`、`mock_tool` 已有最小占位，但仍可继续强化 |
| `Phase 5` 业务编排层 | 部分完成 | `qa_service.py` 已有最小路径编排，但还不是最终完成态 |
| `Phase 6` 接口与工程化收口 | 部分完成 | `main.py`、`logger.py`、测试和 README 已有骨架，但还未达到完整收口 |

## 第一入口

建议先看：

1. `app/services/qa_service.py`
2. `app/chains/qa_chain.py`
3. `app/retrievers/mock_retriever.py`
4. `app/tools/mock_tools.py`

如果你要对照文档继续补实现，回看：

- [docs/03_foundation/04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
- [docs/03_foundation/05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md)
- [docs/03_foundation/06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md)
- [docs/03_foundation/07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md)

如果你当前准备继续推进代码，建议按这个顺序进入：

1. 先看 `app/services/qa_service.py`
2. 再看 `app/chains/qa_chain.py`
3. 再看当前要补的 Phase 对应模块
4. 最后回到本 README 更新当前进度和运行方式

## 当前最值得继续补的地方

按 `07_foundation_lab_tasks.md` 的顺序，当前最合理的下一步是：

1. 补 `Phase 3`
2. 再加强 `Phase 4`
3. 然后继续收紧 `Phase 5-6`

也就是优先推进这些文件：

1. `app/llm/client_langchain.py`
2. `app/chains/qa_chain.py`
3. `scripts/demo_langchain.py`
4. `app/services/qa_service.py`

当前不建议先重写：

- `main.py`
- `logger.py`
- `tests/` 的规模

因为按照项目顺序，这些属于后续收口，不应该反过来抢在底层能力前面。

## Phase 使用方式

后续推进时，建议每个 Phase 都按同一套方式执行：

### `Phase 1`

目标：

- 固定目录结构和模块职责

当前状态：

- 已完成

完成标志：

- 代码目录存在
- 模块边界清晰
- 可以用 mock 路径跑最小脚本

### `Phase 2`

目标：

- 把 `client_native.py` 从占位实现补成真实最小模型调用

当前状态：

- 基础版已完成

已补内容：

- 兼容端点的最小普通调用
- 最小结构化输出示例
- 最小流式读取示例
- 未配置 API Key 时的 mock 自动回退

仍需继续验证：

- 真实 provider 联调结果
- 不同兼容端点的返回差异

### `Phase 3`

目标：

- 把 LangChain 风格路径从概念占位补成真正的最小链路

完成后本 README 应补：

- LangChain 相关依赖说明
- `demo_langchain.py` 的运行命令
- native 与 langchain 的对照说明

### `Phase 4`

目标：

- 强化 retriever 和 tool 的边界验证

完成后本 README 应补：

- `mock_retriever` 怎么验证
- `mock_tool` 怎么验证
- 两者边界如何理解

### `Phase 5`

目标：

- 让 `qa_service.py` 真正成为稳定统一的业务编排入口

完成后本 README 应补：

- 三条路径的选择逻辑
- `plain / retrieval / tool` 的最小流程图
- 当前 service 层负责什么、不负责什么

### `Phase 6`

目标：

- 让项目具备最小独立演示能力

完成后本 README 应补：

- API 运行命令
- `/ask` 和 `/ask/stream` 的请求示例
- 测试命令
- 当前已完成项与未完成项

## 当前可运行内容

## 运行方式

进入项目目录后，可先运行脚本：

```bash
cd source/03_foundation/foundation_lab
python3 scripts/demo_native.py
python3 scripts/demo_langchain.py
python3 scripts/compare_native_vs_lc.py
python3 -m unittest discover -s tests
```

当前这些命令的意义是：

- `demo_native.py`：验证 native 路径的普通调用、结构化输出和流式输出入口
- `demo_langchain.py`：验证 langchain 风格路径骨架存在
- `compare_native_vs_lc.py`：验证两条路径都能经过同一 service 层
- `unittest`：验证 Prompt、Retriever、Tool、Native Client 的最小测试骨架可运行

如果要尝试真实 native 调用，可额外提供这些环境变量：

```bash
export FOUNDATION_LAB_PROVIDER=openai
export OPENAI_API_KEY=your_api_key
export OPENAI_BASE_URL=https://api.openai.com/v1
```

不配置这些变量时，`demo_native.py` 会自动走 mock 路径。

如果后续安装了 `fastapi` 和 `uvicorn`，可以再尝试：

```bash
uvicorn app.main:app --reload --port 8000
```

但要明确：

- 当前 API 入口还是骨架状态
- 它已经可以作为收口位置存在
- 但还不是 `Phase 6` 完整收口后的最终形态

## 当前已验证内容

当前已经确认可工作的，是这些最小能力：

- 目录结构可导入
- `qa_service.py` 能统一调度最小路径
- `qa_chain.py` 能组织 `prompt -> llm -> parser` 骨架
- `client_native.py` 能在 mock 模式下演示普通、结构化和流式三类接口
- `mock_retriever` 能返回预置文档
- `mock_tool` 能返回预置结果
- 基础测试和 demo 脚本可以运行

当前还没有进入真实完成态的，是这些能力：

- 真实 native 模型调用的本地联调验证
- 真实 LangChain 组件调用
- 完整的流式实现
- 更完整的 API 演示与接口示例
- 更完整的测试覆盖

## 当前边界

当前故意不做这些事情：

- 真实向量数据库
- 真正的 LangChain 依赖接入
- 真正的 Agent 循环
- 复杂多步工作流
- 生产级配置、日志和部署

这些内容分别留到后续 Phase 和后续阶段继续补齐。

## 更新规则

后续每推进一个 Phase，优先更新这份 README 中的这些部分：

1. `当前状态`
2. `当前阶段映射`
3. `当前最值得继续补的地方`
4. `运行方式`
5. `当前已验证内容`

不要每推进一点实现就回头大改 `docs/03_foundation/05-07`。

只有当代码已经证明设计有偏差时，才回头修改主文档。
