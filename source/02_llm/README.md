# source/02_llm

这个目录用于承载 `02_llm` 的配套代码。

代码不按章节机械堆脚本，而是围绕可复用 package、关键 demo 和后续项目底座组织。

## 专题文档

| 文档 | 说明 |
| --- | --- |
| [course/02_llm/00_llm_problem_space.md](../course/02_llm/00_llm_problem_space.md) | LLM 应用问题空间 |
| [course/02_llm/01_model_api_and_provider_abstraction.md](../course/02_llm/01_model_api_and_provider_abstraction.md) | Model API 与 Provider 抽象 |
| [course/02_llm/02_prompt_engineering_for_apps.md](../course/02_llm/02_prompt_engineering_for_apps.md) | 面向应用的 Prompt Engineering |
| [course/02_llm/03_structured_outputs.md](../course/02_llm/03_structured_outputs.md) | Structured Outputs |
| [course/02_llm/outline.md](../course/02_llm/outline.md) | 课程大纲 |

## 建议结构

```text
source/02_llm/
├── packages/
│   └── llm_core/
├── demos/
│   ├── provider_switching/
│   ├── structured_review_output/
│   ├── streaming_chat/
│   ├── context_budgeting/
│   ├── reliability_demo/
│   └── llm_harness_eval/
└── README.md
```

`llm_core` 是后续 `03_rag`、`04_agent` 和 `07_projects` 复用的模型调用底座。
