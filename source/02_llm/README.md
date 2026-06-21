# source/02_llm

这个目录用于承载 `02_llm` 的配套代码。

代码不按章节机械堆脚本，而是围绕可复用 package、关键 demo 和后续项目底座组织。

建议结构：

```text
source/02_llm/
├── packages/
│   └── llm_core/
├── demos/
│   ├── provider_switching/
│   ├── structured_review_output/
│   ├── streaming_chat/
│   ├── context_budgeting/
│   └── llm_harness_eval/
└── README.md
```

`llm_core` 是后续 `03_rag`、`04_agent` 和 `07_projects` 复用的模型调用底座。
