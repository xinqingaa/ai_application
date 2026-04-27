# 05. 检索策略

> 本章目标：把第四章的“能查”推进到第五章的“查得稳、查得可控、查得可评估”。你会先建立 Retriever 策略层的完整主线和运行时契约，再掌握 `similarity / threshold / mmr` 三种基础策略，随后引入坏案例回归、混合检索、两阶段 Rerank，最后用一个最小 `SmartRetrievalEngine` 把这些能力收束成统一接口。

---

## 1. 概述

### 学习目标

- 理解为什么第五章新增的是 Retriever 策略层，而不是重写第四章存储层
- 掌握 `similarity / threshold / mmr` 三种基础检索策略的行为差异
- 理解 `top_k / candidate_k(fetch_k) / score_threshold / filename_filter / mmr_lambda` 的职责
- 学会用坏案例和固定评估集验证检索策略，而不是只看主观印象
- 理解混合检索（BM25 + 向量）和两阶段检索（Rerank）的价值与边界
- 了解 Query 变换、上下文压缩和高级 Retriever 的适用场景
- 能跑通本章代码，并解释为什么综合案例要把多种策略统一到一个检索引擎里

### 预计学习时间

- 检索层主线与参数控制：40-60 分钟
- 基础 Retriever 与坏案例回归：40-60 分钟
- Hybrid / Rerank / 统一引擎：40-60 分钟
- 评估、测试与回归锚点：30-40 分钟

### 本章在 AI 应用中的重要性

| 场景 | 第五章先解决什么 |
|------|----------------|
| 检索稳定性 | 同一个问题怎样避免结果过少、过噪或过重复 |
| 检索可控性 | `top_k / threshold / filter / mmr` 怎样变成显式参数 |
| 检索优化 | 什么时候该用关键词、语义、多样性或两阶段精排 |
| 检索评估 | 怎样把“看起来不错”变成坏案例回归和固定指标 |
| 应用接入 | 多种检索实验怎样收束成统一可复用接口 |

### 学习前提

- 建议先完成第四章，已经理解 Vector Store 的最小契约
- 建议已经理解 `EmbeddedChunk / RetrievalResult / EmbeddingSpace`
- 建议知道 query 和 store 必须处于同一 embedding space
- 如果你已经跑过第四章的 `json / chroma / langchain` 路径，这一章会更顺

这一章不再重复讲：

- 文本怎样切块
- 向量怎样生成
- `embed_query / embed_documents` 的基础语义
- 持久化存储、文档替换、文档删除的底层实现

第五章只关注检索层特有的问题。

### 本章与前后章节的关系

第四章已经解决：

1. 文本怎样变成向量
2. 向量怎样真正进入 JSON / Chroma 存储
3. query 和 store 为什么必须保持同一 embedding space
4. 最小相似度查询怎样返回 `RetrievalResult[]`

第五章继续解决：

1. 如何把底层查询收束成 Retriever
2. 如何控制召回数量、噪声和多样性
3. 如何引入关键词检索、两阶段精排和固定评估
4. 如何把多种检索策略收束成统一应用接口

第六章才继续解决：

1. 把 Retriever 返回结果拼进 Prompt
2. 形成真正的 RAG Chain
3. 让 LLM 基于检索上下文生成答案

### 本章代码入口

- [README.md](../../source/04_rag/05_retrieval_strategies/README.md)
- [requirements.txt](../../source/04_rag/05_retrieval_strategies/requirements.txt)
- [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- [chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)
- [retrieval_metrics.py](../../source/04_rag/05_retrieval_strategies/retrieval_metrics.py)
- [smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/smart_retrieval_engine.py)
- [01_compare_retrievers.py](../../source/04_rag/05_retrieval_strategies/01_compare_retrievers.py)
- [02_review_bad_cases.py](../../source/04_rag/05_retrieval_strategies/02_review_bad_cases.py)
- [03_query_demo.py](../../source/04_rag/05_retrieval_strategies/03_query_demo.py)
- [04_hybrid_retrieval.py](../../source/04_rag/05_retrieval_strategies/04_hybrid_retrieval.py)
- [05_rerank_demo.py](../../source/04_rag/05_retrieval_strategies/05_rerank_demo.py)
- [06_smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/06_smart_retrieval_engine.py)
- [evals/retrieval_bad_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json)
- [evals/retrieval_eval_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_eval_cases.json)
- [tests/test_retrievers.py](../../source/04_rag/05_retrieval_strategies/tests/test_retrievers.py)
- [tests/test_chroma_retrievers.py](../../source/04_rag/05_retrieval_strategies/tests/test_chroma_retrievers.py)
- [tests/test_retrieval_metrics.py](../../source/04_rag/05_retrieval_strategies/tests/test_retrieval_metrics.py)
- [tests/test_smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/tests/test_smart_retrieval_engine.py)

### 本章边界

本章重点解决：

1. 基础检索参数和召回行为
2. MMR 多样性控制
3. `filename_filter` 范围约束
4. 坏案例回归
5. 固定评估指标：`Recall@K / MRR / Hit Rate`
6. 混合检索：BM25 + 向量
7. 两阶段检索：粗筛 + Rerank
8. 一个最小统一检索引擎

本章做概念认知但不做主线实现：

- Multi-Query
- HyDE
- Query Decomposition
- Step-back Prompting
- 上下文压缩
- Self-Query / Parent Document / Multi-Vector Retriever

本章不展开：

- Prompt 设计
- 最终答案生成
- 多轮 Agentic RAG
- 真实 cross-encoder reranker 落地工程
- 复杂 metadata DSL

这里故意只保留：

- 一个最小 JSON Retriever 原理层
- 一个真实 `ChromaRetriever`
- 一个最小 BM25 scorer
- 一个 toy reranker
- 一个教学最小 `SmartRetrievalEngine`

目的不是追求“检索技巧列得最多”，而是先把第五章检索层主线讲清楚。

### 本章学习地图

建议按下面这条主线阅读本章，而不是一开始就陷入某个参数、某个检索技巧或某个框架名：

```text
先看 Retriever 策略层完整流程
-> 再看 Store 和 Retriever 的边界
-> 再看运行时对象和策略契约
-> 再看 similarity / threshold / mmr 三种基础策略
-> 再看评估指标和坏案例回归
-> 再看 hybrid / rerank / 高级 Retriever
-> 最后看 SmartRetrievalEngine 如何收束统一入口
```

本章后面的失败案例、治理锚点和实践命令，更适合在你已经理解主线以后回头复盘。

---

## 2. 检索策略层的完整流程 📌

第五章可以先不要从“哪个检索技巧更高级”开始，而是先建立一条完整主线。

这一章做的是把第四章的 `store.similarity_search()`，加工成应用层可以稳定使用、稳定比较、稳定调参的 Retriever 策略层：

```text
question
-> EmbeddingProvider.embed_query()
-> Retriever 从 store 取回 candidate_k 个候选
-> similarity / threshold / mmr 选择最终 top_k
-> optional hybrid
-> optional rerank
-> RetrievalResult[]
-> bad-case regression / fixed eval set
-> SmartRetrievalEngine.retrieve() / evaluate()
```

这条链路里每一步都有明确输入和输出：

| 阶段 | 输入 | 输出 | 对应内容 |
|------|------|------|----------|
| 问题进入 | `question` | query vector | `EmbeddingProvider.embed_query()` |
| 候选召回 | query vector + store | `SearchHit[]` / candidate pool | `SimpleRetriever` / `ChromaRetriever` |
| 基础策略选择 | candidate pool + config | `RetrievalResult[]` | `similarity / threshold / mmr` |
| 范围约束 | `filename_filter` | 更窄的候选范围 | metadata filter |
| 混合检索 | vector score + BM25 score | fused ranking | `SimpleBM25Scorer` / hybrid |
| 两阶段精排 | first-stage candidates | reranked results | `SimpleCrossReranker` |
| 评估回归 | results + expected ids | metrics / bad-case result | `Recall@K / MRR / Hit Rate` |
| 统一入口 | strategy config | retrieve / evaluate | `SmartRetrievalEngine` |

初学时可以先记住一个判断标准：

> 第四章解决“能不能稳定地查”，第五章解决“怎样可控、可评估地查”。

后面的章节会按这条主线展开：先讲 Store 和 Retriever 的边界，再讲运行时对象和策略契约，然后进入基础策略、评估回归、Hybrid、Rerank 和统一引擎。

---

## 3. 主流程拆解：从 Store 查询到 Retriever 策略 📌

### 3.1 第四章交付的内容

第四章已经让系统拥有：

- 可持久化的向量存储
- 最小相似度查询能力
- `document_id` 级更新和删除能力
- metadata 的最小过滤路径
- 稳定的 `RetrievalResult[]` 输出

这意味着第四章已经解决了“能不能查”和“查出来的结果是否有稳定身份”。

### 3.2 第五章新增的标准接口

第五章真正新增的不是“再查一次向量”，而是：

```text
question
-> retriever.retrieve(question, strategy)
-> candidate pool
-> threshold / mmr / filter / hybrid / rerank
-> RetrievalResult[]
```

也就是说，第五章新增的是：

- 检索策略层
- 召回控制参数
- 多样性控制
- 混合检索与两阶段精排
- 检索评估与回归
- 统一应用入口

### 3.3 只有相似度查询还不够

如果系统只有“直接按相似度取 Top-K”，很快会遇到这些问题：

- 相似结果高度重复，浪费上下文窗口
- 无答案问题也会被硬塞进若干“勉强相关”的 chunk
- 精确术语、编号、流程类问题不一定靠纯向量最稳
- 一个 demo 脚本和另一个 demo 脚本之间没有统一接口
- 你无法稳定比较“这次调整到底变好了还是变坏了”

所以第五章不是“第四章再跑一遍”，而是在定义：

> 应用层如何在同一个底层 store 之上，把检索做得更稳、更可控、更可评估。

### 3.4 第五章的运行时主链路

这一章最值得先建立手感的，不是某个高级名词，而是一条完整运行时链路：

```text
question
-> EmbeddingProvider.embed_query()
-> store / retriever 取回 candidate_k 个候选
-> similarity / threshold / mmr 选出 top_k
-> optional hybrid / optional rerank
-> RetrievalResult[]
-> bad-case regression / fixed eval set
-> SmartRetrievalEngine.retrieve() / evaluate()
```

如果你能把这条链路讲清楚，第五章的大部分内容就已经真正掌握了。

### 3.5 第五章交付的是稳定策略层

很多资料会把这一章讲成：

- 再加几个检索技巧
- 看看效果
- 结束

这种讲法不够。

更准确的说法是：

> 第五章在定义后续 Prompt 层和生成层要消费的稳定 Retriever 策略接口。

所以这里的重点不是“又多会了几个名词”，而是：

- 参数要显式
- 行为要可重复
- 失败要可观察
- 调优要可评估
- 多种策略要能收束成统一入口

### 3.6 检索层的职责边界

检索层负责的是：

- 接收用户问题
- 设定召回策略
- 控制结果数量、冗余和噪声
- 在需要时引入关键词和精排
- 把结果整理成后续链路可直接消费的接口

检索层不负责：

- 重新切块
- 重新生成向量
- 实现底层持久化数据库
- 设计 Prompt
- 让 LLM 生成答案

它的职责是“把相关证据查得更稳”，不是“替整个 RAG 完成回答”。

---

## 4. 运行时对象与 Retriever 契约 📌

主流程清楚以后，再看对象会更容易。第五章的对象不是为了把代码拆散，而是在共同守住策略层的不变量。

### 4.1 第五章最值得先看的运行时对象

如果你第一次读第五章，最先应该认识这些对象：

| 对象 | 作用 |
|------|------|
| `RetrievalStrategyConfig` | 基础检索策略配置 |
| `SearchHit` | 候选阶段的中间结构 |
| `BadCaseEvaluation` | 坏案例回归结果 |
| `SimpleRetriever` | JSON 原理层 Retriever |
| `ChromaRetriever` | 真实 Chroma 路径 Retriever |
| `SimpleBM25Scorer` | 最小关键词检索 scorer |
| `SimpleCrossReranker` | 教学用两阶段精排器 |
| `SmartRetrievalConfig` | 综合引擎配置 |
| `SmartRetrievalEngine` | 综合案例统一入口 |
| `RetrievalEvalCase` | 固定评估集 case |
| `RetrievalEvaluationReport` | 固定评估结果报告 |

这一遍的目标不是理解所有细节，而是先知道：

- 哪些对象属于基础策略层
- 哪些对象属于真实 backend 映射
- 哪些对象属于评估和治理
- 哪些对象属于统一应用入口

### 4.2 `RetrievalStrategyConfig` 的职责

`RetrievalStrategyConfig` 不是简单参数袋子，它在保三件事：

1. 检索行为是显式的
2. 参数约束会提前失败
3. 下游 Retriever 可以共享同一策略语义

当前它会校验：

- `strategy_name` 必须受支持
- `top_k` 必须大于 `0`
- `candidate_k` 不能小于 `top_k`
- `score_threshold / mmr_lambda` 必须落在 `[0, 1]`

这意味着第五章不是“脚本里随便拼点参数”，而是在定义可复用契约。

### 4.3 `SearchHit -> RetrievalResult` 的分层

第五章特意保留了一个中间结构 `SearchHit`，原因是：

- 候选阶段需要拿到 `EmbeddedChunk`
- 后续阶段要保留 similarity score
- 真正输出时又要统一还原成 `RetrievalResult`

这对应的运行过程是：

```text
EmbeddedChunk + similarity_score
-> SearchHit
-> strategy selection
-> RetrievalResult
```

如果没有这层中间结构，很多策略逻辑会被迫和最终输出结构缠在一起。

### 4.4 `SimpleRetriever` 的原理层价值

`SimpleRetriever` 是第五章的 JSON 原理层。

它的主流程是：

```text
embed_query(question)
-> load_chunks()
-> ensure_same_embedding_space()
-> optional filename filter
-> cosine similarity
-> sort by similarity
-> cut to candidate_k
-> select_search_hits()
-> RetrievalResult[]
```

这一层最重要的教学价值是：

- 让你直接看到“候选召回”和“策略选择”如何拆开
- 让你看到第五章并没有重新发明第四章 store
- 让你看到检索层怎样在 store 之上增加行为控制

### 4.5 `ChromaRetriever` 的真实 backend 映射

`ChromaRetriever` 不是另一个完全不同的检索世界，它补的是：

- 候选召回改由真实 Chroma store 完成
- metadata filter 真正进入数据库查询路径
- 返回的候选需要重新 rehydrate 成 `EmbeddedChunk`

对应主流程大致是：

```text
embed_query(question)
-> store.similarity_search(top_k=candidate_k, where=filename_filter)
-> store.load_chunks(where=...)
-> rehydrate raw results -> EmbeddedChunk
-> select_search_hits()
-> RetrievalResult[]
```

所以第五章同时保留 JSON 和 Chroma 路径，不是为了做两套教学，而是为了让你看清：

> 原理层和真实工具层在策略语义上应该是一致的。

### 4.6 策略选择函数的共同出口

`select_search_hits()` 是基础策略的总路由：

- `similarity` 直接切前 `top_k`
- `threshold` 按阈值过滤后再切 `top_k`
- `mmr` 进入 `maximal_marginal_relevance()`

它的价值在于把“候选召回”和“最终选择”拆开。

候选召回解决的是：

```text
有哪些可能相关的 chunk？
```

策略选择解决的是：

```text
哪些 chunk 应该进入最终上下文？
```

---

## 5. 基础检索策略：similarity / threshold / mmr 📌

基础策略是第五章的核心控制面。Hybrid、Rerank 和高级 Retriever 都应该建立在这里已经稳定的基础上。

### 5.1 三种基础策略的职责

本章当前最核心的三种基础策略是：

| 策略 | 行为 | 适合观察什么 |
|------|------|--------------|
| `similarity` | 直接按相似度从高到低返回结果 | 最基础的语义相关性排序 |
| `threshold` | 先按相似度召回，再用阈值切掉弱相关尾部 | 无答案或弱相关问题 |
| `mmr` | 在候选池中同时考虑相关性和多样性 | 减少重复内容，保留互补信息 |

这三种策略不是三个彼此独立的世界，而是：

> 在同一批候选结果上，采用不同选择规则。

### 5.2 `top_k` 控制最终结果数量

`top_k` 表示最终进入上下文的结果数。

它太小会带来漏召回：

- 相关证据没有进入 Prompt
- 复杂问题只能拿到局部信息
- 后续生成层容易回答不完整

它太大也会带来问题：

- 无关 chunk 进入上下文
- 高度重复 chunk 挤占窗口
- LLM 更容易被噪声干扰

所以 `top_k` 不是“越大越保险”，而是在召回完整性和上下文噪声之间做取舍。

### 5.3 `candidate_k` 控制候选池空间

`candidate_k` 是候选池大小。

它先决定“给 Retriever 多大选择空间”，再由 `threshold` 或 `mmr` 进一步筛选。在很多框架里，它也常被叫做 `fetch_k`。

更准确的理解是：

> `candidate_k` 决定了 Retriever 后续还有没有真正选择的空间。

例如：

- `top_k=3` 且 `candidate_k=3`
  MMR 实际上几乎没有多样化空间
- `top_k=3` 且 `candidate_k=6`
  MMR 才有机会用较低相似度换来更低冗余

这也是第五章会专门保留 `candidate_pool_for_mmr` 这类坏案例的原因。

### 5.4 `score_threshold` 控制弱相关尾部

纯 `similarity` 的默认行为是：

- 无论问题有没有答案
- 都尽量返回 `top_k` 条结果

这在“火星首都是什么？”这类问题上会出问题，因为系统会硬塞几条其实无关的 chunk。

`threshold` 的意义不是“提高精度”这么抽象，而是：

> 允许检索层在无答案或弱相关场景下显式返回空结果。

这是后续生成层非常重要的信号。

当前 demo 默认值 `0.80` 只对本章 toy embedding space 有教学意义，不应该被理解成跨模型通用阈值。

### 5.5 `filename_filter` 控制搜索范围

第五章当前最小实现只支持按 `filename` 过滤。

这一章当然可以继续扩展：

- `document_id`
- `suffix`
- 范围条件
- 复合布尔表达式

但如果在第五章把复杂 metadata DSL 也一起讲，主线会很快跑偏。

所以这里故意只保留：

- 一个最容易观察
- 一个最容易从脚本输出中验证
- 一个最容易和第四章 metadata 概念接上的最小过滤入口

目的不是说“Retriever 只能做 filename 过滤”，而是：

> 先把“过滤应该发生在策略层”这个概念立住。

### 5.6 `mmr_lambda` 控制相关性和多样性

`mmr_lambda` 控制 MMR 中“相关性”和“多样性”的平衡。

- 越接近 `1.0` 越偏相关性
- 越接近 `0.0` 越偏去重

`maximal_marginal_relevance()` 的关键不是公式本身，而是这个思想：

> 下一个结果不是只看“它和 query 有多像”，还要看“它和已经选中的结果有多重复”。

因此它每一步都在平衡：

- 当前候选与 query 的相关性
- 当前候选与已选结果的冗余度

这也是 MMR 经常能把 `refund_process:0` 这类虽然不是最像、但信息互补的 chunk 提出来的原因。

### 5.7 `average_redundancy()` 的观察价值

很多教程讲 MMR，只停在“它可以去重”，但学员很难验证。

`average_redundancy()` 的价值在于：

- 它把“结果是否更重复”变成可计算现象
- 它让 `similarity` 和 `mmr` 的差异不再只是靠肉眼判断
- 它直接进入坏案例回归和单元测试

它不是标准检索指标，但它对这一章非常重要。

---

## 6. 检索评估与坏案例回归 📌

第五章开始不能只看“结果看起来像不像对”，而要开始固定评估口径。

### 6.1 检索评估进入第五章的原因

检索策略一旦多起来，主观观察很快会失效。

你可能遇到这些情况：

- `threshold` 看起来减少了噪声，但也误杀了正确结果
- `MMR` 降低了重复度，但把最关键 chunk 挤掉了
- hybrid 在某个问题上变好，在另一个问题上变差
- rerank 改了排序，但候选池本来就错了

所以第五章必须把“策略效果”变成可复查的观察点。

### 6.2 三个标准检索指标

本章当前使用三类最小指标：

1. `Recall@K`
   期望 chunk 里有多少被召回
2. `MRR`
   第一个正确结果排得有多靠前
3. `Hit Rate`
   至少命中一个正确结果的比例

它们分别回答：

- 是否召回到了足够多正确证据
- 正确证据是否排在足够靠前
- 至少有没有命中一个可用证据

### 6.3 `Average Redundancy` 的教学指标

另外还有一个很关键但不属于标准 IR 指标的教学指标：

4. `Average Redundancy`
   结果之间彼此有多像，用来观察 MMR 是否真的减少冗余

它补的是基础指标很难直接表达的一件事：

> 最终返回的几个 chunk 是否在浪费上下文窗口。

### 6.4 坏案例回归的作用

坏案例不是“多准备几道题”这么简单。

它真正解决的是：

- 把已知脆弱点固定下来
- 用机器可判定的期望做回归
- 避免每次调参数都靠主观感觉

当前坏案例支持检查：

- 顶部结果是不是预期 chunk
- 结果数是不是符合预期
- 是否应该返回空结果
- 是否必须包含某些 chunk
- filename 是否都被限制住
- 冗余度是否超过上限

也就是说，第五章已经开始从“试验脚本”进入“最小治理脚手架”。

### 6.5 基础策略的典型观察点

本章当前最值得反复观察的几条 case：

1. `购买后多久还能退款？`
   `similarity` 会拉回多个高度相似的退款块，`MMR` 更容易带出流程块
2. `为什么 metadata 很重要？`
   加上 `filename_filter=metadata_rules.md` 后，结果范围应明显收缩
3. `火星首都是什么？`
   `threshold` 应尽量把弱相关尾部清掉
4. `candidate_pool_for_mmr`
   说明 `candidate_k` 不够大时，MMR 根本没有可选择空间

这些 case 让策略差异不再只是“看起来不同”，而是能被反复验证。

---

## 7. 混合检索与 Query 增强视角 📌

基础 Retriever 稳定以后，才适合继续讨论检索增强。第五章这里分成两类：一类是本章主线实现的混合检索，一类是只做概念认知的 Query 变换和上下文压缩。

### 7.1 纯向量检索与关键词检索的差异

纯向量检索擅长：

- 语义相似
- 表达泛化
- 同义改写

纯关键词检索擅长：

- 精确术语匹配
- 编号、缩写、短语
- 流程名、专有名词

所以混合检索要解决的问题是：

> 把 BM25 的精确匹配能力和向量检索的语义匹配能力组合起来。

### 7.2 当前代码里的混合检索

当前本章的最小实现包括：

- BM25 scorer：[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- 混合检索 demo：[04_hybrid_retrieval.py](../../source/04_rag/05_retrieval_strategies/04_hybrid_retrieval.py)
- 统一引擎中的 hybrid 入口：[smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/smart_retrieval_engine.py)

当前 demo 用的是：

```text
hybrid_score = alpha * normalized_vector_score
             + (1 - alpha) * normalized_bm25_score
```

其中：

- `alpha` 越大，越偏语义相似
- `alpha` 越小，越偏关键词匹配

运行示例：

```bash
python 04_hybrid_retrieval.py --backend chroma --reset
python 04_hybrid_retrieval.py "退费申请流程" --backend chroma --alpha 0.3
```

### 7.3 `SimpleBM25Scorer` 的教学价值

这一章没有直接接外部 BM25 库，而是手写了最小实现，原因是：

- 让学员看清 TF、IDF 和长度归一化在做什么
- 让“关键词检索”不再只是黑盒名词
- 让 hybrid 的两路分数来源都可解释

这里的 tokenizer 采用：

- 单字
- 字符 bigram

它不追求生产效果，只追求教学透明度。

### 7.4 Query 变换策略的共同目标

这一类策略的共同目标是：

> 不直接拿原始问题去检索，而是先把查询改写成更有利于召回的形式。

典型策略包括：

| 策略 | 做法 | 适合场景 |
|------|------|----------|
| Multi-Query | 让 LLM 生成多个相关查询，再合并多次检索结果 | 用户表达不稳定、同义说法很多 |
| HyDE | 先生成一个“假设性答案”，再拿假设答案做向量检索 | 问题表达抽象，但目标文档语言更具体 |
| Query Decomposition | 把复杂问题拆成多个子问题，分别检索再合并 | 多跳问题或复合问题 |
| Step-back Prompting | 先退一步问更宽泛的问题，再结合原问题检索 | 细节问题依赖大背景 |

### 7.5 上下文压缩的位置

上下文压缩不是“再查一次”，而是：

- 先召回更大候选集
- 再从结果中裁掉无关句段
- 尽量减少噪声和 token 浪费

它解决的是“召回后如何压缩上下文”，不是“如何找到候选”。

这一能力本章只做概念认知，不做本地实现主线。

### 7.6 本章只做部分实现的原因

Query 变换、上下文压缩和混合检索在现实工程里都可以继续深化，但第五章现在只立住三件事：

1. 纯向量不是检索层的唯一工具
2. 关键词和语义各有长短
3. 混合检索最终也应该回到统一接口，而不是永远停留在单独 demo

Multi-Query、HyDE、Query Decomposition、Step-back Prompting 和上下文压缩都很有价值，但它们会显著引入：

- LLM 调用
- prompt 设计
- 多轮检索流程
- 更复杂的评估和缓存问题

如果第五章一开始就把这些策略拉进主线，会把注意力从“检索层基本控制面”拉走。

---

## 8. 两阶段检索：粗筛与 Rerank 📌

Rerank 是第五章的第二类重要增强：它不是替代基础 Retriever，而是在基础召回之后做第二阶段精排。

### 8.1 Rerank 的位置

向量检索适合粗筛，因为它快、可扩展、能先把大量无关文档排除掉。

但向量检索不擅长做非常精细的最终排序，尤其是在：

- 候选都看起来“有点像”
- 需要精确关键词对齐
- 需要更细粒度的 query-document 交互

所以常见做法是：

```text
Query
-> 向量检索粗筛 Top-K
-> Rerank 模型精排
-> 返回 Top-N
```

### 8.2 `fetch_k` 必须大于最终 `top_n`

两阶段检索的关键前提是：

- 第一阶段负责广泛召回
- 第二阶段负责局部重排

如果 `fetch_k == top_n`，第二阶段基本没有空间发挥。

更重要的是：

> Rerank 只能在候选池内部重排，不能凭空创造新结果。

所以如果候选池本身就错了，Rerank 也救不回来。

### 8.3 真实世界里的 Rerank 模型

常见路线包括：

- Cohere Rerank API
- `BAAI/bge-reranker-large`
- ColBERT 一类 late interaction 模型

本章为了保持零额外依赖，只实现了一个教学用 `SimpleCrossReranker`。

它不追求真实效果，只负责把“两阶段检索”这个架构讲清楚。

### 8.4 当前 toy reranker 的行为

`SimpleCrossReranker` 当前做的是：

- 对 query 和 candidate chunk 做最小 token overlap 分析
- 计算一个关键词交叉 F1
- 按 rerank score 重排

这和真实 cross-encoder 的效果当然差很远，但它足够让你观察：

- 粗筛阶段和精排阶段是两回事
- 第二阶段分数语义可能和第一阶段完全不同
- 两阶段架构可以让最终排序更贴近任务需求

### 8.5 当前代码实现

- toy reranker：[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- 单主题 demo：[05_rerank_demo.py](../../source/04_rag/05_retrieval_strategies/05_rerank_demo.py)
- 统一引擎 rerank 入口：[smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/smart_retrieval_engine.py)

运行示例：

```bash
python 05_rerank_demo.py --backend chroma --reset
python 05_rerank_demo.py "购买后多久还能退款？" --backend chroma --fetch-k 6 --top-n 3
```

你应该观察：

- 第一阶段 `fetch_k` 要大于最终 `top_n`
- Rerank 只在候选池内部重排，不会凭空创造新结果
- rerank 分数和向量相似度分数不是同一种语义
- 如果候选池质量太差，Rerank 也无能为力

---

## 9. 高级 Retriever：复杂场景的扩展方向

这一节不要求你现在就实现，而是让你知道在什么场景下，基础方案不够用了。

### 9.1 Self-Query Retriever

Self-Query Retriever 会让 LLM 把自然语言问题拆成：

```text
语义查询 + metadata filter
```

它适合 metadata 丰富的知识库。

它的代价是：

- 更依赖 schema
- 更依赖 prompt 设计
- 更需要 filter 解析和校验

### 9.2 Parent Document Retriever

Parent Document Retriever 的核心思想是：

- 检索时用小块提高召回
- 返回时回到父文档降低碎片化

它适合切块后语义被打散的长文档。

它要求系统能维护：

- 子 chunk
- 父文档
- 子父映射关系

### 9.3 Multi-Vector Retriever

Multi-Vector Retriever 会给同一文档保存多种向量表示。

常见做法包括：

- 标题向量
- 摘要向量
- 正文向量
- 问题式改写向量

它适合多视角表达差异明显的内容。

### 9.4 高级 Retriever 的使用前提

高级 Retriever 值得上的前提是：

- 基础相似度检索已经稳定
- metadata 足够丰富
- 业务允许更高的构建和维护成本
- 你已经有固定评估集，知道新复杂度到底带来了多少收益

这一节最重要的不是记住名词，而是建立判断：

> 只有在基础检索已经稳定、可评估之后，再上更复杂的 Retriever 才有意义。

---

## 10. 综合案例：智能检索引擎 📌

当基础策略、Hybrid、Rerank 和评估都已经出现后，第五章最后用一个最小 `SmartRetrievalEngine` 把它们收束成统一入口。

### 10.1 综合案例解决的内容

大纲要求的不是再写一个零散 demo，而是一个统一入口：

```python
engine = SmartRetrievalEngine(...)
results = engine.retrieve(...)
metrics = engine.evaluate(...)
```

当前本章的最小实现包括：

- 引擎主体：[smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/smart_retrieval_engine.py)
- 评估模块：[retrieval_metrics.py](../../source/04_rag/05_retrieval_strategies/retrieval_metrics.py)
- 评估集：[evals/retrieval_eval_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_eval_cases.json)
- 综合 demo：[06_smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/06_smart_retrieval_engine.py)

### 10.2 `SmartRetrievalConfig` 收束的参数

`SmartRetrievalConfig` 不是简单把前面参数再抄一遍，它收束的是：

- 基础策略选择
- hybrid 权重
- optional rerank
- `fetch_k` 和 `rerank_top_n`
- filename filter
- 参数一致性校验

这意味着：

- 单个 demo 脚本里的零散参数
- 开始上升为统一应用级配置对象

### 10.3 `SmartRetrievalEngine.retrieve()` 的主流程

这一层核心逻辑是：

```text
if strategy == hybrid:
    走向量召回 + BM25 scorer + hybrid fusion
else:
    走基础 retriever strategy

if rerank:
    对粗筛结果做第二阶段重排

return final results
```

这里有两个非常值得建立的判断：

1. hybrid 不是单独的另一个系统，它仍然是检索引擎内部的一种策略
2. rerank 不是和基础检索对立的东西，而是建立在基础召回之上的第二阶段能力

### 10.4 `SmartRetrievalEngine.evaluate()` 的评估闭环

`evaluate()` 的存在非常关键，因为它意味着：

- 第五章不只是在“跑结果”
- 而是在“用固定案例集稳定比较结果”

当前它会：

- 读取 `RetrievalEvalCase`
- 对每条 case 调用统一 `retrieve()`
- 计算 `Recall@K / MRR / Hit Rate`
- 汇总成 `RetrievalEvaluationReport`

这一步让统一引擎不再只是“调用方便”，而是真正进入可评估状态。

### 10.5 统一引擎的价值

如果没有统一引擎，你会很快落入这种状态：

- `01` 是基础对比
- `04` 是混合检索
- `05` 是 rerank
- 每个脚本都能跑
- 但业务代码不知道应该调哪个入口

所以综合案例真正解决的是：

> 把“多个检索实验脚本”收束成“一个可复用应用接口”。

### 10.6 当前综合案例的边界

当前仍然只是教学最小实现，不包括：

- 结果缓存
- 自适应策略选择
- 在线 A/B 测试平台
- 真实 cross-encoder reranker
- query rewrite orchestration

但它已经足够把第五章的核心能力收束起来。

---

## 11. 检索治理与最小回归锚点 📌

第五章还没有进入 Prompt 和生成，但已经开始出现策略差异、参数调优和评估变化，所以这里必须建立最小治理锚点。

### 11.1 第五章建立治理视角的原因

很多课程会把检索策略讲成：

- 改个参数
- 看下效果
- 继续往下

这种做法在小 demo 阶段似乎够用，但一旦开始积累策略，很快就会出现问题：

- 今天调好 `threshold`，明天把 `mmr` 调坏
- hybrid 变好了，但 metadata filter 退化了
- Chroma 路径没坏，JSON 路径坏了
- 统一引擎能跑，但评估集指标掉了

所以第五章就应该开始建立最小治理视角。

### 11.2 第五章最重要的治理锚点

这一章当前最重要的治理锚点有四类：

| 锚点 | 内容 | 作用 |
|------|------|------|
| 参数锚点 | `top_k / candidate_k / threshold / alpha / fetch_k` | 保证调参可复现 |
| 行为锚点 | `similarity / threshold / mmr / hybrid / rerank` | 保证策略语义清晰 |
| 回归锚点 | 坏案例机器可判定 | 保证已知脆弱点不反复退化 |
| 指标锚点 | 固定评估集可重复计算 | 保证策略比较不是主观印象 |

### 11.3 治理锚点缺失后的连锁问题

如果这一章不先把这些锚点立住，第六章开始你会很难判断：

- 是检索坏了，还是生成坏了
- 是召回不够，还是 Prompt 拼接不对
- 是多样性提高了，还是只是把正确答案挤掉了
- 是模型回答变强了，还是只是侥幸命中了正确 chunk

所以第五章的治理价值在于：

> 把“检索层问题”单独隔离、单独观察、单独回归。

### 11.4 第五章最小回归观察点

本章当前最小回归观察点至少包括：

1. `购买后多久还能退款？`
   `similarity` 会拉回多个高度相似的退款块，`MMR` 更容易带出流程块
2. `为什么 metadata 很重要？`
   加上 `filename_filter=metadata_rules.md` 后，结果范围应明显收缩
3. `火星首都是什么？`
   `threshold` 应尽量把弱相关尾部清掉
4. `退费申请流程`
   hybrid 和 rerank 都应更容易把 `refund_process:0` 提前
5. `candidate_pool_for_mmr`
   说明 `candidate_k` 不够大时，MMR 根本没有可选择空间

### 11.5 第五章最值得刻意观察的失败案例

第五章现在最值得你刻意观察的失败类型包括：

1. 重复 chunk 挤占上下文
2. filter 没有限定住结果范围
3. 无答案问题仍然返回若干“看起来像”的结果
4. rerank 改了排序，但其实候选池早就错了
5. hybrid 看似更强，但只是调参后偏向了某一路

如果你能主动观察这些失败，第五章就不只是“会跑命令”，而是真正进入工程视角。

---

## 12. 代码实践：按流程阅读第五章 📌

这一节把前面的抽象落实到代码阅读和命令运行。建议不要一上来就从 `06_smart_retrieval_engine.py` 开始，因为统一引擎会把很多策略细节藏起来。

更适合的顺序是：

```text
先跑基础策略对比
-> 再跑坏案例回归
-> 再看单项增强：hybrid 和 rerank
-> 最后跑统一引擎
-> 回头看 tests 在锁什么
```

### 12.1 目录结构

本章代码目录是：

```text
source/04_rag/05_retrieval_strategies/
├── README.md
├── requirements.txt
├── retrieval_basics.py
├── chroma_retriever.py
├── retrieval_metrics.py
├── smart_retrieval_engine.py
├── 01_compare_retrievers.py
├── 02_review_bad_cases.py
├── 03_query_demo.py
├── 04_hybrid_retrieval.py
├── 05_rerank_demo.py
├── 06_smart_retrieval_engine.py
├── evals/
│   ├── retrieval_bad_cases.json
│   └── retrieval_eval_cases.json
└── tests/
    ├── test_retrievers.py
    ├── test_chroma_retrievers.py
    ├── test_retrieval_metrics.py
    └── test_smart_retrieval_engine.py
```

这些文件可以分成五层：

| 层次 | 文件 | 作用 |
|------|------|------|
| 基础策略层 | `retrieval_basics.py` / `01-03` | similarity / threshold / mmr、BM25、toy reranker |
| 真实 backend 层 | `chroma_retriever.py` | 把策略语义映射到 Chroma |
| 评估层 | `retrieval_metrics.py` / `evals/` / `02` | 固定评估和坏案例回归 |
| 单项增强层 | `04_hybrid_retrieval.py` / `05_rerank_demo.py` | hybrid 和 rerank |
| 统一引擎层 | `smart_retrieval_engine.py` / `06` | 收束多种策略入口 |

### 12.2 本章的输入和输出

第五章的输入不是原始文件，也不是裸向量，而是：

```text
question + store + strategy config
```

第五章的标准输出仍然是：

```text
RetrievalResult[]
```

但第五章比第四章多了一层策略含义：

- 结果数量由 `top_k` 控制
- 候选池由 `candidate_k / fetch_k` 控制
- 弱相关尾部由 `score_threshold` 控制
- 搜索范围由 `filename_filter` 控制
- 多样性由 `mmr_lambda` 控制
- hybrid 和 rerank 可以继续改变排序

如果第五章只返回“某个 store 查出来的 Top-K”，它就没有真正完成策略层任务。

### 12.3 本章最值得先看的对象和函数

第一遍阅读时，建议先看这些对象：

| 对象 | 阅读重点 |
|------|----------|
| `RetrievalStrategyConfig` | 基础策略参数和校验 |
| `SearchHit` | 候选阶段中间结构 |
| `SimpleRetriever` | JSON 原理层 Retriever |
| `ChromaRetriever` | 真实 Chroma 路径 Retriever |
| `SimpleBM25Scorer` | hybrid 的关键词分数来源 |
| `SimpleCrossReranker` | 两阶段精排的教学实现 |
| `BadCaseEvaluation` | 坏案例回归结果 |
| `SmartRetrievalConfig` | 综合引擎配置 |
| `SmartRetrievalEngine` | 统一应用入口 |
| `RetrievalEvaluationReport` | 固定评估输出 |

第二遍再看这些函数和方法：

| 函数/方法 | 阅读重点 |
|-----------|----------|
| `build_demo_retriever()` | demo Retriever 怎样准备 |
| `SimpleRetriever.retrieve()` | JSON 路径基础主流程 |
| `ChromaRetriever.retrieve()` | Chroma 路径策略映射 |
| `select_search_hits()` | 三种基础策略如何路由 |
| `maximal_marginal_relevance()` | MMR 如何平衡相关性和冗余 |
| `average_redundancy()` | 冗余度如何被观察 |
| `load_bad_cases()` | 坏案例如何固定下来 |
| `evaluate_bad_case()` | 坏案例如何机器判定 |
| `hybrid_search()` | 向量分数和 BM25 分数如何融合 |
| `SimpleCrossReranker.rerank()` | 第二阶段如何重排 |
| `SmartRetrievalEngine.retrieve()` | 多种策略如何统一查询 |
| `SmartRetrievalEngine.evaluate()` | 固定评估如何进入引擎 |

### 12.4 运行方式

先进入本章代码目录：

```bash
cd source/04_rag/05_retrieval_strategies
python -m pip install -r requirements.txt
```

如果你的环境暂时没有安装 Chroma 相关依赖，可以先看 JSON 路径和文档主线；真实 Chroma 路径需要对应依赖齐全。

### 12.5 推荐运行顺序

建议按下面顺序跑，而不是先挑一个最复杂的脚本：

1. `01_compare_retrievers.py`
2. `02_review_bad_cases.py`
3. `03_query_demo.py`
4. `04_hybrid_retrieval.py`
5. `05_rerank_demo.py`
6. `06_smart_retrieval_engine.py`
7. `python -m unittest discover -s tests`

这个顺序和文档主线一致：

```text
基础策略 -> 坏案例 -> 单条查询 -> hybrid -> rerank -> 统一引擎 -> tests
```

### 12.6 第一步：`01_compare_retrievers.py`

```bash
python 01_compare_retrievers.py --backend json --reset
python 01_compare_retrievers.py --backend chroma --reset
```

你应该观察到：

- Vector Store 能查，不等于应用层就已经“检索做好了”
- `top_k / candidate_k / threshold / filename_filter / MMR` 都归 Retriever 层管理
- JSON 路径和 Chroma 路径在策略语义上应保持一致
- `similarity / threshold / mmr` 的结果数量、排序和冗余表现不同

### 12.7 第二步：`02_review_bad_cases.py`

```bash
python 02_review_bad_cases.py --backend chroma
```

重点观察：

- `duplicate_refund_chunks`
- `candidate_pool_for_mmr`
- `metadata_scope`
- `no_answer`

这几类 case 已经把第五章最关键的策略差异变成了机器可判定现象。

### 12.8 第三步：`03_query_demo.py`

```bash
python 03_query_demo.py --backend chroma --strategy mmr --candidate-k 4
python 03_query_demo.py --backend chroma --strategy threshold --threshold 0.80 "火星首都是什么？"
```

你应该观察到：

- `candidate_k` 变化会影响 MMR 的选择空间
- `threshold` 可以让弱相关问题返回更少结果或空结果
- 同一个 question 在不同策略下不是只改变展示，而是改变最终进入上下文的证据

### 12.9 第四步：`04_hybrid_retrieval.py`

```bash
python 04_hybrid_retrieval.py --backend chroma --reset
python 04_hybrid_retrieval.py "退费申请流程" --backend chroma --alpha 0.3
```

你应该观察到：

- 关键词和语义相似度各自擅长什么
- `alpha` 怎样改变混合排序
- hybrid 不是替代基础 Retriever，而是在基础召回和关键词分数之间做融合

### 12.10 第五步：`05_rerank_demo.py`

```bash
python 05_rerank_demo.py --backend chroma --reset
python 05_rerank_demo.py "购买后多久还能退款？" --backend chroma --fetch-k 6 --top-n 3
```

你应该观察到：

- `fetch_k` 必须大于最终 `top_n`
- rerank 只是第二阶段精排，不是万能补救
- rerank 分数和向量相似度分数不是同一种语义
- 候选池质量太差时，第二阶段无法创造正确结果

### 12.11 第六步：`06_smart_retrieval_engine.py`

```bash
python 06_smart_retrieval_engine.py "退费申请流程" --backend chroma --strategy hybrid
python 06_smart_retrieval_engine.py "购买后多久还能退款？" --backend chroma --strategy hybrid --rerank --fetch-k 6
python 06_smart_retrieval_engine.py --backend chroma --strategy hybrid --rerank --evaluate
```

这一层开始，你看到的已经不是零散 demo，而是统一应用接口：

- `retrieve(question, config)`
- `evaluate(test_cases, config)`

你应该观察：

- hybrid 和 rerank 可以组合进统一引擎
- 评估不再只是脚本外部动作，而是进入统一接口
- 业务代码不需要直接知道每个 demo 脚本的细节

### 12.12 测试：`tests/`

建议运行：

```bash
python -m unittest discover -s tests
```

这组测试现在锁定的不是“类存在”，而是：

1. JSON 路径能稳定返回相关结果
2. Chroma 路径也能稳定返回相关结果
3. `threshold` 会清空无答案场景的弱相关尾部
4. `filename_filter` 真正作用在 Retriever 层
5. `MMR` 的平均冗余度低于纯 `similarity`
6. `candidate_k` 会改变 MMR 的可选候选池
7. `Recall@K / MRR / Hit Rate` 能在固定评估集上稳定计算
8. `SmartRetrievalEngine` 能统一跑 `hybrid` 和可选 `rerank`

### 12.13 第五章最小回归集

第五章最小回归集可以先记住这几条：

| 场景 | 期望 |
|------|------|
| `购买后多久还能退款？` | `MMR` 比 `similarity` 更容易带出互补流程块 |
| `为什么 metadata 很重要？` | `filename_filter=metadata_rules.md` 后范围明显收窄 |
| `火星首都是什么？` | `threshold` 应清掉弱相关尾部 |
| `退费申请流程` | hybrid / rerank 更容易把 `refund_process:0` 提前 |
| `candidate_pool_for_mmr` | `candidate_k` 太小时 MMR 没有选择空间 |
| `fetch_k == top_n` | rerank 基本没有重排空间 |
| 固定评估集 | `Recall@K / MRR / Hit Rate` 能稳定计算 |

### 12.14 本章代码刻意简化的范围

第五章代码刻意简化了几件事：

1. 本章复用第四章 store 契约，不重新实现存储层
2. metadata filter 只保留 `filename_filter`
3. BM25 scorer 使用教学最小实现，不追求生产分词效果
4. reranker 使用 toy cross reranker，不接真实 cross-encoder
5. Multi-Query / HyDE / Query Decomposition / Step-back 只做概念认知
6. 上下文压缩只做位置说明，不进入本地实现主线
7. 高级 Retriever 只做扩展方向，不纳入默认代码路径
8. 统一引擎不包含缓存、在线实验平台或自适应策略选择

这些简化不是降低知识密度，而是为了保证第五章的学习重心始终在：

> 检索策略契约、参数控制、评估回归和统一入口。

### 12.15 第五章最值得刻意观察的失败案例

第一类是重复结果挤占上下文。

`similarity` 很容易返回多个高度相似的 chunk。你需要观察 MMR 是否真的降低了 `Average Redundancy`，而不是只改变了排序顺序。

第二类是候选池太小。

`candidate_k` 太接近 `top_k` 时，MMR 基本没有选择空间。这个问题不会靠调 `mmr_lambda` 自然消失。

第三类是无答案问题硬返回结果。

如果 `threshold` 没有清掉弱相关尾部，第六章生成层就可能拿着错误上下文认真编答案。

第四类是 filter 假生效。

如果加了 `filename_filter` 后结果范围没有明显收窄，就要检查过滤是否真的进入 Retriever 和 backend 查询路径。

第五类是 rerank 候选池错误。

Rerank 只能重排已有候选。如果第一阶段没有召回正确 chunk，第二阶段不会凭空生成正确结果。

第六类是 hybrid 偏向单路。

`alpha` 调得太偏，hybrid 可能只是披着混合检索外衣的纯向量或纯关键词排序。

### 12.16 建议你主动改的地方

如果你想真正吃透第五章，建议你主动做这些小改动：

1. 把 `candidate_k` 分别改成 `3 / 4 / 6`，观察 MMR 结果怎么变
2. 把 `threshold` 从 `0.80` 调到 `0.70` 或 `0.90`，看无答案问题怎么变
3. 把 `alpha` 从 `0.2 / 0.5 / 0.8` 跑一遍，观察 hybrid 排序变化
4. 把 `fetch_k` 改小到接近 `top_n`，感受 rerank 为什么失去空间
5. 自己往 eval case 和 bad case 里新增一条问题，再看测试和评估是否还能稳定

### 12.17 最推荐的阅读配套顺序

跑代码时，建议对应打开这些文件：

1. 跑 `01-03` 时看 [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
2. 跑 Chroma backend 时看 [chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)
3. 跑坏案例和评估时看 [retrieval_metrics.py](../../source/04_rag/05_retrieval_strategies/retrieval_metrics.py) 与 `evals/`
4. 跑 `04-05` 时回到 [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py) 看 BM25 和 reranker
5. 跑 `06` 时看 [smart_retrieval_engine.py](../../source/04_rag/05_retrieval_strategies/smart_retrieval_engine.py)

这样会比“先把所有脚本都跑一遍，再回头找实现”更容易建立结构感。

---

## 13. 常见疑惑与复盘问题

### 13.1 Retriever 是不是 Vector Store 的包装

不是。

Vector Store 负责：

- 存向量
- 查向量
- 保留 chunk 和 metadata
- 支持基础过滤和删除

Retriever 负责：

- 接收 question
- 设定策略
- 控制候选池
- 处理阈值、多样性、混合分数和精排
- 把结果组织成后续生成层可消费的证据

所以 Retriever 不是给 Vector Store 套一层名字，而是在 store 之上建立策略层。

### 13.2 `candidate_k` 为什么不是附属参数

`candidate_k` 决定策略还有多少选择空间。

如果 `candidate_k == top_k`，MMR 没有更多候选可以比较，Rerank 也没有更多候选可以重排。

所以 `candidate_k / fetch_k` 是检索策略的核心参数，不是随手设大的附属参数。

### 13.3 threshold 是不是越高越好

不是。

阈值太低会保留弱相关噪声，阈值太高会误杀有用证据。

而且分数分布依赖 embedding provider、向量库距离度量和具体语料。当前 demo 的 `0.80` 只服务于本章 toy space，不是生产默认答案。

### 13.4 MMR 是不是简单去重

不是。

MMR 不是只把相似内容删掉，而是在相关性和多样性之间做平衡。

如果 `mmr_lambda` 太低，结果可能过度追求多样性而牺牲相关性；如果太高，又会退化得接近普通 similarity。

### 13.5 Hybrid 和 Rerank 谁更高级

它们解决的问题不同。

Hybrid 是召回和排序阶段的分数融合，目的是把关键词匹配和语义匹配结合起来。

Rerank 是两阶段架构，目的是在候选池内部用更精细的模型或规则重新排序。

实际工程里它们可以组合，而不是互相替代。

### 13.6 Query 增强为什么本章只做概念认知

Multi-Query、HyDE、Query Decomposition 和 Step-back Prompting 都需要引入 LLM 调用、prompt 设计、多轮检索、缓存和更复杂评估。

如果第五章一开始就把它们全部实现，会遮住本章更基础的主线：

> Retriever 策略、参数控制、评估回归和统一入口。

所以它们先作为扩展方向出现，等基础 Retriever 稳定以后再深入更合适。

### 13.7 统一引擎会不会掩盖策略差异

一个好的统一引擎不应该假装策略没有差异。

`SmartRetrievalEngine` 统一的是应用入口：

- retrieve
- evaluate
- config

策略差异仍然保留在内部：

- similarity
- threshold
- mmr
- hybrid
- rerank

这样业务调用更稳定，同时读代码时仍然能看清不同策略的行为边界。

---

## 14. 本章学完后你应该能回答

- 为什么第五章应该复用第四章的 store 契约，而不是重做存储层
- 为什么 Retriever 不能等同于 Vector Store
- `top_k / candidate_k / threshold / filename_filter / MMR` 各自解决什么问题
- 为什么坏案例和固定评估集都必须存在
- 为什么混合检索和 Rerank 都应该建立在基础 Retriever 之上
- 为什么 Query 增强和高级 Retriever 先作为扩展方向出现
- 为什么综合案例需要一个统一检索引擎，而不是继续堆更多独立脚本

---

## 15. 下一章

第六章开始，你才会把本章的 Retriever 输出真正拼进 Prompt 和生成链路。

也就是说：

> 第五章解决的是“怎么查得更稳、更可控、更可评估”，不是“怎么生成最终答案”。
