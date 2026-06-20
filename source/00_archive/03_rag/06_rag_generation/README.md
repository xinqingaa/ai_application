# 06. RAG 生成 - 实践指南

> 这份 README 只负责一件事：带你按正确顺序跑完第六章，先看检索候选怎样变成 Prompt，再看 `answer + sources`、拒答、真实 LLM fallback 和 LCEL，最后把“生成主线”和“真实接入”连起来。

---

## 核心原则

```text
先看候选如何进入 Prompt -> 再看 answer + sources -> 再看 refusal -> 最后接真实 LLM 和 LCEL
```

- 在 `source/04_rag/06_rag_generation/` 目录下操作
- 本章主线仍然是生成闭环，不重新展开检索策略
- 第六章当前有三条观察路径：
  - mock 主线：先把生成链路讲清楚
  - real LLM 路径：把同一条链路接到真实模型
  - LCEL 路径：把同一条链路换成标准链式表达
- 真实 LLM 调用参考 `02_llm/02_multi_provider` 的最小抽象方式，但不会把第二章整套多平台教学复制进来
- 第六章当前真正要立住的是：同一批 `RetrievalResult[]` 在应用层怎样收缩成可回答、可拒答、可追溯的 `answer + sources`

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
  第六章最小真实调用接缝：provider config、统一响应对象、OpenAI-compatible client
- `generation_basics.py`
  第六章主线文件：demo retriever、chapter 5 retriever adapter、context selection、formatter、Prompt、mock 生成器和 `RagService`
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
- `tests/test_generation.py`
  锁定 `format_context`、拒答、sources 对齐、mock fallback 和第五章运行时复用

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

## 先怎么读代码

### 1. 第一遍只看对象

先打开 [generation_basics.py](./generation_basics.py)，只看这些对象：

- `AnswerResult`
- `PromptInspection`
- `GenerationDemoRetriever`
- `Chapter5StrategyRetriever`
- `MockLLMClient`
- `ResilientGenerationClient`
- `RagService`

然后再补看：

- `GenerationProviderConfig`
- `GenerationResult`
- `OpenAICompatibleLLMClient`

这一遍的目标不是理解所有逻辑，而是先知道：

- 第六章有哪些最小运行时对象
- 哪些对象属于教学主线，哪些对象属于真实调用接缝
- 为什么第六章不是只返回一段答案

### 2. 第二遍只看主流程

然后再看这些函数和方法：

- `filter_retrieval_results()`
- `select_prompt_results()`
- `select_used_results()`
- `format_context()`
- `build_messages()`
- `inspect_prompt()`
- `create_generation_client()`
- `RagService.ask()`
- `OpenAICompatibleLLMClient.generate()`

这一遍只回答一个问题：

```text
一个 question 进入第六章以后，到底按什么顺序变成可控、可追溯、可拒答的 answer + sources？
```

### 3. 第三遍再看脚本和 tests

最后再看：

- `01_inspect_prompt.py`
- `02_query_demo.py`
- `03_refusal_demo.py`
- `04_real_llm_demo.py`
- `05_lcel_rag_chain.py`
- `tests/test_generation.py`

这样读会比一开始顺着扫更容易建立结构感。

---

## 建议学习顺序

### 第 1 步：先看候选如何进入 Prompt

```bash
python 01_inspect_prompt.py
python 01_inspect_prompt.py "火星首都是什么？"
python 01_inspect_prompt.py "退款规则是什么？" --top-k 5 --min-context-score 0.35 --max-chunks 2
```

重点观察：

- `retrieved_results / accepted_results / prompt_results` 的差异
- 哪些 chunk 被 `min_context_score` 挡掉
- `max_chunks` 怎样进一步裁剪 Prompt 上下文
- Prompt Preview 里是否已经带有 `[S1] / [S2]`

### 第 2 步：再跑 mock 闭环

```bash
python 02_query_demo.py
python 02_query_demo.py "为什么回答里要带来源标签？"
```

重点观察：

- Answer 里是否出现 `[S1]`
- `sources` 是否只返回实际使用到的来源
- `prompt_results` 是否比 `retrieved_results` 更少

### 第 3 步：专门看 refusal

```bash
python 03_refusal_demo.py
```

重点观察：

- 可回答问题和应拒答问题是否被明显分开
- `火星首都是什么？` 是否在生成前就停止
- 拒答时是否没有多余 `sources`

### 第 4 步：接真实 LLM，但不破坏主线

```bash
python 04_real_llm_demo.py
python 04_real_llm_demo.py --backend chroma --strategy mmr --provider openai
python 04_real_llm_demo.py "为什么 metadata 很重要？" --filename metadata_rules.md
```

重点观察：

- 没有真实环境时，为什么仍然能看到 provider 信息和 fallback 原因
- 第五章检索策略变化，怎样影响第六章最终答案和来源
- 真实路径里 `request_preview / response_preview` 为什么重要

### 第 5 步：最后看 LCEL

```bash
python 05_lcel_rag_chain.py
python 05_lcel_rag_chain.py --backend chroma --strategy threshold --threshold 0.80
```

重点观察：

- Prompt Preview 是否仍然是你前面已经理解过的那套 Prompt
- LCEL 版本和手写版本的上下文、答案边界是否一致
- LCEL 是否只是换了表达方式，而没有改变主线语义

### 第 6 步：最后看测试

```bash
python -m unittest discover -s tests
```

测试当前锁定的不是“脚本能跑”，而是：

1. 第六章 demo retriever 继续复用第五章富 metadata 契约
2. `format_context()` 会显式带上标签、文件名和分数
3. `build_messages()` 会保留系统 Prompt、上下文和问题
4. 无可用上下文时 `RagService` 会直接拒答
5. `RagService` 返回的 `sources` 会和答案标签对齐
6. 当 `top_k > max_chunks` 时，`sources` 仍只跟 `prompt_results` 对齐
7. provider 未就绪时 `create_generation_client()` 会回退到 mock
8. `Chapter5StrategyRetriever` 会直接复用第五章运行时路径

---

## 第六章最小回归集

第六章当前最值得反复观察的几条 case：

1. `退款规则是什么？`
   应能返回带 `[S1]` 的简洁答案，并带出对应来源
2. `为什么回答里要带来源标签？`
   `sources` 应该和答案中的标签对齐，而不是把所有候选全返回
3. `火星首都是什么？`
   应在生成前直接拒答
4. `top_k > max_chunks`
   `sources` 仍应只跟 `prompt_results` 对齐
5. mock fallback
   没有真实环境时仍应保留 provider、error 和 request preview 等可观察信息

---

## 本章边界

- 不展开完整多平台 provider 教学
- 不实现流式服务端输出
- 不展开完整线上服务工程
- 不进入复杂 Agent、多工具路由和多轮状态管理
- 不做复杂答案后处理或 citation post-processing

第六章当前真正要立住的是：

> 同一批 `RetrievalResult[]` 在应用层怎样收缩成可回答、可拒答、可追溯的 `answer + sources`。

---

## 学完这一章后你应该能回答

- 为什么第五章的 `RetrievalResult[]` 还不能直接等于模型输入
- 为什么第六章必须显式增加 context selection
- 为什么 context formatter 是生成链路里的独立职责
- 为什么真实 LLM 接入只应该抽取最小配置层，而不是把 provider 判断散落到业务代码
- 为什么最小结果应该是 `answer + sources`
- 为什么“我不知道”必须被当成正确输出之一
- 为什么 LCEL 只是当前链路的标准表达，而不是另一套平行体系

---

## 下一章

下一章开始评估这一条问答链路到底表现得怎么样。

也就是说：

> 第六章解决的是“把检索结果稳定接成可回答链路”，第七章才开始判断“这条链路到底有没有变好”。
