# 05. 检索策略

> 本节目标：理解为什么向量库查询结果还不能直接等同于“好的检索”，掌握 Retriever 的职责，以及 `top_k`、阈值、MMR、metadata filter 分别解决什么问题，并能对着第五章代码快照看清这些策略落在哪一层。

---

## 1. 概述

### 学习目标

- 理解 Retriever 在 RAG 系统里的职责边界
- 理解为什么很多回答问题，根因其实在检索而不是 Prompt
- 掌握 `top_k / score_threshold / MMR / metadata filter` 的基本边界
- 能运行第五章脚本，并看出同一问题在不同策略下的差异
- 理解为什么坏案例记录会成为后续 RAG 优化的入口

### 预计学习时间

- Retriever 边界理解：45 分钟
- 基础检索参数：1 小时
- 坏案例与策略对比：1 小时
- 第五章代码快照阅读：1-1.5 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| FAQ 问答 | similarity、`top_k` |
| 噪声控制 | `score_threshold` |
| 重复内容较多场景 | MMR |
| 多来源知识库 | metadata filter |
| RAG 优化 | “问题出在检索还是生成” 的判断能力 |

> **很多 RAG 效果问题，表面上看像模型回答差，实际上根因在检索。第五章就是建立这种定位能力。**

### 本章与前后章节的关系

第四章已经解决：

1. 向量如何写入真实 Chroma
2. 怎么做最小相似度查询
3. metadata 过滤和删除如何建立

第五章接着解决：

1. 如何把底层查询收束成 Retriever
2. 如何控制召回数量、噪声和多样性
3. 检索失败时先从哪里排查

第六章会继续建立在这里之上：

1. 把 Retriever 返回的结果拼进 Prompt
2. 形成真正的 RAG Chain

### 本章的学习边界

本章重点解决：

1. Retriever 的职责
2. 基础检索参数
3. 坏案例记录和分析
4. 什么时候只是调参数，什么时候才需要升级策略

本章不要求：

- 一次性把混合检索、Rerank、HyDE 都实现一遍
- 进入完整 Agent 级动态决策
- 把所有高级 Retriever 都做成生产级组件

### 当前代码快照

本章对应的代码快照是：

- [phase_5_retrieval_strategies/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/README.md)
- [app/retrievers/chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/chroma.py)
- [scripts/compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/compare_retrievers.py)
- [scripts/review_bad_cases.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/review_bad_cases.py)
- [tests/test_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/tests/test_retrievers.py)

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

### 2.2 为什么第五章不去改 Phase 4 的向量库

第五章当前代码没有重做 Chroma，也没有重做 embedding。

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

## 3. 当前代码里有哪些基础策略 📌

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
- 让 RAG 更容易说“我不知道”，而不是强行在弱相关上下文里回答

### 3.3 MMR

MMR 的目标不是单纯找“最像”的结果，而是：

> 在相关性和多样性之间做平衡。

当前 [app/retrievers/chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/chroma.py) 里的 `maximal_marginal_relevance()` 做的就是这件事：

1. 先拿到一批候选
2. 再根据 query 相关性和结果间相似度做重新选择

它更适合：

- 重复内容较多
- 希望上下文覆盖更多角度

### 3.4 metadata filter

metadata filter 适合：

- 只查某类文档
- 只查某个知识域
- 只查某个来源

它不是“高级技巧”，而是很多真实业务里非常常见的基本需求。

第五章现在把它放在 Retriever 配置里，是为了强调：

> 检索范围本身就是策略的一部分，不只是底层存储的附属参数。

---

## 4. 当前第五章代码具体怎么落地 📌

### 4.1 `RetrievalStrategyConfig`

[app/retrievers/chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/chroma.py) 里现在有一个非常关键的对象：

- `strategy_name`
- `candidate_k`
- `score_threshold`
- `mmr_lambda`
- `metadata_filter`

这说明第五章的设计重点已经从“怎么查向量”转向了：

> 同一份底层数据，在应用层应该怎么组织检索策略。

### 4.2 `ChromaRetriever`

`ChromaRetriever` 现在负责：

1. 读取策略配置
2. 调用 Phase 4 的 `ChromaVectorStore`
3. 在 Retriever 层应用 threshold 或 MMR
4. 输出标准 `RetrievalResult[]`

这就是第五章真正新增的代码重心。

### 4.3 为什么 `candidate_k` 也重要

很多人只关注最终 `top_k`，但第五章代码里把 `candidate_k` 单独保留出来，是因为：

- threshold 需要先有足够候选，才有东西可筛
- MMR 需要先有一批候选，才有空间做多样性选择

所以 `candidate_k` 的作用是：

> 控制“先召回多大范围，再在应用层做进一步策略处理”。

### 4.4 坏案例为什么要进 `evals/`

现在 [evals/retrieval_bad_cases.json](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/evals/retrieval_bad_cases.json) 已经不再是空占位。

它开始记录几类典型问题：

- 事实型问题
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

这也是为什么当前脚本分成了两个入口：

- [scripts/compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/compare_retrievers.py)
  适合看同一问题在不同策略下的即时对比
- [scripts/review_bad_cases.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/review_bad_cases.py)
  适合固定案例回归

没有这两类入口，你很难回答：

- 现在到底是哪种失败
- 加一个策略到底有没有变好

---

## 6. 第五章应该怎么学

### 6.1 推荐顺序

建议按这个顺序进入：

1. 先看 [app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/base.py)
2. 再看 [app/retrievers/chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/chroma.py)
3. 再跑 [scripts/compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/compare_retrievers.py)
4. 再看 [evals/retrieval_bad_cases.json](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/evals/retrieval_bad_cases.json)
5. 最后看 [tests/test_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/tests/test_retrievers.py)

### 6.2 建议先跑的命令

```bash
cd source/04_rag/labs/phase_5_retrieval_strategies
python scripts/index_chroma.py --reset
python scripts/compare_retrievers.py
python scripts/review_bad_cases.py
```

### 6.3 跑完后重点观察什么

- similarity 是否会召回很多高度相似 chunk
- threshold 是否会截掉低分尾部
- MMR 是否会把重复结果往后压
- metadata filter 是否会稳定缩小检索范围
- 无答案问题时 threshold 能不能减少噪声

### 6.4 测试在锁定什么

[tests/test_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/tests/test_retrievers.py) 现在锁定的是：

1. similarity 能稳定返回相关结果
2. threshold 会减少低分尾部
3. metadata filter 真正作用在 Retriever 层
4. MMR 的结果集平均冗余度低于纯 similarity

这说明第五章测试的重心已经从“能不能查”转向了“查得怎么样”。

---

### 6.5 坏案例怎么做策略对比实验

第五章最容易学虚的地方，是只记住参数名字，却没有形成实验顺序。

建议你固定同一个问题，按这个顺序对比：

1. 先跑 `similarity`
   先确认基线结果里有没有正确来源。
2. 再跑 `threshold`
   看它主要是在减少低分尾部，还是把正确结果也误删了。
3. 再跑 `MMR`
   看它是在打散重复内容，还是把真正最相关结果压得太后。
4. 最后加 `metadata filter`
   看问题到底是“语义匹配差”，还是“检索范围本来就太宽”。

如果你每次都同时改 `top_k / threshold / MMR / filter`，第五章就会变成凭感觉调参，而不是建立可复现的检索判断能力。

---

## 7. 综合案例：检索失败时该先改哪里

```python
# 你发现一个问题：
# 用户问“企业版支持哪些 SSO 接入方式？”
# 系统回答很模糊，来源也不准。
#
# 请回答：
# 1. 先看检索还是先改 Prompt？
# 2. Top-K 结果里如果没有正确 chunk，应该先调哪些东西？
# 3. 如果召回结果全是相似重复内容，为什么可以考虑 MMR？
# 4. 什么情况下才值得进一步上混合检索或 Rerank？
```

---

## 8. 本章实施步骤应该怎么理解 📌

第五章的正确顺序不是“先上高级策略”，而是：

| 步骤 | 先做什么 | 主要落在哪些模块 | 这一步在解决什么 |
|------|----------|------------------|------------------|
| 1 | 先确认 Phase 4 的相似度查询已经稳定 | `app/vectorstores/`、`scripts/index_chroma.py` | 避免把存储层问题误判成策略问题 |
| 2 | 定义应用层检索配置对象 | `app/retrievers/base.py`、`app/retrievers/chroma.py` | 让策略参数有统一入口和统一默认值 |
| 3 | 先建立 similarity 基线 | `ChromaRetriever`、`scripts/compare_retrievers.py` | 先知道“默认检索”长什么样 |
| 4 | 再分别加 threshold / MMR / filter | `app/retrievers/chroma.py` | 把噪声控制、多样性控制、范围控制拆开验证 |
| 5 | 用坏案例做回归 | `evals/retrieval_bad_cases.json`、`scripts/review_bad_cases.py` | 让策略优化不只靠主观感觉 |
| 6 | 用测试锁定预期行为 | `tests/test_retrievers.py` | 避免第五章一边调策略，一边把原有正确行为调坏 |

---

## 9. 本章代码映射表

| 文档部分 | 对应代码/文档 | 角色 | 说明 |
|----------|---------------|------|------|
| 本章第一阅读入口 | [phase_5_retrieval_strategies/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/README.md) | 主入口 | 先理解第五章新增模块、实验顺序和策略边界 |
| Retriever 抽象入口 | [app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/base.py) | 核心抽象 | 定义应用层检索接口和通用约定 |
| 策略实现 | [app/retrievers/chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/chroma.py) | 核心实现 | 收束 `similarity / threshold / MMR / metadata filter` |
| 即时对比入口 | [scripts/compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/compare_retrievers.py) | 主示例文件 | 对比同一问题在不同策略下的召回差异 |
| 坏案例回归入口 | [scripts/review_bad_cases.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/review_bad_cases.py) | 扩展示例 | 用固定坏案例回归策略行为 |
| 最小链路演示 | [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/query_demo.py) | 链路示例 | 观察策略切换后服务层收到的上下文差异 |
| 坏案例资产 | [evals/retrieval_bad_cases.json](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/evals/retrieval_bad_cases.json) | 评估资产 | 记录事实型、重复召回、范围控制、无答案等问题 |
| 验收入口 | [tests/test_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/tests/test_retrievers.py) | 核心测试 | 锁定不同策略下的预期检索行为 |

---

## 10. 实践任务

1. 跑一次 [scripts/compare_retrievers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/scripts/compare_retrievers.py)，解释为什么第五章不能把 Vector Store 直接当 Retriever。
2. 对照 [app/retrievers/chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/chroma.py)，说清 `candidate_k / score_threshold / mmr_lambda / metadata_filter` 各自解决什么问题。
3. 选一个容易重复召回的问题，分别跑 similarity 和 MMR，比较结果集的重复度差异。
4. 选一个“无答案”问题，分别跑 similarity 和 threshold，观察 threshold 是否减少了低分噪声。
5. 给 [evals/retrieval_bad_cases.json](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_5_retrieval_strategies/evals/retrieval_bad_cases.json) 自己增加一个坏案例，判断它更像“范围过宽”“重复召回”还是“本来就无答案”。

---

## 11. 完成标准

完成这一章后，至少应满足：

- 能解释为什么 Vector Store 和 Retriever 最好继续拆层
- 能说明为什么很多 RAG 质量问题应该先看检索再看 Prompt
- 能区分 `top_k / threshold / MMR / metadata filter` 的职责边界
- 能运行策略对比脚本、坏案例脚本和测试，并读懂差异
- 能判断一个问题只是调参数就够，还是已经值得升级到混合检索或 Rerank
- 能把第五章看成“检索行为优化层”，而不是新的向量库存储层

---

## 12. 小结

第五章真正建立的是：

> 把第四章“能查”这件事，升级成“知道该怎么查得更好”的应用层能力。

你要记住的主线有 5 条：

1. similarity 是基线，不是终点。
2. threshold 主要解决低分尾部和无答案噪声问题。
3. MMR 主要解决重复召回和上下文覆盖不足问题。
4. metadata filter 不是附属参数，而是检索范围控制的一部分。
5. 坏案例记录和测试回归，是第五章从“调参感觉”升级到“工程优化”的关键。
