# Prompt 单变量对照实验

配套机制：[面向应用的 Prompt Engineering](../mechanisms/prompt-engineering.md)。本实验固定模型和样例，只改变 Prompt 版本。

```bash
uv run python source/demos/llm_invoke_lab/prompt_compare.py
```

运行前先比较各 Prompt 版本唯一新增的任务、证据、约束或输出要求。观察同一需求下风险覆盖、无依据扩写、格式稳定性、Token 和延迟，不用更换样例证明某个版本更好。

排查顺序：样例 → Prompt 版本 → 渲染后的 messages → Provider 请求 → 模型结果。读码入口是 `prompt_compare.py`、`llm_core/prompts/registry.py` 和对应 YAML。修改一个约束后使用同一组样例重新对照。
