# 05. 检索策略

> 本节目标：理解为什么第四章的向量查询结果还不能直接等同于“好的检索”，跑通一个最小的 Retriever 闭环，并建立 `top_k / candidate_k / score_threshold / MMR / filename filter` 分别在解决什么问题的判断。

---

## 1. 概述

### 学习目标

- 理解 Retriever 在 RAG 系统里的职责边界
- 理解为什么很多回答问题，根因其实在检索而不是 Prompt
- 看懂第五章如何继续站在第四章的 `PersistentVectorStore + EmbeddingSpace` 契约之上
- 掌握 `top_k / candidate_k / score_threshold / MMR / filename filter` 的基本边界
- 能运行第五章脚本，并解释坏案例回归为什么要变成可判定的 `PASS / FAIL`

### 预计学习时间

- Retriever 边界理解：30-40 分钟
- 基础检索参数：40-60 分钟
- 坏案例与策略对比：40-60 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 第五章先解决什么 |
|------|------------------|
| 基础 Top-K 查询之后 | 为什么还需要 Retriever 层而不是直接把 store 暴露给业务 |
| 上下文控制 | `top_k / candidate_k / threshold` 怎么影响噪声和覆盖范围 |
| 重复内容较多 | 为什么要引入 MMR 而不只是继续拉高 `top_k` |
| 范围约束 | 为什么 `filename` 过滤应进入策略配置，而不是散在脚本里 |
| 评估与调优 | 为什么坏案例不能只靠人工观察，而要开始有最小可判定回归 |

### 本章与前后章节的关系

第四章已经解决：

1. 向量如何被持久化存起来
2. 怎么做最小相似度查询
3. query 和 store 必须保持同一 embedding space
4. `filename` 过滤和 `document_id` 删除 / 替换为什么重要

第五章接着解决：

1. 如何把底层查询收束成 Retriever
2. 如何控制召回数量、噪声和多样性
3. 检索失败时先从哪里排查
4. 坏案例回归怎样开始变成可重复实验

第六章会继续建立在这里之上：

1. 把 Retriever 返回的结果拼进 Prompt
2. 形成真正的 RAG Chain

### 第五章与第四章的连续性

第五章不应该重新发明一套 provider、chunk 或 store。

当前代码改成了下面这条连续路径：

```text
chapter 4 SourceChunk / EmbeddedChunk / PersistentVectorStore
-> chapter 5 RetrievalStrategyConfig / SimpleRetriever
-> RetrievalResult[]
```

也就是说，第五章真正新增的是策略层，而不是再次重写：

- `SourceChunk`
- `EmbeddedChunk`
- `LocalKeywordEmbeddingProvider`
- `PersistentVectorStore`

本章会复用第四章已经立住的边界：

- 单一 `provider / model / dimensions` 空间
- richer metadata
- `filename`-only filter
- 持久化 store 作为底层数据源

### 本章代码入口

本章对应的代码目录是：

- [../../source/04_rag/05_retrieval_strategies/README.md](../../source/04_rag/05_retrieval_strategies/README.md)
- [../../source/04_rag/05_retrieval_strategies/retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- [../../source/04_rag/05_retrieval_strategies/01_compare_retrievers.py](../../source/04_rag/05_retrieval_strategies/01_compare_retrievers.py)
- [../../source/04_rag/05_retrieval_strategies/02_review_bad_cases.py](../../source/04_rag/05_retrieval_strategies/02_review_bad_cases.py)
- [../../source/04_rag/05_retrieval_strategies/03_query_demo.py](../../source/04_rag/05_retrieval_strategies/03_query_demo.py)
- [../../source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json)

### 本章边界

本章重点解决：

1. Retriever 的职责
2. 基础检索参数
3. MMR 多样性控制
4. `filename` 范围约束
5. 坏案例记录和最小可判定回归

本章不要求：

- 一次性把混合检索、Rerank、HyDE 都实现一遍
- 做通用 metadata filter DSL
- 进入完整 Agent 级动态决策
- 把所有高级 Retriever 做成生产级组件

这一章的目标不是把检索工程做完，而是把下面这件事学会：

> 第五章解决的是“怎么查得更稳、更可控”，不是“怎么把整条 RAG 链都接完”。

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
- 决定返回多少结果
- 决定是否做阈值过滤或多样性控制
- 把结果整理成后续 Chain 能消费的统一接口

所以 Retriever 的本质不是“再包一层类”，而是：

> 把底层查询能力收束成稳定的应用侧检索接口。

### 2.2 第五章到底新增了什么

第五章当前代码没有重做第四章的 chunk 或 store。

真正新增的是：

```text
question
-> Retriever config
-> load EmbeddedChunk[] from chapter 4 store
-> strategy selection
-> RetrievalResult[]
```

也就是说，第五章真正交付的是：

- `RetrievalStrategyConfig`
- `SimpleRetriever`
- `maximal_marginal_relevance()`
- 最小 bad-case regression

### 2.3 为什么检索质量是 RAG 的核心变量

如果召回结果本身不对，后面 Prompt 写得再好，模型也只能在错误上下文里回答。

所以第五章要建立一个很重要的习惯：

> 先看召回结果，再看生成结果。

这也是为什么这一章开始把坏案例从“看一眼输出”推进到“至少有最小可判定回归”。

---

## 3. 当前章节里有哪些基础策略 📌

### 3.1 similarity

这是最直接的策略：

- 拿 query vector 去查最相近的 chunk
- 按相似度从高到低返回

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

要注意一件事：

> threshold 没有跨模型通用的最佳值。

当前第五章 demo 复用了第四章的 embedding space，因此默认阈值基线改成了 `0.80`，而不是旧实现里的 `0.60`。

### 3.3 `candidate_k`

很多人只关注最终 `top_k`，但 `candidate_k` 同样重要：

- threshold 需要先有足够候选，才有东西可筛
- MMR 需要先有一批候选，才有空间做多样性选择

所以 `candidate_k` 的作用是：

> 先控制候选范围，再在 Retriever 层做进一步选择。

### 3.4 MMR

MMR 的目标不是单纯找“最像”的结果，而是：

> 在相关性和多样性之间做平衡。

它更适合：

- 重复内容较多
- 希望上下文覆盖更多角度

要注意当前脚本里的一个细节：

> MMR 输出时展示的 `score` 仍然是 similarity score，不是内部 MMR selection score。

也就是说：

- 显示分数用来帮助你看相关性强弱
- 选择顺序来自 MMR 的多样性算法

### 3.5 当前过滤边界是什么

第五章当前确实支持过滤，但要说准确：

> 当前最小实现只支持 `filename_filter`，不是通用 metadata filter DSL。

这一点和第四章保持一致。

所以文档里如果说“按来源、知识域、租户自由过滤”，那就是把实现说强了。

---

## 4. 当前第五章代码具体怎么落地 📌

### 4.1 `RetrievalStrategyConfig`

[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py) 里最关键的策略对象是：

- `strategy_name`
- `top_k`
- `candidate_k`
- `score_threshold`
- `mmr_lambda`
- `filename_filter`

这说明第五章的重心已经从“怎么存向量”转向：

> 同一份底层数据，在应用层应该怎么组织检索策略。

### 4.2 `SimpleRetriever`

`SimpleRetriever` 当前负责：

1. 把用户问题变成 query vector
2. 从第四章 store 里读取标准 `EmbeddedChunk[]`
3. 校验 query 和 stored vectors 是否属于同一 embedding space
4. 在 Retriever 层应用 `candidate_k / threshold / MMR / filename_filter`
5. 输出标准 `RetrievalResult[]`

第五章真正新增的代码重心就在这里。

### 4.3 为什么 demo store 仍然存在

第五章当前仍然保留一个本章目录下的 demo store 文件：

`source/04_rag/05_retrieval_strategies/store/demo_retrieval_store.json`

但它的职责已经变了：

- 不再定义新的 store 契约
- 只是为了让策略对比有一份固定、可重复的样例索引

脚本运行时会用固定 demo corpus 重建这份 store，目的是保证策略实验可重复。

### 4.4 坏案例为什么要进 `evals/`

现在 [retrieval_bad_cases.json](../../source/04_rag/05_retrieval_strategies/evals/retrieval_bad_cases.json) 已经不只是“写几句期望”。

它开始包含最小 machine-checkable assertions，例如：

- `top_chunk_id`
- `count`
- `empty`
- `filename`
- `must_include_chunk_ids`

这一步很重要，因为后面的优化不应该只靠“感觉更好”，而要开始能回答：

- 哪个策略通过了
- 哪个策略失败了
- 它失败在哪个检查点

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

- [01_compare_retrievers.py](../../source/04_rag/05_retrieval_strategies/01_compare_retrievers.py)
  适合看同一问题在不同策略下的即时对比
- [02_review_bad_cases.py](../../source/04_rag/05_retrieval_strategies/02_review_bad_cases.py)
  适合固定案例回归，并直接输出 `PASS / FAIL / INFO`
- [03_query_demo.py](../../source/04_rag/05_retrieval_strategies/03_query_demo.py)
  适合单独跑某一种策略

没有这三类入口，你很难回答：

- 现在到底是哪种失败
- 加一个策略到底有没有变好

---

## 6. 第五章实践：独立 Retriever 闭环

### 6.1 目录结构

```text
source/04_rag/05_retrieval_strategies/
├── README.md
├── retrieval_basics.py
├── 01_compare_retrievers.py
├── 02_review_bad_cases.py
├── 03_query_demo.py
├── evals/
├── store/
└── tests/
```

第五章保持和前几章一样的平铺目录。

这里不做：

- 生产级检索服务
- 通用 Retriever 注册体系
- 混合检索和 Rerank
- Prompt 和答案生成

### 6.2 输入和输出

本章代码的输入是：

- 一个问题
- 一份固定 demo corpus
- 一份 `RetrievalStrategyConfig`

本章代码的输出是：

- `RetrievalResult[]`
- 各策略下的结果差异
- bad-case regression 的 `PASS / FAIL / INFO`

在 [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py) 里，你最值得先看的是：

- `demo_source_chunks()`
- `build_demo_store()`
- `RetrievalStrategyConfig`
- `SimpleRetriever`
- `maximal_marginal_relevance()`
- `evaluate_bad_case()`

### 6.3 运行方式

```bash
cd source/04_rag/05_retrieval_strategies

python 01_compare_retrievers.py
python 01_compare_retrievers.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 02_review_bad_cases.py
python 03_query_demo.py --strategy similarity
python 03_query_demo.py --strategy threshold --threshold 0.80 "火星首都是什么？"
python 03_query_demo.py --strategy mmr
python -m unittest discover -s tests
```

测试命令不是本章重点，但可以作为辅助验证。

### 6.4 你应该观察到什么

跑 [01_compare_retrievers.py](../../source/04_rag/05_retrieval_strategies/01_compare_retrievers.py) 时：

- similarity 会召回多条非常接近的退款规则
- threshold 会在默认示例里截掉一部分低分尾部
- MMR 会更容易带出流程类 chunk，而不是只保留重复规则
- `filename` filter 会明显缩小结果范围

当前 compare 脚本会把 threshold 设成 `0.88`，目的是让“截尾”效果更容易被观察到。

跑 [02_review_bad_cases.py](../../source/04_rag/05_retrieval_strategies/02_review_bad_cases.py) 时：

- 你会看到固定坏案例在不同策略下的行为差异
- 你会看到哪些策略有明确断言，哪些暂时只是信息输出
- 你会看到 `PASS / FAIL / INFO` 已经开始替代纯人工观察

跑 [03_query_demo.py](../../source/04_rag/05_retrieval_strategies/03_query_demo.py) 时：

- 你会看到单一策略配置如何变成一次完整检索实验
- 你会看到 Retriever 返回的仍然是稳定的结构化结果
- 如果策略是 MMR，脚本会明确提示“显示分数是 similarity score”

### 6.5 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. 只用固定 demo corpus
2. 只支持 `filename_filter`
3. 不做混合检索和 Rerank
4. 只保留最小 bad-case regression
5. 不进入 Prompt 和生成

这是故意的。

因为本章真正要先学会的是：

> 第五章解决的是“怎么查得更好”，不是“怎么把整条 RAG 链都接完”。

### 6.6 这一章值得刻意观察的失败案例

第五章至少要刻意观察三类失败：

1. 重复召回

similarity 把多条几乎相同的规则一起带回来，说明单纯拉 `top_k` 不够。

2. 无答案场景

如果一个明显无答案的问题仍然带回多条弱相关结果，说明需要 threshold。

3. 范围约束失败

如果你明明只想看 `metadata_rules.md`，结果却召回了别的文件，说明范围控制没有进 Retriever 配置。

这些失败都不是“体验细节”，而是后面 Prompt 和生成是否稳定的前置条件。

---

## 7. 本章学完后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么第五章应该复用第四章的 store 契约，而不是再造一套 provider / store
- `top_k / candidate_k / threshold / MMR / filename_filter` 各自解决什么问题
- 为什么当前第五章只支持 `filename` 过滤
- 为什么坏案例回归应该开始变成可判定的最小实验

---

## 8. 下一章

第六章开始，你才会把当前 Retriever 输出接进 Prompt 和答案生成：

- 检索结果怎么拼进上下文
- 怎么要求模型引用来源
- 什么情况下应该拒答

也就是说，第六章处理的是“如何基于检索结果生成回答”。

第五章先把“查得更稳、更可控、更可回归”立住，就够了。
