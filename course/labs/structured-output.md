# Structured Output 与校验实验

配套机制：[Structured Output 与应用侧校验](../mechanisms/structured-output.md)。本实验观察“模型返回了 JSON”与“结果可以进入应用”之间的差异。

```bash
uv run python source/demos/llm_invoke_lab/structured_risk.py
```

运行前预测正常结构、解析失败、Schema 失败和业务校验失败分别出现在哪一层。重点查看原始响应、解析结果、校验错误、最终业务对象和真实 Provider 能力。

读码顺序：`structured_risk.py` → `llm_core/structured` → `llm_core/schemas`。修改一个字段约束，补充或调整测试，确认失败不会被静默修成成功。
