# 06. RAG 生成 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/04_rag/06_rag_generation.md) 学完第六章，并把第五章的检索结果真正接成一个稳定的问答闭环。

---

## 核心原则

```text
先看候选如何进入 Prompt -> 再看答案和 sources 如何对齐 -> 最后再接真实 LLM 和 LCEL
```

- 在 `source/04_rag/06_rag_generation/` 目录下操作
- 本章主线仍然是生成闭环，不重新展开检索策略
- 当前章节分成两层：
  - 稳定主线：context selection、formatter、Prompt、answer + sources、refusal
  - 扩展主线：真实 LLM 接入、LCEL RAG Chain
- 真实 LLM 调用参考 `02_llm/02_multi_provider` 的最小抽象方式，但不会把第二章整套多平台教学复制进来

---

## 项目结构

```text
06_rag_generation/
├── README.md
├── requirements.txt
├── llm_utils.py
├── generation_basics.py
├── 01_inspect_prompt.py
├── 02_query_demo.py
├── 03_refusal_demo.py
├── 04_real_llm_demo.py
├── 05_lcel_rag_chain.py
├── store/
│   └── demo_generation_store.json
└── tests/
    └── test_generation.py
```

- `llm_utils.py`
  放第六章最小真实调用接缝：provider config、统一响应对象、OpenAI-compatible client
- `generation_basics.py`
  放本章核心对象：demo retriever、chapter 5 retriever adapter、context selection、Prompt、mock 生成器和 `RagService`
- `01_inspect_prompt.py`
  看候选结果如何被收缩成 Prompt
- `02_query_demo.py`
  跑一次完整的 mock `question -> answer + sources`
- `03_refusal_demo.py`
  对比“可回答”和“应拒答”两类问题
- `04_real_llm_demo.py`
  把第五章检索器接到真实 LLM 或 mock fallback
- `05_lcel_rag_chain.py`
  用 LCEL 重写第六章最小 RAG 闭环

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/06_rag_generation
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python 01_inspect_prompt.py
python 02_query_demo.py
python 03_refusal_demo.py
python 04_real_llm_demo.py
python 04_real_llm_demo.py --backend chroma --strategy mmr --provider openai
python 05_lcel_rag_chain.py
python -m unittest discover -s tests
```

### 4. 环境变量

真实调用默认会读取 `DEFAULT_PROVIDER`，并从对应平台读取：

- `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL`
- `BAILIAN_API_KEY / BAILIAN_BASE_URL / BAILIAN_MODEL`
- `DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL`
- `GLM_API_KEY / GLM_BASE_URL / GLM_MODEL`

如果环境未配置完整，第六章会自动回退到 mock，不会中断主线学习。

---

## 第 1 步：先看输入和输出契约

**对应文件**：[generation_basics.py](./generation_basics.py)

重点观察：

- 为什么输入应该是稳定 `RetrievalResult[]`
- 为什么输出应该是稳定 `AnswerResult`
- `RagService.ask()` 为什么要先筛上下文、再生成、再对齐 `sources`

---

## 第 2 步：看候选结果如何被收缩成 Prompt

**对应文件**：[generation_basics.py](./generation_basics.py)、[01_inspect_prompt.py](./01_inspect_prompt.py)

重点观察：

- `GenerationDemoRetriever` 如何服务当前 mock 教学语料
- `filter_retrieval_results()` 如何根据 `min_context_score` 挡掉弱相关 chunk
- `prompt_results` 为什么可能少于 `retrieved_results`
- 为什么 `max_chunks` 是上下文边界，而不是细节参数

---

## 第 3 步：看检索结果如何变成上下文

**对应文件**：[generation_basics.py](./generation_basics.py)、[01_inspect_prompt.py](./01_inspect_prompt.py)

重点观察：

- `format_context()` 如何生成 `[S1] / [S2]`
- 为什么上下文里还要显式保留 `filename / chunk_index`
- 为什么现在会同时展示 `retrieval_score / context_score`

---

## 第 4 步：先跑 mock 闭环，再看拒答

**对应文件**：[02_query_demo.py](./02_query_demo.py)、[03_refusal_demo.py](./03_refusal_demo.py)

重点观察：

- `MockLLMClient.generate()`
- `_build_mock_answer()`
- `select_used_results()`
- `RagService.ask()`

运行后重点看：

- 回答里是否出现 `[S1]`
- `sources` 是否只返回答案实际使用到的来源
- 为什么“火星首都是什么？”会在生成前直接拒答

---

## 第 5 步：接真实 LLM，但不破坏主线

**对应文件**：[llm_utils.py](./llm_utils.py)、[04_real_llm_demo.py](./04_real_llm_demo.py)

重点观察：

- `load_generation_provider_config()` 如何把环境变量收束成配置对象
- `OpenAICompatibleLLMClient` 如何复用第二章的 OpenAI-compatible 调用方式
- `create_generation_client()` 为什么要保留 mock fallback
- `Chapter5StrategyRetriever` 如何把第五章的 `backend / strategy` 直接接进第六章

建议先跑：

```bash
python 04_real_llm_demo.py
```

然后再改参数：

```bash
python 04_real_llm_demo.py --backend chroma --strategy mmr --provider bailian
python 04_real_llm_demo.py "为什么 metadata 很重要？" --filename metadata_rules.md
```

这里最重要的观察点是：

- 没有真实环境时，为什么仍然能看到 provider 信息和 fallback 原因
- 第五章检索策略变化，怎样影响第六章最终答案和来源

---

## 第 6 步：看 LCEL 如何重写同一条链路

**对应文件**：[05_lcel_rag_chain.py](./05_lcel_rag_chain.py)

重点观察：

- `retriever -> context -> ChatPromptTemplate -> LLMClient -> StrOutputParser`
- 为什么 LCEL 不是“另一套 RAG”，而只是把当前链路换成标准可组合写法
- 为什么第六章这里仍然不引入完整服务层

建议跑：

```bash
python 05_lcel_rag_chain.py
```

运行后重点看：

- Prompt Preview 是否仍然是你前面已经理解过的那套 Prompt
- LCEL 版本和手写版本的上下文、答案边界是否一致

---

## 建议学习顺序

1. 先读 [第六章学习文档](../../../docs/04_rag/06_rag_generation.md)
2. 跑 `python 01_inspect_prompt.py`
3. 跑 `python 02_query_demo.py`
4. 跑 `python 03_refusal_demo.py`
5. 跑 `python 04_real_llm_demo.py`
6. 最后跑 `python 05_lcel_rag_chain.py`

---

## 学完这一章后你应该能回答

- 为什么第五章的 `RetrievalResult[]` 还不能直接等于模型输入
- 为什么第六章必须显式增加 context selection
- 为什么真实 LLM 接入应该抽取最小配置层，而不是在业务代码里散落 provider 判断
- 为什么一个稳的最小返回结构应该是 `answer + sources`
- 为什么 LCEL 是第六章链路的标准表达，不是另一套平行体系

---

## 当前真实进度和下一章

- 当前真实进度：第六章已经同时具备 mock 主线、真实 LLM fallback 主线、LCEL 最小链路
- 完成标准：能解释 context selection、Prompt、答案引用、拒答、真实调用接缝和 LCEL 对照关系
- 下一章：继续做效果评估，判断一次改动到底改善了检索、生成还是两者都没有改善
