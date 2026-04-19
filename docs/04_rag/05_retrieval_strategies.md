# 05. 检索策略

> 本节目标：理解为什么向量库查询结果还不能直接等同于“好的检索”，跑通一个最小的 Retriever 闭环，并建立 `top_k / threshold / MMR / metadata filter` 分别在解决什么问题的判断。

---

## 1. 概述

### 学习目标

- 理解 Retriever 在 RAG 系统里的职责边界
- 理解为什么很多回答问题，根因其实在检索而不是 Prompt
- 掌握 `top_k / score_threshold / MMR / metadata filter` 的基本边界
- 能运行第五章脚本，并看出同一问题在不同策略下的差异
- 理解为什么坏案例记录会成为后续 RAG 优化的入口

### 预计学习时间

- Retriever 边界理解：30-40 分钟
- 基础检索参数：40-60 分钟
- 坏案例与策略对比：40-60 分钟

### 本章与前后章节的关系

第四章已经解决：

1. 向量如何被持久化存起来
2. 怎么做最小相似度查询
3. metadata 过滤和删除为什么重要

第五章接着解决：

1. 如何把底层查询收束成 Retriever
2. 如何控制召回数量、噪声和多样性
3. 检索失败时先从哪里排查

第六章会继续建立在这里之上：

1. 把 Retriever 返回的结果拼进 Prompt
2. 形成真正的 RAG Chain

### 本章代码入口

本章对应的代码目录是：

- [source/04_rag/05_retrieval_strategies/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/README.md)
- [retrieval_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- [01_compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/01_compare_retrievers.py)
- [02_review_bad_cases.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/02_review_bad_cases.py)
- [03_query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/03_query_demo.py)
- [evals/retrieval_bad_cases.json](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json)

### 本章边界

本章重点解决：

1. Retriever 的职责
2. 基础检索参数
3. 坏案例记录和分析
4. 什么时候只是调参数，什么时候才需要升级策略

本章不要求：

- 一次性把混合检索、Rerank、HyDE 都实现一遍
- 进入完整 Agent 级动态决策
- 把所有高级 Retriever 都做成生产级组件

为了保持章节独立，本章代码提供一个最小 `VectorStore + Retriever` 组合和固定样例 `EmbeddedChunk[]`。

目的不是绕开第四章，而是避免你为了学策略，又被工程骨架分散注意力。

---

## 2. Retriever 在系统里到底负责什么 📌

### 2.1 为什么不能把 Vector Store 直接当 Retriever

Vector Store 更偏基础设施层，负责：

- 存
- 查
- 删
- 过滤

Retriever 更偏应用层，负责：

- 接收用户问题
- 决定查询参数
- 决定返回多少结果
- 决定是否做阈值过滤或多样性控制
- 把结果整理成后续 Chain 能消费的统一接口

所以 Retriever 的本质不是“再包一层类”，而是：

> 把底层查询能力收束成稳定的应用侧检索接口。

### 2.2 为什么第五章不去重做第四章

第五章当前代码没有重做存储层，也没有重做 embedding。

它只是站在第四章之上继续长出这一层：

```text
question
-> Retriever config
-> Vector Store query
-> result filtering / diversification
-> RetrievalResult[]
```

这说明课程主线仍然是逐章增量，不是每章重来一遍。

### 2.3 为什么检索质量是 RAG 的核心变量

如果召回结果本身不对，后面 Prompt 写得再好，模型也只能在错误上下文里回答。

所以第五章要建立一个很重要的习惯：

> 先看召回结果，再看生成结果。

这也是为什么这一章开始正式引入坏案例记录。

---

## 3. 当前章节里有哪些基础策略 📌

### 3.1 similarity

这是最直接的策略：

- 拿 query vector 去查最相近的 chunk
- 按分数从高到低返回

它适合：

- 先确认系统基本能召回正确上下文
- 作为所有增强策略的对照基线

但它的问题也很典型：

- 容易带入低分尾部
- 容易把高度相似的 chunk 一起召回来

### 3.2 `score_threshold`

阈值过滤解决的是：

- 不让明显不相关的结果也进入上下文

它的价值主要在于：

- 控制噪声
- 更好地处理“无答案”场景
- 让系统更容易说“我不知道”，而不是强行在弱相关上下文里回答

### 3.3 MMR

MMR 的目标不是单纯找“最像”的结果，而是：

> 在相关性和多样性之间做平衡。

它更适合：

- 重复内容较多
- 希望上下文覆盖更多角度

### 3.4 metadata filter

metadata filter 适合：

- 只查某类文档
- 只查某个知识域
- 只查某个来源

它不是“高级技巧”，而是很多真实业务里非常常见的基本需求。

第五章把它放在 Retriever 配置里，是为了强调：

> 检索范围本身就是策略的一部分，不只是底层存储的附属参数。

---

## 4. 当前第五章代码具体怎么落地 📌

### 4.1 `RetrievalStrategyConfig`

[retrieval_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/retrieval_basics.py) 里现在有一个非常关键的对象：

- `strategy_name`
- `top_k`
- `candidate_k`
- `score_threshold`
- `mmr_lambda`
- `filename_filter`

这说明第五章的设计重点已经从“怎么查向量”转向了：

> 同一份底层数据，在应用层应该怎么组织检索策略。

### 4.2 `SimpleRetriever`

`SimpleRetriever` 当前负责：

1. 读取策略配置
2. 调用最小 Vector Store
3. 在 Retriever 层应用 threshold 或 MMR
4. 输出标准 `RetrievalResult[]`

这就是第五章真正新增的代码重心。

### 4.3 为什么 `candidate_k` 也重要

很多人只关注最终 `top_k`，但第五章把 `candidate_k` 单独保留出来，是因为：

- threshold 需要先有足够候选，才有东西可筛
- MMR 需要先有一批候选，才有空间做多样性选择

所以 `candidate_k` 的作用是：

> 控制“先召回多大范围，再在应用层做进一步策略处理”。

### 4.4 坏案例为什么要进 `evals/`

现在 [evals/retrieval_bad_cases.json](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json) 已经开始记录几类典型问题：

- 重复召回问题
- 范围控制问题
- 无答案问题

这一步很重要，因为后面的优化不是靠“感觉更好”，而是靠固定案例回归。

---

## 5. 检索效果差时先看什么 📌

第五章建议建立这个排查顺序：

1. 用户问题本身是否清晰
2. similarity 基线里有没有正确来源
3. 低分尾部是不是太多
4. 结果之间是不是高度重复
5. 检索范围是不是过宽或过窄
6. 最后才看 Prompt 和生成

这也是为什么当前脚本分成了三个入口：

- [01_compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/01_compare_retrievers.py)
  适合看同一问题在不同策略下的即时对比
- [02_review_bad_cases.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/02_review_bad_cases.py)
  适合固定案例回归
- [03_query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/03_query_demo.py)
  适合单独跑某一种策略

没有这三类入口，你很难回答：

- 现在到底是哪种失败
- 加一个策略到底有没有变好

---

## 6. 第五章实践：独立 Retriever 闭环

### 6.1 目录结构

本章代码目录是：

```text
source/04_rag/05_retrieval_strategies/
├── README.md
├── retrieval_basics.py
├── 01_compare_retrievers.py
├── 02_review_bad_cases.py
├── 03_query_demo.py
├── evals/
└── tests/
```

第五章保持和前几章一样的平铺目录。

这里不做：

- 生产级检索服务
- 多模块抽象
- 复杂框架集成

因为本章重点是理解检索策略，不是理解工程编排。

### 6.2 输入和输出

本章代码的输入是：

- 一个问题
- 一组固定样例 `EmbeddedChunk[]`
- 一份 `RetrievalStrategyConfig`

本章代码的输出是：

- `RetrievalResult[]`
- 各策略下的结果差异
- 坏案例回归输出

在 [retrieval_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/retrieval_basics.py) 里，你最值得先看的是：

- `RetrievalStrategyConfig`
- `InMemoryVectorStore`
- `SimpleRetriever`
- `maximal_marginal_relevance()`
- `average_redundancy()`
- `load_bad_cases()`

### 6.3 运行方式

```bash
cd source/04_rag/05_retrieval_strategies

python 01_compare_retrievers.py
python 01_compare_retrievers.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 02_review_bad_cases.py
python 03_query_demo.py --strategy similarity
python 03_query_demo.py --strategy threshold --threshold 0.60
python 03_query_demo.py --strategy mmr
python -m unittest discover -s tests
```

### 6.4 你应该观察到什么

跑 [01_compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/01_compare_retrievers.py) 时：

- similarity 是否会召回很多高度相似的退款块
- threshold 是否会截掉低分尾部
- MMR 是否会把一些重复结果往后压
- filename filter 是否会缩小结果来源范围

跑 [02_review_bad_cases.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/02_review_bad_cases.py) 时：

- 你会看到固定坏案例在不同策略下的行为差异
- 你会看到“无答案”“范围控制”“重复召回”应该分开判断

跑 [03_query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/03_query_demo.py) 时：

- 你会看到单一策略配置如何变成一次完整检索实验
- 你会看到 Retriever 返回的仍然是稳定的结构化结果

### 6.5 本章代码刻意简化了什么

这一章的实现刻意简化了四件事：

1. 只用固定样例 `EmbeddedChunk[]`
2. 只做本地最小 Vector Store
3. 不接混合检索和 Rerank
4. 不进入 Prompt 和生成

这是故意的。

因为本章要先把下面这件事学会：

> 第五章解决的是“怎么查得更好”，不是“怎么把整条 RAG 链都接完”。

---

## 7. 本章学完后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么很多问题应该先看检索再看 Prompt
- `top_k / threshold / MMR / filter` 各自解决什么问题
- 什么时候只是调参数就够，什么时候才值得升级到更复杂检索
- 为什么坏案例回归是检索优化的基本习惯

---

## 8. 下一章

第六章开始，你才会把当前 Retriever 输出接进 Prompt 和答案生成：

- 检索结果怎么拼进上下文
- 怎么要求模型引用来源
- 什么情况下应该拒答

也就是说，第六章处理的是“如何基于检索结果生成回答”。

第五章先把“查得更好”立住，就够了。
