# app_log

`app_log` 是整个仓库共享的结构化日志与终端呈现 package。`llm_core`、`rag_core`、后续 `agent_core` / `eval_core`、所有 demo、app 和 `review_assistant` 都使用这一入口，不各自维护颜色、缩进和日志格式。

## 公共入口

```python
from app_log import configure_logging, console, get_logger

configure_logging(log_format="compact", level="INFO", color="auto")
log = get_logger(__name__)
log.info("document.loaded", "文档加载完成", filename="rules.pdf")
console.success("实验完成")
```

package 使用 `get_logger()` 记录结构化事件；demo 和产品入口使用 `console` 组织表格、摘要与提示。领域 package 不直接决定终端布局。

## 输出模式

| 模式 | 用途 |
| --- | --- |
| `compact` | 默认人类可读日志 |
| `verbose` | 展示事件字段和实验诊断 |
| `json` | 每行一个机器可读事件 |
| `quiet` | 只保留 warning 和 error |

`source/python_base/` 是基础练习，不要求迁移到本 package。

## 当前边界

当前只提供结构化事件、Rich 终端输出、JSON Lines、CLI 参数与敏感字段脱敏。Trace、Span、Metrics、日志持久化、OpenTelemetry 和 Dashboard 进入后续质量与工程观测阶段，不在这里提前实现。
