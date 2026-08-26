# 真实模型调用与 Provider 实验

配套机制：[Model API、调用生命周期与 Provider 抽象](../mechanisms/model-api-and-provider.md)。本实验观察同一调用契约怎样进入真实 Provider，以及配置或服务失败怎样暴露。

## 准备与运行

在根 `.env` 配置真实 Chat 模型凭证，随后运行：

```bash
uv run python source/demos/llm_invoke_lab/first_chat.py
uv run python source/demos/llm_invoke_lab/provider_switching.py --verbose
```

运行前预测：切换 Provider 配置只应改变模型端点和能力事实，不应改变业务调用入口。

## 观察与排查

先看请求配置、消息、模型响应、usage 和 latency，再区分缺少 Key、鉴权失败、模型不支持、限流与超时。真实失败不得变成静态回复。

读码顺序：`first_chat.py` → `provider_switching.py` → `llm_core/client` → `llm_core/providers`。修改一个 `config_ref` 或 temperature，预测哪些字段会变化，再运行对应测试。
