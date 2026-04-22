# 05. 检索策略

> 本章目标：理解为什么第四章的向量查询结果还不能直接等同于“好的检索”，先用 JSON store 看清基础策略参数在做什么，再把同一套策略真正挂到第四章的 `Chroma` 上，然后进一步掌握混合检索和两阶段检索（Rerank）的核心原理。

---

## 1. 概述

### 学习目标

- 理解 Retriever 在 RAG 系统里的职责边界
- 理解为什么很多回答错误，根因其实在检索而不是 Prompt
- 看懂第五章如何继续站在第四章的 `PersistentVectorStore / ChromaVectorStore + EmbeddingSpace` 契约之上
- 掌握 `top_k / candidate_k / score_threshold / MMR / filename_filter` 的基本边界
- 能运行第五章脚本，并解释坏案例回归为什么要变成可判定的 `PASS / FAIL`
- 理解混合检索（BM25 + 向量）如何取长补短
- 理解两阶段检索（Rerank）的架构和价值
- 了解 Query 变换策略和高级 Retriever 的概念边界

### 预计学习时间

- Retriever 边界理解：30-40 分钟
- 策略参数与坏案例：40-60 分钟
- 真实 Chroma 实践：30-40 分钟
- 混合检索：40-60 分钟
- Rerank 两阶段检索：40-60 分钟
- Query 变换与高级 Retriever 概念认知：20-30 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 第五章先解决什么 |
|------|------------------|
| 基础 Top-K 查询之后 | 为什么还需要 Retriever 层而不是直接把 store 暴露给业务 |
| 噪声控制 | `top_k / candidate_k / threshold` 怎么影响上下文质量 |
| 重复内容较多 | 为什么要引入 MMR 而不只是继续增大 `top_k` |
| 范围约束 | 为什么 `filename_filter` 应进入策略配置 |
| 回归调试 | 为什么坏案例不能只靠人工观察，而要开始有机器可判定标准 |
| 精确关键词查询 | 为什么纯向量检索会漏掉精确匹配，混合检索怎么补 |
| 候选池噪声大 | 两阶段检索（Rerank）为什么能提升精排质量 |

### 本章与前后章节的关系

第四章已经解决：

1. 向量怎样被持久化存起来
2. 怎么做最小相似度查询
3. query 和 store 必须保持同一 embedding space
4. JSON store、Chroma、LangChain Chroma 的映射关系

第五章接着解决：

1. 如何把底层查询收束成 Retriever
2. 如何控制召回数量、噪声和多样性
3. 如何把策略差异做成可重复实验
4. 如何把第四章的真实 Chroma 变成第五章的真实策略实验底座

第六章才继续解决：

1. 把 Retriever 返回结果拼进 Prompt
2. 形成真正的 RAG Chain

### 第五章与第四章的连续性

第五章不应该重新发明一套 provider、chunk 或 store。

当前代码有两条连续路径：

```text
chapter 4 PersistentVectorStore
-> chapter 5 SimpleRetriever
-> RetrievalResult[]
```

```text
chapter 4 ChromaVectorStore
-> chapter 5 ChromaRetriever
-> RetrievalResult[]
```

也就是说，第五章真正新增的是策略层，而不是再次重写：

- `SourceChunk`
- `EmbeddedChunk`
- embedding provider
- 向量空间契约
- store 持久化

### 关于代码复制的说明

第五章新增的：

- [chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)

是从旧的 `labs/phase_5_retrieval_strategies/app/retrievers/chroma.py` 扁平化提炼出来的。

保留独立副本的原因是：

- 当前主线章节不再回到 `app/` 工程骨架
- 但第五章仍然需要一个真实 `ChromaRetriever`
- 所以这里保留一个“只服务于第五章策略实验”的平铺版实现

### 本章代码入口

- [README.md](../../source/04_rag/05_retrieval_strategies/README.md)
- [requirements.txt](../../source/04_rag/05_retrieval_strategies/requirements.txt)
- [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- [chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)
- [01_compare_retrievers.py](../../source/04_rag/05_retrieval_strategies/01_compare_retrievers.py)
- [02_review_bad_cases.py](../../source/04_rag/05_retrieval_strategies/02_review_bad_cases.py)
- [03_query_demo.py](../../source/04_rag/05_retrieval_strategies/03_query_demo.py)
- [04_hybrid_retrieval.py](../../source/04_rag/05_retrieval_strategies/04_hybrid_retrieval.py)
- [05_rerank_demo.py](../../source/04_rag/05_retrieval_strategies/05_rerank_demo.py)
- [evals/retrieval_bad_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json)

### 本章边界

本章重点解决：

1. Retriever 的职责
2. 基础检索参数
3. MMR 多样性控制
4. `filename` 范围约束
5. 坏案例记录和最小可判定回归
6. JSON 原理层和 Chroma 实践层的对照
7. 混合检索：BM25 + 向量加权融合
8. 两阶段检索：Rerank 重排序

本章做概念认知但不展开实现：

- Query 变换策略（Multi-Query / HyDE / Query Decomposition）
- 高级 Retriever（Self-Query / Parent Document / Multi-Vector）

本章不展开：

- LangChain Retriever 抽象
- Prompt 和生成答案

---

## 2. Retriever 在系统里到底负责什么 📌

### 2.1 为什么不能把 Vector Store 直接当 Retriever

第四章的 Vector Store 更偏基础设施层，负责：

- 存
- 查
- 删
- 保证向量空间一致性
- 保留 metadata 和 chunk 身份

Retriever 更偏应用层，负责：

- 接收用户问题
- 决定查询参数
- 决定召回数量
- 决定是否做阈值过滤或多样性控制
- 把结果整理成后续链路能消费的统一接口

所以 Retriever 的本质不是“再包一层类”，而是：

> 把底层查询能力收束成稳定的应用侧检索接口。

### 2.2 第五章真正新增了什么

第五章当前真正新增的是：

- `RetrievalStrategyConfig`
- `SimpleRetriever`
- `ChromaRetriever`
- `maximal_marginal_relevance()`
- 最小 bad-case regression

### 2.3 为什么检索质量是 RAG 的核心变量

如果召回结果本身不对，后面 Prompt 写得再好，模型也只能在错误上下文里回答。

所以第五章要建立的习惯是：

> 先看召回结果，再看生成结果。

---

## 3. 这些策略参数分别在解决什么 📌

### 3.1 `top_k`

`top_k` 决定最终要带多少条结果进入后续链路。

它太小：

- 可能漏掉关键依据

它太大：

- 会把噪声和冗余一起带进去

### 3.2 `candidate_k`

很多人只盯 `top_k`，但 Retriever 真正先控制的是候选池。

`candidate_k` 的作用是：

> 先把“可能有用的范围”拉出来，再让 threshold 或 MMR 在这批候选里做进一步选择。

这一点在第五章的 `candidate_pool_for_mmr` case 里会被显式看到。

### 3.3 `score_threshold`

阈值过滤解决的是：

- 不让明显弱相关的尾部进入上下文
- 更好地处理“无答案”场景

要注意：

> threshold 没有跨模型通用的最佳值。

当前第五章默认阈值基线是 `0.80`，因为它复用了本章当前 embedding space 的分布。

### 3.4 MMR

MMR 的目标不是单纯找“最像”的结果，而是：

> 在相关性和多样性之间做平衡。

它更适合：

- 重复内容较多
- 希望上下文覆盖更多角度

### 3.5 `filename_filter`

第五章当前确实支持过滤，但要说准确：

> 当前最小实现只支持 `filename_filter`，不是通用 metadata filter DSL。

这和第四章保持一致。

---

## 4. JSON 原理层和真实 Chroma 层怎么分工 📌

### 4.1 为什么第五章现在还保留 JSON 路径

JSON 路径仍然很有价值，因为它最适合把策略本身看清楚。

在这条路径里，你可以直接看到：

- query vector
- candidate pool
- similarity score
- MMR 选择顺序

它更像一个“策略教学放大镜”。

### 4.2 为什么第五章默认切到 Chroma

如果第五章只停留在 JSON 路径，会和第四章刚补上的真实存储层脱节。

所以第五章现在默认把脚本切到：

> `--backend chroma`

这样你会直接在真实向量数据库上比较：

- similarity
- threshold
- MMR
- filename filter

### 4.3 当前代码里的两种 Retriever

当前主线里：

- [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
  提供 `SimpleRetriever`
- [chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)
  提供 `ChromaRetriever`

它们共享同一套：

- `RetrievalStrategyConfig`
- `SearchHit`
- `maximal_marginal_relevance()`
- `evaluate_bad_case()`

也就是说：

> 第五章把“策略逻辑”和“底层存储后端”拆开了，但没有把课程结构重新工程化。

---

## 5. 坏案例为什么现在必须变成 PASS / FAIL 📌

第五章现在的 [retrieval_bad_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json) 已经不只是“写几句期望”。

它现在至少覆盖：

1. `duplicate_refund_chunks`
2. `candidate_pool_for_mmr`
3. `metadata_scope`
4. `no_answer`

这些 case 的价值是：

- 让你不再只凭印象判断策略好坏
- 把策略调优变成最小可回归实验
- 让 `candidate_k / threshold / MMR / filter` 的作用都能落到机器可判定的现象上

---

## 6. 第五章实践：建议运行顺序

### 6.1 安装依赖

```bash
cd source/04_rag/05_retrieval_strategies
python -m pip install -r requirements.txt
```

### 6.2 先看原理层

```bash
python 01_compare_retrievers.py --backend json --reset
```

你应该先建立的直觉是：

- `top_k / candidate_k / threshold / MMR / filename_filter` 都属于 Retriever 层
- 不同策略的差异可以通过同一问题重复观察

### 6.3 再看真实 Chroma

```bash
python 01_compare_retrievers.py --backend chroma --reset
python 03_query_demo.py --backend chroma --strategy mmr --candidate-k 4 --mmr-lambda 0.35 "购买后多久还能退款？"
```

你应该观察到：

- 第四章的真实 Chroma 现在直接成了第五章的实验底座
- `MMR` 不是靠“多拿点结果”解决，而是靠“在候选池里做选择”

### 6.4 跑坏案例回归

```bash
python 02_review_bad_cases.py --backend chroma
```

你应该观察到：

- 输出里已经有明确的 `PASS / FAIL / INFO`
- `candidate_pool_for_mmr` 会显式体现 `candidate_k`
- `no_answer` 会显式体现 `threshold`
- `metadata_scope` 会显式体现 `filename_filter`

### 6.5 测试

```bash
python -m unittest discover -s tests
```

当前测试锁定两类路径：

1. JSON Retriever
2. Chroma Retriever

---

## 7. 本章学完后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么第五章应该复用第四章 store 契约，而不是再造一套 provider / store
- `top_k / candidate_k / threshold / MMR / filename_filter` 各自解决什么问题
- 为什么第五章现在默认要跑真实 Chroma
- 为什么坏案例回归应该开始变成可判定的最小实验

---

## 8. 下一章

第六章开始，你才会把当前 Retriever 输出接进 Prompt 和答案生成。

也就是说：

> 第五章解决的是“怎么查得更稳、更可控”，不是“怎么生成最终回答”。
