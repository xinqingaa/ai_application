# 02_provider_switching

`02_llm/01` demo：用 `LLMClient` + `config_ref` 对同一 `messages` 切换模型配置，对比 `latency_ms`、token 与输出。

00 的 [`02_first_chat`](../02_first_chat/) 仍保留直调 OpenAI SDK，用于对照「抽象前后」的差异。

## 前置

```bash
# 仓库根目录
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # 填写 OPENAI_API_KEY
```

## 配置 OpenAI（默认）

`.env` 示例：

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# OPENAI_STRUCTURED_MODEL=gpt-4o   # structured_chat 用，可选
```

## 配置 DeepSeek（OpenAI 兼容）

在 `.env` 中改为：

```bash
OPENAI_API_KEY=你的DeepSeek密钥
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
OPENAI_STRUCTURED_MODEL=deepseek-chat
```

无需改 Python 代码；`models.yaml` 通过 `${OPENAI_BASE_URL}` / `${OPENAI_MODEL}` 读取。

## 运行

```bash
cd source/demos/02_provider_switching

# 默认对比 chat.dev_chat 与 chat.structured_chat
python provider_switching.py

# 打印完整 system/user、请求参数、assistant 全文、usage
python provider_switching.py --verbose

# 指定 config_ref 列表
python provider_switching.py --configs chat.dev_chat,chat.fallback_chat

# 固定 S2，覆盖 temperature 做对比
python provider_switching.py --temperature 0.7
```

## 应看到什么

1. 先输出完整对比表：`config_ref`、`model`、`latency_ms`、`total_tokens`、`content` 预览（含 ERROR 行）  
2. `--verbose` 时：表后再按 `config_ref` 输出 `llm_core.observability` 格式化的完整请求与响应  
3. 无 `OPENAI_API_KEY` 时：明确错误并以非零退出

## models.yaml 走读

配置真源：[`source/packages/llm_core/config/models.yaml`](../../packages/llm_core/config/models.yaml)

| config_ref | 用途 |
| --- | --- |
| `chat.dev_chat` | 日常开发、Prompt 试验 |
| `chat.structured_chat` | 结构化输出任务（专题 03 深化） |
| `chat.fallback_chat` | 限流/兜底 |
| `embedding.default_embed` | 预置给 `03_rag`，01 不调用 |

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- 学习文档：[course/02_llm/01_model_api_and_provider_abstraction.md](../../../course/02_llm/01_model_api_and_provider_abstraction.md)
- 上一节 demo：[02_first_chat](../02_first_chat/)
