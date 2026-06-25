# source/03_rag

这个目录用于承载 `03_rag` 的配套代码。

代码服务 RAG 知识系统和需求评审助手项目，不要求每篇文档都有对应脚本。

建议结构：

```text
source/03_rag/
├── packages/
│   ├── rag_core/
│   ├── rag_eval/
│   └── rag_memory/
├── demos/
│   ├── minimal_rag/
│   ├── chunking_comparison/
│   ├── retrieval_comparison/
│   ├── sources_refusal_demo/
│   └── rag_eval_demo/
├── apps/
│   └── review_assistant_v0/
└── README.md
```

`rag_core` 负责主链路，`rag_eval` 负责评估与回归，`rag_memory` 先保持轻量，`review_assistant_v0` 负责需求评审助手 V0 最小闭环。
