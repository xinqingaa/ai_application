# 可靠调用与结构化错误实验

配套机制：[Reliability、错误分类与可见降级](../mechanisms/reliability-and-errors.md)。本实验观察重试、退避和错误分类，不证明模型输出质量。

```bash
uv run python source/demos/llm_reliability_lab/reliability_compare.py
```

运行前预测哪些错误可重试，哪些必须立即失败。查看 attempt、latency、final config、error kind 和最终状态；缺少 Key、鉴权失败和模型不支持不能被重试伪装成成功。

排查顺序：本地配置 → 请求构造 → Provider 错误 → 重试策略 → 最终报告。读码入口见 `source/demos/llm_reliability_lab/README.md`。改变一个重试参数并运行 `llm_core` 相关测试。
