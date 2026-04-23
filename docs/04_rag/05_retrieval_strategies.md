# 05. 检索策略

> 本章目标：把第四章的“能查”推进到第五章的“查得稳、查得可控、查得可评估”。你会先掌握基础 Retriever 策略，再理解混合检索与两阶段检索，最后用一个最小 `SmartRetrievalEngine` 把这些能力收束成统一接口。

---

## 1. 概述

### 学习目标

- 理解 Retriever 和 Vector Store 的职责边界
- 掌握 `similarity / threshold / mmr` 的行为差异
- 理解 `top_k / candidate_k(fetch_k) / score_threshold / filename_filter` 的作用
- 学会用坏案例和固定评估集验证检索策略，而不是只看主观印象
- 理解混合检索（BM25 + 向量）和两阶段检索（Rerank）的价值
- 了解 Query 变换、上下文压缩、高级 Retriever 的边界
- 能跑通本章代码，并解释为什么综合案例要把多种策略统一到一个检索引擎里

### 本章与前后章节的关系

第四章已经解决：

1. 文本如何变成向量
2. 向量如何进入 JSON / Chroma 存储
3. query 和 store 必须保持同一 embedding space
4. 如何做最小相似度查询

第五章继续解决：

1. 如何把底层查询收束成 Retriever
2. 如何控制召回数量、噪声和多样性
3. 如何引入关键词检索、两阶段精排和固定评估
4. 如何把多种检索策略收敛成统一应用接口

第六章才继续解决：

1. 把 Retriever 返回结果拼进 Prompt
2. 形成真正的 RAG Chain

### 当前代码入口

- [README.md](../../source/04_rag/05_retrieval_strategies/README.md)
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

### 本章边界

本章重点解决：

1. 基础检索参数和召回行为
2. MMR 多样性控制
3. `filename_filter` 范围约束
4. 坏案例回归
5. 检索评估指标：`Recall@K / MRR / Hit Rate`
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

---

## 2. 基础检索（对应大纲第 13 节） 📌

### 2.1 为什么 Vector Store 不能直接等同于 Retriever

第四章的 Vector Store 更偏基础设施层，负责：

- 存
- 查
- 删
- 保证 embedding space 一致
- 保留 chunk 和 metadata 身份

Retriever 更偏应用层，负责：

- 接收用户问题
- 设定查询策略
- 决定召回数量
- 决定是否做阈值过滤、多样性控制、范围过滤
- 把结果整理成后续链路能直接消费的统一接口

这就是为什么第五章新增的是策略层，而不是再次重写 chunk、provider 或 store。

### 2.2 基础检索方式

本章当前最核心的三种基础策略是：

1. `similarity`
   直接按相似度从高到低返回结果
2. `threshold`
   先按相似度召回，再用阈值切掉弱相关尾部
3. `mmr`
   在候选池里同时考虑相关性和多样性，减少重复内容

对应代码：

- JSON 路径：[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- Chroma 路径：[chroma_retriever.py](../../source/04_rag/05_retrieval_strategies/chroma_retriever.py)

### 2.3 基础检索参数

#### `top_k`

- 最终进入上下文的结果数
- 太小容易漏信息
- 太大容易带入噪声和冗余

#### `candidate_k`

- 候选池大小
- 先决定“给 Retriever 多大选择空间”，再由 `threshold` 或 `mmr` 进一步筛选
- 在大纲语义里，它对应常见框架里的 `fetch_k`

#### `score_threshold`

- 用于处理弱相关尾部和“无答案”问题
- 没有跨模型通用的最佳阈值
- 当前 demo 默认值是 `0.80`，只对本章的 toy embedding space 有意义

#### `filename_filter`

- 本章当前最小实现只支持按 `filename` 过滤
- 这是教学用最小 metadata filter，不是完整 DSL

### 2.4 基础检索评估

第五章不再只看“结果看起来像不像对”，而要开始固定评估口径。

本章当前使用三类最小指标：

1. `Recall@K`
   期望 chunk 里有多少被召回
2. `MRR`
   第一个正确结果排得有多靠前
3. `Average Redundancy`
   结果之间彼此有多像，用来观察 MMR 是否减少冗余

其中：

- `Recall@K / MRR / Hit Rate` 放在 [retrieval_metrics.py](../../source/04_rag/05_retrieval_strategies/retrieval_metrics.py)
- `Average Redundancy` 放在 [retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)

### 2.5 基础检索实践映射

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

## 3. 高级检索策略（对应大纲第 14 节）

### 3.1 Query 变换策略

这些策略的共同目标是：

> 不直接拿原始问题去检索，而是先把查询改写成更有利于召回的形式。

#### Multi-Query

- 让 LLM 生成多个相关查询
- 合并多次检索结果
- 适合用户问题表达不稳定、同义说法很多的场景

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
- 再结合原问题做精确检索
- 适合细节问题依赖大背景时

### 3.2 上下文压缩

上下文压缩不是“再查一次”，而是：

- 先召回更大候选集
- 再从结果中裁掉无关句段
- 尽量减少噪声和 token 浪费

这一能力本章只做概念认知，不做本地实现主线。

### 3.3 混合检索

纯向量检索擅长语义相似，但容易漏精确关键词。

纯关键词检索擅长匹配编号、术语、专有名词，但容易缺少语义泛化。

所以混合检索要解决的问题是：

> 把 BM25 的精确匹配能力和向量检索的语义匹配能力组合起来。

当前代码里的最小实现：

- BM25 scorer：[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- 混合检索 demo：[04_hybrid_retrieval.py](../../source/04_rag/05_retrieval_strategies/04_hybrid_retrieval.py)

当前 demo 用的是：

```text
hybrid_score = alpha * normalized_vector_score
             + (1 - alpha) * normalized_bm25_score
```

其中：

- `alpha` 越大，越偏向语义相似
- `alpha` 越小，越偏向关键词匹配

运行示例：

```bash
python 04_hybrid_retrieval.py --backend chroma --reset
python 04_hybrid_retrieval.py "退费申请流程" --backend chroma --alpha 0.3
```

### 3.4 这一节的边界

Query 变换和上下文压缩在本章只做概念认知，目的是先让你知道：

- 它们和基础 Retriever 是同一层面的“检索优化”
- 但它们引入 LLM 调用、额外依赖和更高复杂度
- 所以不适合作为第五章主线的默认实现

---

## 4. Rerank 重排序（对应大纲第 15 节） 📌

### 4.1 为什么需要 Rerank

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

### 4.2 真实世界里的 Rerank 模型

常见路线包括：

- Cohere Rerank API
- `BAAI/bge-reranker-large`
- ColBERT 一类 late interaction 模型

本章为了保持零额外依赖，只实现了一个教学用 `SimpleCrossReranker`。

它不追求真实效果，只负责把“两阶段检索”这个架构讲清楚。

### 4.3 当前代码实现

- toy reranker：[retrieval_basics.py](../../source/04_rag/05_retrieval_strategies/retrieval_basics.py)
- 单主题 demo：[05_rerank_demo.py](../../source/04_rag/05_retrieval_strategies/05_rerank_demo.py)

运行示例：

```bash
python 05_rerank_demo.py --backend chroma --reset
python 05_rerank_demo.py "购买后多久还能退款？" --backend chroma --fetch-k 6 --top-n 3
```

你应该观察：

- 第一阶段 `fetch_k` 要大于最终 `top_n`
- Rerank 只在候选池内部重排，不会凭空创造新结果
- 如果候选池本身就错了，Rerank 也救不回来

---

## 5. 高级 Retriever（选读，对应大纲第 16 节）

这一节不要求你现在就实现，而是让你知道在什么场景下，基础方案不够用了。

### 5.1 Self-Query Retriever

- 让 LLM 把自然语言问题拆成“语义查询 + metadata filter”
- 适合 metadata 丰富的知识库
- 代价是更依赖 schema 和 prompt 设计

### 5.2 Parent Document Retriever

- 检索时用小块提高召回
- 返回时回到父文档降低碎片化
- 适合切块后语义被打散的长文档

### 5.3 Multi-Vector Retriever

- 同一文档保存多种向量表示
- 标题、摘要、正文可以分别建索引
- 适合多视角表达差异明显的内容

### 5.4 什么时候值得上高级 Retriever

- 基础相似度检索已经稳定
- metadata 足够丰富
- 业务允许更高的构建和维护成本
- 你已经有固定评估集，知道新复杂度到底带来了多少收益

---

## 6. 综合案例：智能检索引擎

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

这个综合案例当前目标是：

1. 支持 `similarity / threshold / mmr / hybrid`
2. 支持可选 `rerank`
3. 支持 `filename_filter`
4. 支持固定测试集评估
5. 统一 JSON 和 Chroma 两条后端路径

### 6.1 统一引擎为什么重要

如果没有统一引擎，你会很快落入这种状态：

- `01` 是基础对比
- `04` 是混合检索
- `05` 是 rerank
- 但业务代码不知道到底应该调哪个入口

所以综合案例真正解决的是：

> 把“多个检索实验脚本”收束成“一个可复用应用接口”。

### 6.2 运行示例

```bash
python 06_smart_retrieval_engine.py "退费申请流程" --backend chroma --strategy hybrid
python 06_smart_retrieval_engine.py "购买后多久还能退款？" --backend chroma --strategy hybrid --rerank --fetch-k 6
python 06_smart_retrieval_engine.py --backend chroma --strategy hybrid --rerank --evaluate
```

### 6.3 当前综合案例的边界

当前仍然只是教学最小实现，不包括：

- 结果缓存
- 自适应策略选择
- A/B 测试平台
- 真实 cross-encoder reranker

但它已经足够把第五章的核心能力收束起来。

---

## 7. 建议运行顺序

### 7.1 先看基础策略

```bash
python 01_compare_retrievers.py --backend json --reset
python 01_compare_retrievers.py --backend chroma --reset
python 02_review_bad_cases.py --backend chroma
```

### 7.2 再看单项增强

```bash
python 04_hybrid_retrieval.py --backend chroma --reset
python 05_rerank_demo.py --backend chroma --reset
```

### 7.3 最后跑统一引擎

```bash
python 06_smart_retrieval_engine.py --backend chroma --strategy hybrid --rerank --evaluate
```

### 7.4 测试

```bash
python -m unittest discover -s tests
```

---

## 8. 本章学完后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- `top_k / candidate_k / threshold / filename_filter / MMR` 各自解决什么问题
- 为什么坏案例和固定评估集必须同时存在
- 为什么混合检索和 Rerank 都应该建立在基础 Retriever 之上
- 为什么综合案例需要一个统一检索引擎，而不是继续堆更多独立脚本

---

## 9. 下一章

第六章开始，你才会把本章的 Retriever 输出真正拼进 Prompt 和生成链路。

也就是说：

> 第五章解决的是“怎么查得更稳、更可控、更可评估”，不是“怎么生成最终答案”。
