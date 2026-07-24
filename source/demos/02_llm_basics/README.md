# 02_llm_basics

模型最小调用观察 demo：用 OpenAI SDK 发起一次真实 chat，打印 `usage` 与 `latency_ms`。

Provider 抽象与 `LLMClient` 见 `source/demos/02_model_contracts/`。

## 前置

1. 仓库根目录已同步 uv 环境：

   ```bash
   uv sync
   ```

2. 配置 API Key（**必须**，本 demo 不做 mock）：

   ```bash
   cp .env.example .env
   # 编辑 .env，填写 OPENAI_API_KEY
   # 若使用 OpenAI 兼容平台，可设置 OPENAI_BASE_URL 与 OPENAI_MODEL
   ```

## 运行

```bash
cd source/demos/02_llm_basics

# 默认：样例 S2（售后 PRD 风险识别），temperature=0
uv run python first_chat.py

# 对比实验：同一输入，不同 temperature
uv run python first_chat.py --temperature 0.7

# 换模型或样例（S1–S5 见 samples.json）
uv run python first_chat.py --model gpt-4o-mini --sample S3
```

## 应看到什么

终端输出至少包含：

| 字段 | 含义 |
| --- | --- |
| `sample` | 当前 harness 样例 id 与类型 |
| `model` | 请求与响应中的模型 id |
| `usage.prompt_tokens` / `completion_tokens` | 计费与上下文体量 |
| `latency_ms` | 端到端耗时（毫秒） |
| `content preview` | 模型生成文本前 300 字 |

无 `OPENAI_API_KEY` 时应打印配置指引并以非零退出码结束。

## 对比实验建议

用**同一条样例**（默认 S2）记录表格：`model`, `temperature`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `notes`。

```bash
uv run python first_chat.py --temperature 0
uv run python first_chat.py --temperature 0.7
```

观察风险表述是否更发散、是否出现材料中未写的模块名。

## 样例集

[`samples.json`](samples.json) 对应 [LLM 概念篇的最小调用样例集](../../../course/concepts/llm-in-ai-applications.md#最小调用样例集建议先收-5-条)（S1–S5），供调用 Harness 复用。

## 相关

- Package 壳：[source/packages/llm_core/](../../packages/llm_core/)
- 学习文档：[LLM 在 AI 应用中的位置与边界](../../../course/concepts/llm-in-ai-applications.md)
