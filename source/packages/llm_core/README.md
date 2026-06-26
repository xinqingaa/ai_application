# llm_core

需求评审助手的 **LLM 模型交互底座**，供 RAG、Agent、Workflow 与评估观测复用。

## 职责边界

| 负责 | 不负责 |
| --- | --- |
| 统一模型调用、Prompt、Schema、usage 记录 | 文档入库与向量检索（`rag_core`） |
| Provider 切换与错误分类（01 起） | Tool 执行与多 Agent 编排（`agent_core`） |
| 流式事件、上下文预算、harness（04–07） | 完整评审业务与人工审批流程 |

## 当前进度（02_llm/00）

- 本目录为 **package 壳**（`__version__` 可 import）。
- 第一个可运行 demo：[../../demos/02_first_chat/](../../demos/02_first_chat/) — 直接用 OpenAI SDK 完成最小 chat，观察 `usage` 与 `latency_ms`。
- `LLMClient`、`providers/`、`models.yaml` 等从 **01** 起在本包内实现。

## 安装

```bash
# 仓库根目录
pip install -e .
python -c "import llm_core; print(llm_core.__version__)"
```

## 目标结构（全课收敛对照，非 00 预建）

```text
llm_core/
├── client.py           # 01
├── providers/          # 01
├── prompts/            # 02
├── schemas/            # 03
├── context/            # 05
├── streaming/          # 04
├── reliability/        # 06
└── harness/            # 07
```

详见 [course/02_llm/00_llm_problem_space.md](../../../course/02_llm/00_llm_problem_space.md)。
