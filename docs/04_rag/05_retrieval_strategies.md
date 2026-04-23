# 05. 检索策略

> 本章目标：把第四章的“能查”推进到第五章的“查得稳、查得可控、查得可评估”。你会先掌握基础 Retriever 策略，再理解混合检索与两阶段检索，最后用一个最小 `SmartRetrievalEngine` 把这些能力收束成统一接口。

---

## 1. 概述

### 学习目标

- 理解为什么第五章新增的是 Retriever 策略层，而不是重写第四章存储层
- 掌握 `similarity / threshold / mmr` 三种基础检索策略的行为差异
- 理解 `top_k / candidate_k(fetch_k) / score_threshold / mmr_lambda / filename_filter` 的职责
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

第五章只关注检索层 specific 的问题。

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

### 当前代码入口

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

---

## 2. 为什么第四章的 Store 还不等于第五章的 Retriever 📌

### 2.1 第四章交付了什么

第四章已经让系统拥有：

- 可持久化的向量存储
- 最小相似度查询能力
- `document_id` 级更新和删除能力
- metadata 的最小过滤路径
- 稳定的 `RetrievalResult[]` 输出

这意味着第四章已经解决了“能不能查”和“查出来的结果是否有稳定身份”。

### 2.2 第五章真正新增的是什么

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

### 2.3 为什么只有相似度查询还不够

如果系统只有“直接按相似度取 Top-K”，很快会遇到这些问题：

- 相似结果高度重复，浪费上下文窗口
- 无答案问题也会被硬塞进若干“勉强相关”的 chunk
- 精确术语、编号、流程类问题不一定靠纯向量最稳
- 一个 demo 脚本和另一个 demo 脚本之间没有统一接口
- 你无法稳定比较“这次调整到底变好了还是变坏了”

所以第五章不是“第四章再跑一遍”，而是在定义：

> 应用层如何在同一个底层 store 之上，把检索做得更稳、更可控、更可评估。

### 2.4 第五章的运行时主链路

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

### 2.5 第五章交付的是“稳定策略层”

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

### 2.6 检索层不负责什么

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

## 3. 基础检索与参数控制（对应大纲第 13 节） 📌

### 3.1 第五章最值得先看的运行时对象

如果你第一次读第五章代码，最先应该认识这些对象：

- `RetrievalStrategyConfig`
- `SearchHit`
- `SimpleRetriever`
- `ChromaRetriever`
- `SimpleBM25Scorer`
- `SimpleCrossReranker`
- `SmartRetrievalConfig`
- `SmartRetrievalEngine`

它们分别对应：

- 策略配置
- 候选阶段中间结构
- JSON 原理层 Retriever
- 真实 Chroma 路径 Retriever
- 关键词检索
- 两阶段精排
- 综合案例配置
- 综合案例统一入口

### 3.2 三种基础策略到底在做什么

本章当前最核心的三种基础策略是：

1. `similarity`
   直接按相似度从高到低返回结果
2. `threshold`
   先按相似度召回，再用阈值切掉弱相关尾部
3. `mmr`
   在候选池中同时考虑相关性和多样性，减少重复内容

对应代码：

- JSON 路径：[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- Chroma 路径：[chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)

这三种策略不是三个彼此独立的世界，而是：

> 在同一批候选结果上，采用不同选择规则。

### 3.3 `top_k / candidate_k / score_threshold / filename_filter / mmr_lambda`

#### `top_k`

- 最终进入上下文的结果数
- 太小容易漏信息
- 太大容易带入噪声和冗余

#### `candidate_k`

- 候选池大小
- 先决定“给 Retriever 多大选择空间”，再由 `threshold` 或 `mmr` 进一步筛选
- 在大纲语义里，它对应很多框架里的 `fetch_k`

#### `score_threshold`

- 处理弱相关尾部和“无答案”问题
- 没有跨模型通用的最佳阈值
- 当前 demo 默认值 `0.80` 只对本章 toy embedding space 有教学意义

#### `filename_filter`

- 当前最小实现只支持按 `filename` 过滤
- 它代表“Retriever 层可以显式缩小搜索范围”
- 它是教学用最小 metadata filter，不是完整 DSL

#### `mmr_lambda`

- 控制 MMR 中“相关性”和“多样性”的平衡
- 越接近 `1.0` 越偏相关性
- 越接近 `0.0` 越偏去重

### 3.4 为什么 `candidate_k` 不是附属参数

很多初学者会把 `candidate_k` 看成“随便比 `top_k` 大一点就行”的附属参数，这不够准确。

更准确的理解是：

> `candidate_k` 决定了 Retriever 后续还有没有真正选择的空间。

例如：

- `top_k=3` 且 `candidate_k=3`
  MMR 实际上几乎没有多样化空间
- `top_k=3` 且 `candidate_k=6`
  MMR 才有机会用较低相似度换来更低冗余

这也是为什么第五章会专门保留 `candidate_pool_for_mmr` 这类坏案例。

### 3.5 为什么 `threshold` 对“无答案”问题特别重要

纯 `similarity` 的默认行为是：

- 无论问题有没有答案
- 都尽量返回 `top_k` 条结果

这在“火星首都是什么？”这类问题上会出问题，因为系统会硬塞几条其实无关的 chunk。

`threshold` 的意义不是“提高精度”这么抽象，而是：

> 允许检索层在无答案或弱相关场景下显式返回空结果。

这是后续生成层非常重要的信号。

### 3.6 为什么第五章现在只讲 `filename_filter`

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

### 3.7 基础检索评估

第五章不再只看“结果看起来像不像对”，而要开始固定评估口径。

本章当前使用三类最小指标：

1. `Recall@K`
   期望 chunk 里有多少被召回
2. `MRR`
   第一个正确结果排得有多靠前
3. `Hit Rate`
   至少命中一个正确结果的比例

另外还有一个很关键但不属于标准 IR 指标的教学指标：

4. `Average Redundancy`
   结果之间彼此有多像，用来观察 MMR 是否真的减少冗余

其中：

- `Recall@K / MRR / Hit Rate` 放在 [retrieval_metrics.py](../../source/04_rag/05_retrieval_strategies/retrieval_metrics.py)
- `Average Redundancy` 放在 [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)

### 3.8 基础检索实践映射

对比不同策略：

```bash
python 01_compare_retrievers.py --backend json --reset
python 01_compare_retrievers.py --backend chroma --reset
```

观察坏案例回归：

```bash
python 02_review_bad_cases.py --backend chroma
```

只跑一条策略：

```bash
python 03_query_demo.py --backend chroma --strategy mmr --candidate-k 4
python 03_query_demo.py --backend chroma --strategy threshold --threshold 0.80 "火星首都是什么？"
```

这一节学完后，你至少应该能回答：

- 为什么 `candidate_k` 不只是附属参数
- 为什么 `threshold` 对“无答案”问题特别重要
- 为什么 MMR 不是“再多拿几条相似结果”

---

## 4. 基础 Retriever 实现映射 📌

### 4.1 `RetrievalStrategyConfig` 在保什么

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

### 4.2 `SearchHit -> RetrievalResult` 在补什么

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

### 4.3 `SimpleRetriever` 真正在做什么

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

### 4.4 `ChromaRetriever` 真正在补什么

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

所以第五章现在同时保留 JSON 和 Chroma 路径，不是为了做两套教学，而是为了让你看清：

> 原理层和真实工具层在策略语义上应该是一致的。

### 4.5 `select_search_hits()` 和 `maximal_marginal_relevance()` 在补什么

`select_search_hits()` 是基础策略的总路由：

- `similarity` 直接切前 `top_k`
- `threshold` 按阈值过滤后再切 `top_k`
- `mmr` 进入 `maximal_marginal_relevance()`

`maximal_marginal_relevance()` 的关键不是公式本身，而是这个思想：

> 下一个结果不是只看“它和 query 有多像”，还要看“它和已经选中的结果有多重复”。

因此它每一步都在平衡：

- 当前候选与 query 的相关性
- 当前候选与已选结果的冗余度

这也是为什么 MMR 经常能把 `refund_process:0` 这类虽然不是最像、但信息互补的 chunk 提出来。

### 4.6 `average_redundancy()` 为什么值得单独保留

很多教程讲 MMR，只停在“它可以去重”，但学员很难验证。

`average_redundancy()` 的价值在于：

- 它把“结果是否更重复”变成可计算现象
- 它让 `similarity` 和 `mmr` 的差异不再只是靠肉眼判断
- 它直接进入坏案例回归和单元测试

它不是标准检索指标，但它对这一章非常重要。

### 4.7 `load_bad_cases()` / `evaluate_bad_case()` 在补什么

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

---

## 5. 混合检索与 Query 增强视角（对应大纲第 14 节） 📌

### 5.1 Query 变换策略在解决什么

这一类策略的共同目标是：

> 不直接拿原始问题去检索，而是先把查询改写成更有利于召回的形式。

#### Multi-Query

- 让 LLM 生成多个相关查询
- 合并多次检索结果
- 适合用户表达不稳定、同义说法很多的场景

#### HyDE

- 先生成一个“假设性答案”
- 再拿假设答案做向量检索
- 适合问题表达抽象，但目标文档语言更具体的场景

#### Query Decomposition

- 把复杂问题拆成多个子问题
- 分别检索，再合并结果
- 适合多跳问题或复合问题

#### Step-back Prompting

- 先退一步问更宽泛的问题
- 再结合原问题做更精细检索
- 适合细节问题依赖大背景时

### 5.2 为什么这些策略本章只做概念认知

这些策略当然很有价值，但它们会显著引入：

- LLM 调用
- prompt 设计
- 多轮检索流程
- 更复杂的评估和缓存问题

如果第五章一开始就把这些策略拉进主线，会把注意力从“检索层基本控制面”拉走。

所以本章先只做认知对齐：

- 它们属于检索优化层
- 但不是第五章当前主线默认实现

### 5.3 上下文压缩在解决什么

上下文压缩不是“再查一次”，而是：

- 先召回更大候选集
- 再从结果中裁掉无关句段
- 尽量减少噪声和 token 浪费

它解决的是“召回后如何压缩上下文”，不是“如何找到候选”。

这一能力本章只做概念认知，不做本地实现主线。

### 5.4 为什么纯向量检索还需要混合检索

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

### 5.5 当前代码里的混合检索实现

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

### 5.6 `SimpleBM25Scorer` 的教学价值

这一章没有直接接外部 BM25 库，而是手写了最小实现，原因是：

- 让学员看清 TF、IDF 和长度归一化在做什么
- 让“关键词检索”不再只是黑盒名词
- 让 hybrid 的两路分数来源都可解释

这里的 tokenizer 采用：

- 单字
- 字符 bigram

它不追求生产效果，只追求教学透明度。

### 5.7 这一节的边界

Query 变换、上下文压缩和混合检索在现实工程里都可以继续深化，但第五章现在只立住三件事：

1. 纯向量不是检索层的唯一工具
2. 关键词和语义各有长短
3. 混合检索最终也应该回到统一接口，而不是永远停留在单独 demo

---

## 6. Rerank 重排序（对应大纲第 15 节） 📌

### 6.1 为什么需要 Rerank

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

### 6.2 为什么 `fetch_k` 必须大于最终 `top_n`

两阶段检索的关键前提是：

- 第一阶段负责广泛召回
- 第二阶段负责局部重排

如果 `fetch_k == top_n`，第二阶段基本没有空间发挥。

更重要的是：

> Rerank 只能在候选池内部重排，不能凭空创造新结果。

所以如果候选池本身就错了，Rerank 也救不回来。

### 6.3 真实世界里的 Rerank 模型

常见路线包括：

- Cohere Rerank API
- `BAAI/bge-reranker-large`
- ColBERT 一类 late interaction 模型

本章为了保持零额外依赖，只实现了一个教学用 `SimpleCrossReranker`。

它不追求真实效果，只负责把“两阶段检索”这个架构讲清楚。

### 6.4 当前 toy reranker 在做什么

`SimpleCrossReranker` 当前做的是：

- 对 query 和 candidate chunk 做最小 token overlap 分析
- 计算一个关键词交叉 F1
- 按 rerank score 重排

这和真实 cross-encoder 的效果当然差很远，但它足够让你观察：

- 粗筛阶段和精排阶段是两回事
- 第二阶段分数语义可能和第一阶段完全不同
- 两阶段架构为什么能让最终排序更贴近任务需求

### 6.5 当前代码实现

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

## 7. 高级 Retriever（选读，对应大纲第 16 节）

这一节不要求你现在就实现，而是让你知道在什么场景下，基础方案不够用了。

### 7.1 Self-Query Retriever

- 让 LLM 把自然语言问题拆成“语义查询 + metadata filter”
- 适合 metadata 丰富的知识库
- 代价是更依赖 schema 和 prompt 设计

### 7.2 Parent Document Retriever

- 检索时用小块提高召回
- 返回时回到父文档降低碎片化
- 适合切块后语义被打散的长文档

### 7.3 Multi-Vector Retriever

- 同一文档保存多种向量表示
- 标题、摘要、正文可以分别建索引
- 适合多视角表达差异明显的内容

### 7.4 什么时候值得上高级 Retriever

- 基础相似度检索已经稳定
- metadata 足够丰富
- 业务允许更高的构建和维护成本
- 你已经有固定评估集，知道新复杂度到底带来了多少收益

这一节最重要的不是记住名词，而是建立判断：

> 只有在基础检索已经稳定、可评估之后，再上更复杂的 Retriever 才有意义。

---

## 8. 综合案例：智能检索引擎 📌

### 8.1 大纲真正要求的是什么

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

### 8.2 `SmartRetrievalConfig` 在收束什么

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

### 8.3 `SmartRetrievalEngine.retrieve()` 真正在做什么

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

### 8.4 `SmartRetrievalEngine.evaluate()` 真正在补什么

`evaluate()` 的存在非常关键，因为它意味着：

- 第五章不只是在“跑结果”
- 而是在“用固定案例集稳定比较结果”

当前它会：

- 读取 `RetrievalEvalCase`
- 对每条 case 调用统一 `retrieve()`
- 计算 `Recall@K / MRR / Hit Rate`
- 汇总成 `RetrievalEvaluationReport`

这一步让统一引擎不再只是“调用方便”，而是真正进入可评估状态。

### 8.5 为什么统一引擎重要

如果没有统一引擎，你会很快落入这种状态：

- `01` 是基础对比
- `04` 是混合检索
- `05` 是 rerank
- 每个脚本都能跑
- 但业务代码不知道到底应该调哪个入口

所以综合案例真正解决的是：

> 把“多个检索实验脚本”收束成“一个可复用应用接口”。

### 8.6 当前综合案例的边界

当前仍然只是教学最小实现，不包括：

- 结果缓存
- 自适应策略选择
- 在线 A/B 测试平台
- 真实 cross-encoder reranker
- query rewrite orchestration

但它已经足够把第五章的核心能力收束起来。

---

## 9. 检索治理与最小回归锚点 📌

### 9.1 为什么第五章就要开始有治理视角

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

### 9.2 第五章最重要的治理锚点是什么

这一章当前最重要的治理锚点有四类：

1. 参数锚点
   `top_k / candidate_k / threshold / alpha / fetch_k` 必须显式
2. 行为锚点
   `similarity / threshold / mmr / hybrid / rerank` 必须语义清晰
3. 回归锚点
   坏案例必须机器可判定
4. 指标锚点
   固定评估集必须可重复计算

### 9.3 如果第五章不把这些锚点立住，后面会发生什么

如果这一章不先把这些锚点立住，第六章开始你会很难判断：

- 是检索坏了，还是生成坏了
- 是召回不够，还是 Prompt 拼接不对
- 是多样性提高了，还是 simply 把正确答案挤掉了
- 是模型回答变强了，还是只是侥幸命中了正确 chunk

所以第五章的治理价值在于：

> 把“检索层问题”单独隔离、单独观察、单独回归。

### 9.4 第五章最小回归观察点

本章当前最值得反复观察的几条 case：

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

### 9.5 第五章最值得刻意观察的失败案例

第五章现在最值得你刻意观察的失败类型包括：

- 重复 chunk 挤占上下文
- filter 没有限定住结果范围
- 无答案问题仍然返回若干“看起来像”的结果
- rerank 改了排序，但其实候选池早就错了
- hybrid 看似更强，但只是调参后偏向了某一路

如果你能主动观察这些失败，第五章就不只是“会跑命令”，而是真正进入工程视角。

---

## 10. 如何阅读第五章代码

### 10.1 第一遍只看对象

先打开 [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)，只看这些对象：

- `RetrievalStrategyConfig`
- `SearchHit`
- `BadCaseEvaluation`
- `SimpleRetriever`
- `SimpleBM25Scorer`
- `SimpleCrossReranker`

然后再补看：

- `ChromaRetriever`
- `SmartRetrievalConfig`
- `SmartRetrievalEngine`
- `RetrievalEvalCase`
- `RetrievalEvaluationReport`

这一遍的目标不是理解所有逻辑，而是先知道：

- 第五章有哪些最小运行时对象
- 哪些对象属于原理层，哪些属于真实工具层
- 为什么第五章不是只返回一组相似度分数

### 10.2 第二遍只看主流程

然后再看这些函数和方法：

- `build_demo_retriever()`
- `SimpleRetriever.retrieve()`
- `ChromaRetriever.retrieve()`
- `select_search_hits()`
- `maximal_marginal_relevance()`
- `hybrid_search()`
- `SimpleCrossReranker.rerank()`
- `SmartRetrievalEngine.retrieve()`
- `SmartRetrievalEngine.evaluate()`

这一遍只回答一个问题：

```text
一个 question 进入第五章以后，到底按什么顺序变成可控、可比较、可评估的 RetrievalResult[]？
```

### 10.3 第三遍再看 demo 和 tests

最后再看：

- `01_compare_retrievers.py`
- `02_review_bad_cases.py`
- `03_query_demo.py`
- `04_hybrid_retrieval.py`
- `05_rerank_demo.py`
- `06_smart_retrieval_engine.py`
- `tests/`

这样读会比一开始从头到尾顺着扫更容易建立结构感。

---

## 11. 第五章实践：建议运行顺序

### 11.1 安装依赖

在 `source/04_rag/05_retrieval_strategies/` 目录下运行：

```bash
python -m pip install -r requirements.txt
```

### 11.2 先跑基础策略对比

```bash
python 01_compare_retrievers.py --backend json --reset
python 01_compare_retrievers.py --backend chroma --reset
python 03_query_demo.py --backend chroma --strategy mmr --candidate-k 4
python 03_query_demo.py --backend chroma --strategy threshold --threshold 0.80 "火星首都是什么？"
```

重点观察：

- Vector Store 能查，不等于应用层就已经“检索做好了”
- `top_k / candidate_k / threshold / filename_filter / MMR` 都归 Retriever 层管理
- JSON 路径和 Chroma 路径在策略语义上应保持一致

### 11.3 再跑坏案例回归

```bash
python 02_review_bad_cases.py --backend chroma
```

重点观察：

- `duplicate_refund_chunks`
- `candidate_pool_for_mmr`
- `metadata_scope`
- `no_answer`

这几类 case 已经把第五章最关键的策略差异变成了机器可判定现象。

### 11.4 再看单项增强：hybrid 和 rerank

```bash
python 04_hybrid_retrieval.py --backend chroma --reset
python 04_hybrid_retrieval.py "退费申请流程" --backend chroma --alpha 0.3
python 05_rerank_demo.py --backend chroma --reset
python 05_rerank_demo.py "购买后多久还能退款？" --backend chroma --fetch-k 6 --top-n 3
```

重点观察：

- 关键词和语义相似度各自擅长什么
- `alpha` 怎样改变混合排序
- `fetch_k` 为什么必须大于最终 `top_n`
- rerank 为什么只是第二阶段精排，而不是万能补救

### 11.5 最后跑统一引擎

```bash
python 06_smart_retrieval_engine.py "退费申请流程" --backend chroma --strategy hybrid
python 06_smart_retrieval_engine.py "购买后多久还能退款？" --backend chroma --strategy hybrid --rerank --fetch-k 6
python 06_smart_retrieval_engine.py --backend chroma --strategy hybrid --rerank --evaluate
```

这一层开始，你看到的已经不是零散 demo，而是统一应用接口：

- `retrieve(question, config)`
- `evaluate(test_cases, config)`

### 11.6 测试在锁定什么

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

### 11.7 建议你主动改的地方

如果你想真正吃透第五章，建议你主动做这些小改动：

1. 把 `candidate_k` 分别改成 `3 / 4 / 6`，观察 MMR 结果怎么变
2. 把 `threshold` 从 `0.80` 调到 `0.70` 或 `0.90`，看无答案问题怎么变
3. 把 `alpha` 从 `0.2 / 0.5 / 0.8` 跑一遍，观察 hybrid 排序变化
4. 把 `fetch_k` 改小到接近 `top_n`，感受 rerank 为什么失去空间
5. 自己往 eval case 和 bad case 里新增一条问题，再看测试和评估是否还能稳定

---

## 12. 本章学完后你应该能回答

- 为什么第五章应该复用第四章的 store 契约，而不是重做存储层
- 为什么 Retriever 不能等同于 Vector Store
- `top_k / candidate_k / threshold / filename_filter / MMR` 各自解决什么问题
- 为什么坏案例和固定评估集都必须存在
- 为什么混合检索和 Rerank 都应该建立在基础 Retriever 之上
- 为什么综合案例需要一个统一检索引擎，而不是继续堆更多独立脚本

---

## 13. 下一章

第六章开始，你才会把本章的 Retriever 输出真正拼进 Prompt 和生成链路。

也就是说：

> 第五章解决的是“怎么查得更稳、更可控、更可评估”，不是“怎么生成最终答案”。
