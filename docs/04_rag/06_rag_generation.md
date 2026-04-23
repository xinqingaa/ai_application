# 06. RAG 生成

> 本章目标：把第五章稳定的 `RetrievalResult[]` 真正接成一个最小可运行的问答闭环，掌握 `retriever candidates -> context selection -> context formatter -> RAG Prompt -> answer + sources` 这条固定生成路径。

---

## 1. 概述

### 学习目标

- 理解为什么第六章真正新增的是受控生成链路，而不是“再接一个模型”
- 理解为什么第六章的输入应该是第五章产出的稳定 `RetrievalResult[]`
- 理解为什么生成前还要再做一次 context selection，而不是把全部召回结果直接塞进 Prompt
- 掌握 `answer + sources` 为什么是 RAG 系统的最小返回结构
- 理解为什么“我不知道”必须在生成链路里被显式设计
- 能说明第六章为什么只抽取 `02_llm/02_multi_provider` 里的最小真实调用能力，而不重讲整套多平台抽象
- 能区分“手写生成链路”和 `LCEL RAG Chain` 之间的一一映射关系
- 能独立运行第六章脚本，并区分问题究竟出在检索候选、上下文筛选还是生成组织

### 预计学习时间

- 输入输出契约与章节连续性：30-40 分钟
- context selection 与 formatter：40-60 分钟
- Prompt、引用与拒答边界：40-60 分钟
- 真实 LLM 接入与 fallback：30-40 分钟
- LCEL 最小链路：30-40 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 第六章先解决什么 |
|------|------------------|
| 检索已经有结果 | 哪些结果真的值得进入 Prompt |
| 结果太多太杂 | 为什么需要 context selection 和 `max_chunks` |
| 回答需要可追溯 | 为什么返回值必须是 `answer + sources` |
| 无答案问题 | 为什么拒答应该发生在生成前 |
| 真实模型接入 | 怎样不破坏教学主线地接入真实 LLM |
| 调参定位 | 如何拆开“检索候选问题”和“生成组织问题” |

### 学习前提

- 建议先完成第五章，已经理解 `RetrievalResult[]` 的稳定契约
- 建议已经理解第四章的 `SourceChunk / metadata / filename / chunk_index`
- 建议已经理解第五章的 `top_k / threshold / mmr / filename_filter`
- 如果你已经跑过第二章的 OpenAI-compatible 多平台调用，这一章读起来会更快

这一章不再重复讲：

- 如何切块
- 如何生成向量
- 如何做底层检索
- 如何设计完整多平台 provider 抽象
- 如何做复杂服务端工程

第六章只关注生成层 specific 的问题。

### 本章与前后章节的关系

第五章已经解决：

1. 如何把底层查询收束成稳定 Retriever
2. 如何让 Retriever 输出统一的 `RetrievalResult[]`
3. 如何比较 `similarity / threshold / MMR / filename filter`
4. 检索失败时应该先从哪里排查

第六章接着解决：

1. 如何从 `RetrievalResult[]` 里挑出适合进入 Prompt 的上下文
2. 如何把这些结果格式化成模型可读上下文
3. 如何通过 RAG Prompt 固定回答边界
4. 如何返回真正可追溯的 `answer + sources`
5. 如何把第二章已经讲过的真实模型调用能力，最小化地接进当前 RAG 闭环
6. 如何用 LCEL 改写同一条链路，而不是重做一套平行实现

第七章会继续建立在这里之上：

1. 对问答链路建立最小评估闭环
2. 判断一次改动到底改善了检索、生成还是两者都没有改善

### 第六章与前几章的连续性

第六章不应该重新定义一套新的 `SourceChunk / RetrievalResult / Retriever` 数据模型。

当前代码改成了下面这条连续路径：

```text
chapter 4 SourceChunk / metadata / store
-> chapter 5 SimpleRetriever / RetrievalResult[]
-> chapter 6 context selection / prompt / answer + sources
```

也就是说，第六章真正新增的是：

- `min_context_score`
- `max_chunks`
- `format_context()`
- `build_messages()`
- `RagService.ask()`

而不是再次重写：

- `SourceChunk`
- `RetrievalResult`
- 向量 store
- 检索基础接口

真实模型接入也有同样的边界：

> 第六章不会把 `02_llm/02_multi_provider` 整章复制进来，而是只抽取 `provider config -> OpenAI-compatible client -> normalized response -> mock fallback` 这条最小接缝。

### 本章代码入口

本章对应的代码目录是：

- [README.md](../../source/04_rag/06_rag_generation/README.md)
- [requirements.txt](../../source/04_rag/06_rag_generation/requirements.txt)
- [llm_utils.py](../../source/04_rag/06_rag_generation/llm_utils.py)
- [generation_basics.py](../../source/04_rag/06_rag_generation/generation_basics.py)
- [01_inspect_prompt.py](../../source/04_rag/06_rag_generation/01_inspect_prompt.py)
- [02_query_demo.py](../../source/04_rag/06_rag_generation/02_query_demo.py)
- [03_refusal_demo.py](../../source/04_rag/06_rag_generation/03_refusal_demo.py)
- [04_real_llm_demo.py](../../source/04_rag/06_rag_generation/04_real_llm_demo.py)
- [05_lcel_rag_chain.py](../../source/04_rag/06_rag_generation/05_lcel_rag_chain.py)
- [tests/test_generation.py](../../source/04_rag/06_rag_generation/tests/test_generation.py)

### 本章边界

本章重点解决：

1. `RetrievalResult[]` 的输入契约
2. context selection
3. context formatter
4. RAG Prompt
5. `answer + sources`
6. 无答案处理
7. 真实 LLM 的最小接入
8. LCEL 对当前链路的标准表达

本章不要求：

- 展开完整多平台 provider 教学
- 实现流式服务端输出
- 展开完整线上服务工程
- 引入多轮状态管理、上传与索引 API
- 进入复杂 Agent 或多工具路由
- 做复杂答案后处理或 citation post-processing

这一章的核心目标不是“把模型接起来”，而是把下面这条生成主线固定住：

> 第六章解决的是“哪些检索结果值得进入回答，以及怎样把它们稳定接到真实模型”，不是“重新做一遍检索工程”。

---

## 2. 为什么第六章不是“接一个模型” 📌

### 2.1 很多初学者会误解第六章在做什么

很多人一看到“RAG 生成”，就会把注意力放在：

- 选哪个模型
- 怎么发 API 请求
- 模型回答得像不像人

这会把第六章学偏。

因为如果没有受控链路，你很快就会遇到这些问题：

- 召回结果全塞进 Prompt，噪声过高
- 模型回答了，但你不知道它依据了什么
- 无答案问题被硬答
- mock 路径、真实模型路径、LCEL 路径三套理解彼此脱节

所以第六章真正新增的不是“模型调用”本身，而是：

> 把检索结果收束成可回答、可追溯、可拒答、可切换实现方式的稳定生成链路。

### 2.2 第六章的运行时主链路

这一章最值得先建立手感的，是这条完整运行时链路：

```text
question
-> RetrievalResult[] candidates
-> context selection
-> prompt_results
-> format_context()
-> build_messages()
-> llm.generate()
-> answer text + labels
-> select_used_results()
-> answer + sources
```

如果你能把这条链路讲清楚，第六章的大部分内容就已经真正掌握了。

### 2.3 mock、真实 LLM、LCEL 不是三套平行系统

这一章很容易出现一个理解误区：

- `02_query_demo.py` 是 mock 路径
- `04_real_llm_demo.py` 是真实模型路径
- `05_lcel_rag_chain.py` 是 LCEL 路径

看起来像三套东西，但其实不是。

它们更准确的关系是：

1. mock 路径
   让你先把生成主线讲清楚
2. 真实 LLM 路径
   验证这条主线怎样接入真实模型
3. LCEL 路径
   把同一条主线换成标准链式表达

也就是说：

> 三条路径观察的是同一条生成主线，不是三套独立 RAG 系统。

### 2.4 第六章交付的是“稳定生成层”

如果第五章交付的是“稳定策略层”，那第六章交付的就是：

> 后续评估层和应用层都能消费的稳定生成接口。

因此这里的重点不是：

- 模型多不多
- Prompt 花不花
- 回答像不像真人

而是：

- 输入要稳定
- 上下文要受控
- 拒答要显式
- 来源要可追溯
- 真实调用要可降级

---

## 3. 本章的输入和输出到底是什么 📌

### 3.1 输入为什么是 `RetrievalResult[]`

第六章最重要的一步，是把注意力从“接一个模型”改成“固定一条受控生成链路”。

它的最小数据流应该长这样：

```text
question
-> RetrievalResult[] candidates
-> context selection
-> formatted context
-> RAG Prompt
-> answer + sources
```

这里最关键的是两端：

- 输入不是原始文档，而是第五章已经整理好的 `RetrievalResult[]`
- 输出不是一段随意文本，而是最小可追溯的 `answer + sources`

### 3.2 输入为什么不是“文档”

真正送进生成层的，不是整份 PDF，也不是原始文件内容，而是更小、更稳定的一组检索结果：

- chunk 文本
- 检索分数
- stable chunk 身份
- richer metadata

这说明生成层的前提是：

> 检索层已经把候选依据缩小到一批可以继续筛选和组织的结果。

所以第六章真正吃的是第五章的输出契约，不是重新做一次检索。

### 3.3 输出为什么不能只是“一段答案”

如果最终只返回一段文本，你很快会遇到三个问题：

- 用户无法核对依据
- 你无法判断答对是不是碰巧
- 第七章开始做评估时很难区分“答对了但引用错了”

所以第六章推荐的最小返回结构是：

```text
answer + sources
```

### 3.4 为什么 `sources` 不能只是“所有召回结果”

真正应该返回的 `sources`，至少要和下面两件事对齐：

1. 真正进入 Prompt 的上下文
2. 最终答案里实际使用的来源标签

如果 `sources` 只是把所有低质量候选都原样返回，你会失去引用链路的可解释性。

### 3.5 第六章最重要的三组结果

这一章要刻意区分三类结果：

1. `retrieved_results`
   Retriever 原始候选
2. `accepted_results`
   通过 `min_context_score` 的可用上下文
3. `prompt_results`
   真正进入 Prompt 的有限上下文

如果不把这三层拆开，你会很难定位问题到底发生在哪一步。

---

## 4. 为什么检索结果还要过一次 context selection 📌

### 4.1 Retriever 候选池不等于 Prompt 上下文

第五章解决的是：

- 从 store 里召回候选
- 返回稳定 `RetrievalResult[]`

第六章还要额外解决：

- 候选里哪些结果值得进 Prompt
- 候选过多时先裁掉谁
- 无答案时在哪里停下来

所以当前第六章的最小链路是：

```text
chapter 5 retriever candidates
-> chapter 6 min_context_score filter
-> chapter 6 max_chunks cap
-> formatted context
```

这一步的意义非常大，因为它把“检索能查到一些东西”和“这些东西真的值得成为回答依据”拆开了。

### 4.2 `min_context_score` 在解决什么问题

当前实现会对 Retriever 返回的候选再做一次问题相关性筛选。

它的职责不是替代第五章的 Retriever，而是：

- 在进入 Prompt 之前挡掉弱相关上下文
- 让“我不知道”可以在生成前发生
- 让第六章可以更清楚地演示 context selection 的存在价值

你可以把它理解成：

> 第五章负责“把候选找出来”，第六章负责“把候选收缩成可回答上下文”。

### 4.3 `max_chunks` 为什么不是小参数

就算已经有一批可接受结果，也不代表应该全部塞进 Prompt。

`max_chunks` 解决的是：

- 控制上下文长度
- 控制引用标签数量
- 保证 `sources` 和实际回答更容易对齐

它不是简单的 UI 参数，而是生成层的边界控制参数。

### 4.4 如果没有 context selection，会发生什么

如果没有这一步，很快会出现这些问题：

- 上下文被重复 chunk 挤满
- 明明有正确候选，但被大量弱相关内容稀释
- 用户问无答案问题时，模型仍会被喂入一些“沾边内容”
- `sources` 很难和真正回答依据保持一致

所以 context selection 不是“锦上添花”，而是：

> 生成层把检索候选转成回答依据的关键闸门。

---

## 5. context formatter 到底在做什么 📌

### 5.1 formatter 不是“拼字符串”

很多初学者会把 formatter 理解成“把字符串拼起来”，但这不够。

一个最小可用的 context formatter 至少要负责：

1. 给每个 prompt chunk 一个稳定标签，例如 `[S1]`
2. 显式保留 `filename / chunk_index`
3. 让调试时能看到 `retrieval_score / context_score`
4. 控制每段内容长度
5. 让最终答案和 `sources` 能对得上

当前代码里的 [format_context()](../../source/04_rag/06_rag_generation/generation_basics.py) 正在做这件事。

### 5.2 为什么来源标签必须在 formatter 阶段立住

如果来源标签不是在 formatter 阶段明确写入，你后面会很难保证：

- Prompt 里的上下文块有稳定身份
- 模型输出的 `[S1] / [S2]` 指向明确
- `sources` 能和答案标签对齐

所以 formatter 不只是展示层，它实际上在补：

> 生成前的可追溯结构。

### 5.3 为什么要显式保留 metadata

当前 formatter 不只保留 chunk 文本，还会显式保留：

- `filename`
- `chunk_index`
- `retrieval_score`
- `context_score`

这样做不是为了让 Prompt 更“花”，而是为了让：

- 调试更容易
- 引用更明确
- Prompt Preview 更可解释

---

## 6. RAG Prompt、引用和拒答边界 📌

### 6.1 RAG Prompt 和普通聊天 Prompt 的区别

普通聊天 Prompt 常见的重点是：

- 角色
- 任务
- 风格

RAG Prompt 还必须额外固定三件事：

1. 回答依据从哪里来
2. 如果上下文不够该怎么办
3. 如果用了上下文，答案要怎么标来源

当前本章的 [RAG_SYSTEM_PROMPT](../../source/04_rag/06_rag_generation/generation_basics.py) 和 [RAG_USER_TEMPLATE](../../source/04_rag/06_rag_generation/generation_basics.py) 固定了三个边界：

- 只能依据当前上下文回答
- 没有依据时直接说“我不知道”
- 使用了上下文就要带 `[S1]` 这样的来源标签

从这里开始，Prompt 的任务不再只是“让模型说得更像人”，而是“让模型在边界里说话”。

### 6.2 为什么“我不知道”必须成为主线能力

很多初学者会把拒答看成异常分支，但对 RAG 来说，它其实是主线能力。

因为真实问题里一定会出现：

- 没有召回到真正相关的依据
- 候选结果虽然有分数，但仍然不值得进 Prompt
- 问题超出知识库范围

所以当前更稳的顺序应该是：

```text
retrieved results
-> context selection
-> no acceptable context
-> 直接返回“我不知道”
```

这比“先让模型回答，再希望 Prompt 限制住它”更稳。

### 6.3 为什么拒答应该发生在生成前

如果系统已经知道：

- 没有可用上下文

却仍然调用模型，那你其实是在把一个本可确定的问题推给 LLM 去碰运气。

这会让系统：

- 更贵
- 更慢
- 更容易幻觉

所以第六章当前更稳的做法是：

> 先用结构化条件判断是否有资格进入生成，再决定是否调用 LLM。

### 6.4 `sources` 对齐为什么是主线能力

RAG 里很多人会把来源显示看成 UI 附件，但在这门课的语境里，它是主线能力。

因为 `sources` 对齐同时解决三件事：

1. 用户能核对依据
2. 你能定位答案到底用了哪些上下文
3. 第七章开始时，评估不只是“答没答对”，还能继续判断“引用链是否正确”

也就是说：

> 没有 `sources` 对齐，RAG 生成层就还没有真正完成闭环。

---

## 7. 真实 LLM 接入为什么只抽最小 client 接缝 📌

### 7.1 第六章为什么不重讲第二章

真实模型接入当然重要，但如果第六章重新展开：

- provider registry
- 认证方式
- 各家 API 差异
- 多平台抽象设计

主线会立刻跑偏。

所以这里故意只抽最小接缝：

- provider config
- normalized generation result
- OpenAI-compatible client
- mock fallback

### 7.2 `llm_utils.py` 真正在补什么

这个文件不是第二章 `provider_utils.py` 的完整拷贝，而是专门为第六章抽出来的最小真实调用层。

它只保留四件事：

- provider config
- normalized generation result
- OpenAI-compatible client
- 环境不完整时的 mock fallback 前置判断

这里最重要的边界是：

> 第六章要学的是“怎么把真实模型稳定接进 RAG 主线”，不是在这一章重新做一套多平台接入课程。

### 7.3 为什么要保留 mock fallback

如果环境变量不完整、SDK 没装好、调用异常就直接让整章跑不起来，会出现两个问题：

- 读者学不到第六章主线
- 你无法区分“生成链路没讲清”还是“环境没配好”

所以 mock fallback 的意义不是“偷懒”，而是：

> 在真实环境不完整时，依然保留第六章最重要的可观察行为。

### 7.4 `GenerationResult` 为什么重要

真实模型接入后，如果只拿一段文本回来，你很快会丢失很多关键上下文。

`GenerationResult` 当前保留的最关键字段包括：

- `provider`
- `model`
- `content`
- `usage`
- `finish_reason`
- `request_preview`
- `raw_response_preview`
- `mocked`
- `error`

这让第六章的真实调用不只是“有返回”，而是可诊断、可回退、可解释。

---

## 8. LCEL 在这一章到底是什么 📌

### 8.1 LCEL 不是另一套 RAG

第六章里的 LCEL 很容易被误解成“额外新知识点”，甚至像另一章。

但这里最重要的理解是：

> LCEL 不是另一套 RAG，而是把你已经学过的同一条链路改写成标准可组合表达。

当前对应关系大致是：

```text
手写链路:
retriever -> inspect/select -> build_messages -> llm.generate -> answer

LCEL 链路:
retriever -> context -> ChatPromptTemplate -> LLMClient -> StrOutputParser
```

### 8.2 为什么第六章现在就要补 LCEL

如果现在不补 LCEL，后面你会很容易把“手写脚本”和“框架链路”理解成两套平行系统。

第六章现在补 LCEL，目的不是增加复杂度，而是帮你建立这个映射：

- 手写链路解决的是运行时逻辑
- LCEL 解决的是标准组合表达

### 8.3 第六章里 LCEL 的边界

当前 LCEL demo 只做这些事：

- 复用同一套检索器
- 复用同一套 Prompt 边界
- 复用同一套上下文选择结果
- 把调用过程写成标准链式组合

它不在这一章做：

- 完整服务封装
- 多步 agent chain
- 更复杂的 runnable graph

---

## 9. 第六章代码是怎么落地的 📌

### 9.1 `generation_basics.py`

这个文件承载了本章全部核心对象：

- `AnswerResult`
- `PromptInspection`
- `GenerationDemoRetriever`
- `Chapter5StrategyRetriever`
- `MockLLMClient`
- `ResilientGenerationClient`
- `RagService`

同时也放了本章所有核心动作：

- `build_generation_demo_store()`
- `filter_retrieval_results()`
- `select_prompt_results()`
- `select_used_results()`
- `format_context()`
- `build_messages()`
- `inspect_prompt()`
- `create_generation_client()`

这里最重要的变化是：

> 第六章不再自己重写 `SourceChunk / RetrievalResult`，而是直接复用第五章链路和第四章 metadata；真实模型调用也不再在业务里散落判断，而是被收束成最小 client 接缝。

### 9.2 `AnswerResult` 在保什么

`AnswerResult` 看起来很简单，但它其实固定了第六章的最小输出契约：

- `answer`
- `sources`

这让生成层的交付物从“一段话”升级成“可追溯回答”。

### 9.3 `PromptInspection` 在保什么

`PromptInspection` 的价值很大，因为它把第六章最容易混掉的几层状态拆开了：

- `retrieved_results`
- `accepted_results`
- `prompt_results`
- `context_scores`
- `context`
- `messages`
- `prompt_preview`

有了它，你才真正能看清：

- 候选是什么
- 被筛掉了什么
- 真正喂给模型的是什么

### 9.4 `GenerationDemoRetriever` 和 `Chapter5StrategyRetriever`

第六章当前保留两条 retriever 路径：

1. `GenerationDemoRetriever`
   用于第六章自己的教学语料和 mock 主线
2. `Chapter5StrategyRetriever`
   直接复用第五章的 `backend / strategy / threshold / mmr / filename_filter`

这样设计的意义是：

- 既能保留第六章最小教学闭环
- 又能让真实生成链路直接吃第五章运行时能力

### 9.5 `RagService.ask()` 真正在做什么

`RagService.ask()` 是第六章最值得先看清的主流程方法。

它做的事情大致是：

```text
retrieve()
-> filter_retrieval_results()
-> select_prompt_results()
-> build_messages()
-> llm.generate()
-> extract_source_labels()
-> select_used_results()
-> AnswerResult
```

如果没有可用上下文，它会直接返回拒答，而不是继续调用模型。

### 9.6 `llm_utils.py`

这个文件是第六章最小真实调用层。

它当前最重要的对象包括：

- `GenerationProviderProfile`
- `GenerationProviderConfig`
- `GenerationUsage`
- `GenerationResult`
- `OpenAICompatibleLLMClient`

它解决的是：

- 环境变量怎样收束成统一配置
- 不同 provider 怎样统一到 OpenAI-compatible 调用方式
- 真实调用结果怎样变成可诊断的标准结构

### 9.7 脚本各自的职责

各脚本不是随机分散的，它们分别锁定不同观察点：

- [01_inspect_prompt.py](../../source/04_rag/06_rag_generation/01_inspect_prompt.py)
  看候选怎样变成 Prompt
- [02_query_demo.py](../../source/04_rag/06_rag_generation/02_query_demo.py)
  跑最小 mock 闭环
- [03_refusal_demo.py](../../source/04_rag/06_rag_generation/03_refusal_demo.py)
  对比“该答”和“该拒答”
- [04_real_llm_demo.py](../../source/04_rag/06_rag_generation/04_real_llm_demo.py)
  把第五章真实检索路径接到真实 LLM 或 mock fallback
- [05_lcel_rag_chain.py](../../source/04_rag/06_rag_generation/05_lcel_rag_chain.py)
  用 LCEL 重写同一条生成链路

---

## 10. 生成治理与最小回归锚点 📌

### 10.1 为什么第六章就要开始有治理视角

如果这一章只讲“模型能答出来”，后面很快会失控：

- 今天换了 Prompt，答案变好了还是碰巧了？
- 今天调了 `min_context_score`，是更稳了还是只是更爱拒答了？
- 今天 provider 变了，是模型强了，还是 sources 对齐坏了？

所以第六章就要开始建立最小治理视角。

### 10.2 第六章最重要的治理锚点是什么

这一章当前最重要的治理锚点有四类：

1. 输入锚点
   `RetrievalResult[]` 必须稳定
2. 上下文锚点
   `accepted_results / prompt_results` 必须可观察
3. 输出锚点
   `answer + sources` 必须对齐
4. 拒答锚点
   无依据时必须稳定拒答

### 10.3 第六章最小回归观察点

当前最值得反复观察的几条 case：

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

### 10.4 第六章最值得刻意观察的失败类型

这一章最值得你刻意观察的失败类型包括：

- 检索候选明明对，但 context selection 挡掉了正确块
- Prompt 里上下文对了，但答案没按来源标签输出
- 答案看起来对，但 `sources` 没和标签对齐
- 无答案问题仍然触发真实生成
- 真实环境不完整时，fallback 把教学主线打断

### 10.5 这一章最关键的三类错误定位

你应该刻意区分三类错误：

1. 检索候选错误
   第五章根本没把对的候选找出来
2. 上下文筛选错误
   候选有了，但第六章没挑对
3. 生成组织错误
   上下文已经对了，但 Prompt、引用或回答组织方式有问题

这就是第六章最大的学习价值之一。

---

## 11. 如何阅读第六章代码

### 11.1 第一遍只看对象

先打开 [generation_basics.py](../../source/04_rag/06_rag_generation/generation_basics.py)，只看这些对象：

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

### 11.2 第二遍只看主流程

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

### 11.3 第三遍再看脚本和 tests

最后再看：

- `01_inspect_prompt.py`
- `02_query_demo.py`
- `03_refusal_demo.py`
- `04_real_llm_demo.py`
- `05_lcel_rag_chain.py`
- `tests/test_generation.py`

这样读会比一开始从头到尾顺着扫更容易建立结构感。

---

## 12. 第六章实践：建议运行顺序

### 12.1 安装依赖

在 `source/04_rag/06_rag_generation/` 目录下运行：

```bash
python -m pip install -r requirements.txt
```

### 12.2 先看候选如何进入 Prompt

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

### 12.3 再跑 mock 闭环

```bash
python 02_query_demo.py
python 02_query_demo.py "为什么回答里要带来源标签？"
```

重点观察：

- Answer 里是否出现 `[S1]`
- `sources` 是否只返回实际使用到的来源
- `prompt_results` 是否比 `retrieved_results` 更少

### 12.4 专门看拒答

```bash
python 03_refusal_demo.py
```

重点观察：

- 可回答问题和应拒答问题是否被明显分开
- `火星首都是什么？` 是否在生成前就停止
- 拒答时是否没有多余 `sources`

### 12.5 接真实 LLM，但不破坏主线

```bash
python 04_real_llm_demo.py
python 04_real_llm_demo.py --backend chroma --strategy mmr --provider openai
python 04_real_llm_demo.py "为什么 metadata 很重要？" --filename metadata_rules.md
```

重点观察：

- 没有真实环境时，为什么仍然能看到 provider 信息和 fallback 原因
- 第五章检索策略变化，怎样影响第六章最终答案和来源
- 真实路径里 `request_preview / response_preview` 为什么重要

### 12.6 最后看 LCEL

```bash
python 05_lcel_rag_chain.py
python 05_lcel_rag_chain.py --backend chroma --strategy threshold --threshold 0.80
```

重点观察：

- Prompt Preview 是否仍然是你前面已经理解过的那套 Prompt
- LCEL 版本和手写版本的上下文、答案边界是否一致
- LCEL 是否只是换了表达方式，而没有改变主线语义

### 12.7 测试在锁定什么

```bash
python -m unittest discover -s tests
```

这组测试当前锁定的不是“脚本能跑”，而是：

1. 第六章 demo retriever 继续复用第五章富 metadata 契约
2. `format_context()` 会显式带上标签、文件名和分数
3. `build_messages()` 会保留系统 Prompt、上下文和问题
4. 无可用上下文时 `RagService` 会直接拒答
5. `RagService` 返回的 `sources` 会和答案标签对齐
6. 当 `top_k > max_chunks` 时，`sources` 仍只跟 `prompt_results` 对齐
7. provider 未就绪时 `create_generation_client()` 会回退到 mock
8. `Chapter5StrategyRetriever` 会直接复用第五章运行时路径

### 12.8 建议你主动改的地方

如果你想真正吃透第六章，建议你主动做这些小改动：

1. 把 `min_context_score` 分别改成 `0.2 / 0.35 / 0.5`，看系统何时更爱拒答
2. 把 `max_chunks` 分别改成 `1 / 2 / 3`，观察 Prompt 和 `sources` 怎么变化
3. 把第五章的 `strategy` 改成 `similarity / threshold / mmr`，看答案和来源怎么变化
4. 在真实 demo 里切换 `provider`，观察 fallback 和真实调用信息有什么差别
5. 主动新增一个测试问题，判断它属于检索错误、筛选错误还是生成组织错误

---

## 13. 本章学完后你应该能回答

- 为什么第五章的 `RetrievalResult[]` 还不能直接等于模型输入
- 为什么第六章必须显式增加 context selection
- 为什么 context formatter 是生成链路里的独立职责
- 为什么真实 LLM 接入只应该抽取最小配置层，而不是把 provider 判断散落到业务代码
- 为什么最小结果应该是 `answer + sources`
- 为什么“我不知道”必须被当成正确输出之一
- 为什么 LCEL 只是当前链路的标准表达，而不是另一套平行体系

---

## 14. 下一章

第七章开始，你会进一步评估这一条问答链路到底表现得怎么样。

也就是说：

> 第六章解决的是“把检索结果稳定接成可回答链路”，第七章才开始判断“这条链路到底有没有变好”。
