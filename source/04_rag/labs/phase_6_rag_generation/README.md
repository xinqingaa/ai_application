# phase_6_rag_generation - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md) 阅读第六章代码快照。

---

## 核心原则

```text
先确认 Phase 5 已经稳定召回上下文 -> 再看 context formatter 和 RAG Prompt -> 再看 RagService 如何做筛选、生成和 answer + sources -> 最后用脚本与测试验证引用和拒答边界
```

- 在 `source/04_rag/labs/phase_6_rag_generation/` 目录下操作
- 这一章的重点不是“接个模型就算做完”，而是把检索结果翻译成受控上下文，再把回答边界固定住
- 检索侧继续复用真实 Chroma 和上一章的 `ChromaRetriever`
- 生成侧默认用 `mock`，保证没有 API Key 也能完整学习；需要真实模型时切到 `openai_compatible`
- 本章保持最小返回结构：`answer + sources`

---

## 本章定位

- 对应章节：[06_rag_generation.md](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md)
- 本章目标：把检索结果组织成模型可读上下文，接入最小生成客户端，返回带来源的答案，并处理无答案问题
- 上一章输入契约：稳定 `ChromaRetriever`、稳定 `RetrievalResult[]`、稳定 `similarity / threshold / MMR / metadata filter`
- 输出契约：固定 `RAG Prompt`、固定 `context formatter`、最小 `LLMClient` 抽象、真实 `RagService` 问答链路、可回归测试
- 本章新增：`app/prompts/rag_prompt.py`、`app/chains/rag_chain.py`、`app/llms/providers.py`、`scripts/inspect_prompt.py`、`tests/test_generation.py`
- 本章可忽略：Golden Set 评估、Rerank、混合检索、HyDE、多路召回、完整 API 服务
- 第一命令：`python scripts/query_demo.py`

---

## 项目结构

```text
phase_6_rag_generation/
├── README.md
├── requirements.txt
├── app/
│   ├── chains/
│   │   └── rag_chain.py
│   ├── llms/
│   │   ├── __init__.py
│   │   └── providers.py
│   ├── prompts/
│   │   └── rag_prompt.py
│   ├── retrievers/
│   ├── services/
│   │   └── rag_service.py
│   ├── vectorstores/
│   └── ...
├── scripts/
│   ├── inspect_prompt.py
│   ├── query_demo.py
│   ├── compare_retrievers.py
│   └── review_bad_cases.py
└── tests/
    ├── test_generation.py
    ├── test_retrievers.py
    └── test_vectorstores.py
```

这一章真正新增的主角只有四块：

1. `app/prompts/rag_prompt.py`
2. `app/chains/rag_chain.py`
3. `app/llms/providers.py`
4. `app/services/rag_service.py / scripts/inspect_prompt.py / tests/test_generation.py`

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/labs/phase_6_rag_generation
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python scripts/index_chroma.py --reset
python scripts/query_demo.py
python scripts/query_demo.py "What is the capital of Mars?" --strategy threshold --threshold 0.70
python scripts/inspect_prompt.py
python scripts/query_demo.py --llm-provider openai_compatible --llm-model gpt-4o-mini
python -m unittest discover -s tests
```

如果要走真实生成路径，还需要：

```bash
export OPENAI_API_KEY=...
```

如果你用的是兼容网关，也可以额外设置：

```bash
export OPENAI_BASE_URL=...
```

### 4. 先跑哪个

建议先跑：

```bash
python scripts/query_demo.py
```

你现在最该先建立的直觉是：

- 检索结果不是直接塞给模型，而是先要经过上下文格式化
- 第六章开始，系统终于有了“回答边界”，不再是只打印检索结果
- “我不知道”是主线能力，不是异常分支

---

## 第 1 步：先确认第六章真正继承了什么

**对应文件**：`app/retrievers/chroma.py`、`scripts/compare_retrievers.py`、`tests/test_retrievers.py`

### 这一步要解决什么

- 第六章不是重做检索，而是站在第五章稳定 Retriever 之上继续长
- 当前问答链路吃到的仍然是 `RetrievalResult[]`
- 如果检索质量不稳，第六章生成层只会把问题放大，不会自动修复

### 重点观察

- `RetrievalStrategyConfig`
- `ChromaRetriever.retrieve()`
- `score_threshold`
- `metadata_filter`

---

## 第 2 步：看检索结果如何翻译成 Prompt 上下文

**对应文件**：`app/chains/rag_chain.py`、`app/prompts/rag_prompt.py`

### 这一步要解决什么

- 为什么 `RetrievalResult[]` 还不是模型最适合消费的输入
- 为什么上下文里要显式保留 `[S1] / [S2]` 这样的来源标签
- 为什么要限制 `max_chunks` 和 `max_chars_per_chunk`

### 重点观察

- `format_context()`
- `_truncate_content()`
- `build_messages()`
- `RAG_SYSTEM_PROMPT`
- `RAG_USER_TEMPLATE`

### 建议主动修改

- 改 `default_context_max_chunks`
- 改 `default_context_max_chars_per_chunk`
- 修改 Prompt 里的回答要求，再跑 `inspect_prompt.py`

---

## 第 3 步：看生成客户端如何保持最小抽象

**对应文件**：`app/llms/providers.py`

### 这一步要解决什么

- 为什么课程里不把生成直接写死在一个 SDK 调用里
- 为什么 `openai_compatible` 和 `mock` 要共享同一份 `LLMClient` 接口
- 为什么默认要保留 mock fallback，而不是把学习入口绑死在外部 API

### 重点观察

- `GenerationProviderConfig`
- `GenerationResult`
- `LLMClient`
- `OpenAICompatibleLLMClient`
- `MockLLMClient`
- `create_generation_client()`

### 建议主动修改

- 把 `default_generation_provider` 从 `mock` 切成 `openai_compatible`
- 改 `default_generation_max_tokens`
- 给 `OPENAI_BASE_URL` 配兼容网关，再看实际回包是否仍走同一抽象

---

## 第 4 步：看 RagService 如何把检索和生成接起来

**对应文件**：`app/services/rag_service.py`、`scripts/query_demo.py`

### 这一步要解决什么

- 为什么服务层返回结构必须是 `answer + sources`
- 为什么第六章要把 `min_source_score` 放在生成前，而不是回答后
- 为什么 `query_demo.py` 现在同时要打印检索策略、生成提供方和最终来源

### 重点观察

- `filter_retrieval_results()`
- `RagService.ask()`
- `last_messages`
- `last_generation_result`
- `last_retrieval_results`

### 建议先跑

```bash
python scripts/query_demo.py
python scripts/query_demo.py --strategy mmr
python scripts/query_demo.py "What is the capital of Mars?" --strategy threshold --threshold 0.70
```

运行后重点看：

- 命中问题时，回答里是否出现 `[S1]`
- 无答案问题时，生成步骤是否被直接跳过
- `sources` 是否和最终进入 Prompt 的 chunk 对齐

---

## 第 5 步：用 Prompt 检视脚本建立调试习惯

**对应文件**：`scripts/inspect_prompt.py`

### 这一步要解决什么

- 如何区分“检索到的原始结果”和“真正进入生成上下文的结果”
- 为什么 Prompt 调试不能只看最终答案
- 为什么第六章开始要养成先看上下文再看输出的习惯

### 建议先跑

```bash
python scripts/inspect_prompt.py
python scripts/inspect_prompt.py --strategy threshold --threshold 0.70
python scripts/inspect_prompt.py --filename product_overview.md
```

运行后重点看：

- 原始召回 `raw[i]` 和最终接受块的差异
- `[S1] / [S2]` 对应的 chunk 元数据是否完整
- 被截断后的上下文是否仍保留关键事实

---

## 第 6 步：最后看测试在锁定什么

**对应文件**：`tests/test_generation.py`

### 重点观察

- `test_format_context_includes_labels_metadata_and_score()`
- `test_build_messages_carries_system_prompt_context_and_question()`
- `test_rag_service_returns_no_answer_when_retriever_returns_nothing()`
- `test_rag_service_filters_out_low_score_results_before_generation()`
- `test_rag_service_returns_answer_and_sources_with_mock_llm()`

测试现在锁定的不是“脚本能跑”，而是：

- 上下文格式里保留了引用标签和 metadata
- Prompt 消息包含问题、上下文和回答约束
- 无答案时服务层会直接返回拒答
- 低分结果不会被送进生成模型
- mock 生成也能稳定返回 `answer + sources`

---

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. `app/config.py`
2. `app/prompts/rag_prompt.py`
3. `app/chains/rag_chain.py`
4. `app/llms/providers.py`
5. `app/services/rag_service.py`
6. `scripts/inspect_prompt.py`
7. `scripts/query_demo.py`
8. `tests/test_generation.py`

## 建议主动修改的地方

1. 把 `default_generation_min_score` 从 `0.60` 调高到 `0.70`，看拒答率会怎么变化。
2. 把 `default_context_max_chunks` 改成 `2`，再观察回答是否开始丢失依据。
3. 把 `RAG_USER_TEMPLATE` 里的引用要求删掉，再跑 `query_demo.py`，看输出是否更容易丢来源。
4. 在 `query_demo.py` 里切到 `--llm-provider openai_compatible`，对比 mock 和真实模型的回答差异。

## 学完这一章后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么很多问题应该先看检索再看 Prompt
- `top_k / threshold / MMR / filter` 各自解决什么问题
- 什么时候只是调参数就够，什么时候才值得升级到混合检索或 Rerank

## 当前真实进度和下一章

- 当前真实进度：第五章已经交付可替换 Retriever 和基础策略实验，但还没有进入真正的生成链
- 完成标准：能稳定返回检索结果，能解释检索失败原因，能判断是否需要增强检索
- 下一章：把当前 Retriever 输出接进 Prompt 和答案生成，形成真正的 RAG Chain
