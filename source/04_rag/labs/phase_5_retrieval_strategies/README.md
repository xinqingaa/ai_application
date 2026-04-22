# phase_5_retrieval_strategies - 旧版备份

> 迁移说明：第五章新的学习入口已经切换到 [source/04_rag/05_retrieval_strategies/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/README.md)。这个目录目前只作为迁移期备份保留，等前六章替换完成后会删除。

> 下面内容保留原样，方便对照旧结构，不再推荐作为第五章主入口。

---

## 核心原则

```text
先确认 Phase 4 已经能稳定返回相似度结果 -> 再看 Retriever 如何封装这些查询 -> 再对比 similarity / threshold / MMR / filter -> 最后用坏案例和测试验证策略边界
```

- 在 `source/04_rag/labs/phase_5_retrieval_strategies/` 目录下操作
- 这一章的重点不是“多写几个参数”，而是把向量库查询收束成稳定的应用侧检索接口
- 默认仍然用本地 `local_hash` embedding，所以没有 API Key 也能完整跑这一章
- 本章继续复用真实 Chroma，不重做向量库存储层

---

## 本章定位

- 对应章节：[05_retrieval_strategies.md](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md)
- 本章目标：把 Phase 4 的原始查询能力封装成 Retriever，并对比 `similarity / threshold / MMR / metadata filter`
- 上一章输入契约：稳定 Chroma collection、稳定 `EmbeddedChunk[]`、稳定 query/document embedding 入口
- 输出契约：真实 `ChromaRetriever`、可切换的检索策略、坏案例样例、可回归测试
- 本章新增：`app/retrievers/chroma.py`、`scripts/compare_retrievers.py`、`scripts/review_bad_cases.py`、`tests/test_retrievers.py`、`evals/retrieval_bad_cases.json`
- 本章可忽略：混合检索、Rerank、HyDE、完整生成链路
- 第一命令：`python scripts/compare_retrievers.py`

---

## 项目结构

```text
phase_5_retrieval_strategies/
├── README.md
├── requirements.txt
├── app/
│   ├── config.py
│   ├── retrievers/
│   │   ├── base.py
│   │   ├── __init__.py
│   │   └── chroma.py
│   ├── vectorstores/
│   └── ...
├── evals/
│   ├── README.md
│   └── retrieval_bad_cases.json
├── scripts/
│   ├── compare_retrievers.py
│   ├── review_bad_cases.py
│   └── query_demo.py
└── tests/
    ├── test_vectorstores.py
    └── test_retrievers.py
```

这一章真正新增的主角只有三块：

1. `app/retrievers/chroma.py`
2. `scripts/compare_retrievers.py / review_bad_cases.py / query_demo.py`
3. `tests/test_retrievers.py`

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/labs/phase_5_retrieval_strategies
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python scripts/index_chroma.py --reset
python scripts/compare_retrievers.py
python scripts/review_bad_cases.py
python scripts/query_demo.py --strategy similarity
python scripts/query_demo.py --strategy threshold --threshold 0.70
python scripts/query_demo.py --strategy mmr
python -m unittest discover -s tests
```

### 4. 先跑哪个

建议先跑：

```bash
python scripts/compare_retrievers.py
```

你现在最该先建立的直觉是：

- Vector Store 能查，不等于应用层就已经“检索做好了”
- `top_k / threshold / MMR / filter` 都应该归到 Retriever 层来管理
- 检索策略的对比要靠同一问题下的可重复实验，而不是凭印象

---

## 第 1 步：先确认第五章真正继承了什么

**对应文件**：`app/vectorstores/chroma_store.py`、`scripts/index_chroma.py`、`tests/test_vectorstores.py`

### 这一步要解决什么

- 第五章不是重做向量库，而是站在第四章真实 Chroma 之上继续长
- 当前 `phase_5` 只会调用 `similarity_search()`，不会改写存储层语义
- 第五章的每个策略都必须复用同一份 collection 和同一套 embedding

### 重点观察

- `ChromaVectorStore`
- `similarity_search()`
- `similarity_search_by_vector()`

---

## 第 2 步：看 Retriever 如何收束查询参数

**对应文件**：`app/retrievers/base.py`、`app/retrievers/chroma.py`

### 这一步要解决什么

- 为什么 Retriever 不应该直接等同于 Vector Store
- 为什么应用层需要一份独立的 `RetrievalStrategyConfig`
- 为什么第五章要在 Retriever 里处理 `candidate_k / score_threshold / mmr_lambda / metadata_filter`

### 重点观察

- `RetrievalStrategyConfig`
- `ChromaRetriever`
- `_apply_score_threshold()`
- `maximal_marginal_relevance()`

### 建议主动修改

- 改 `default_retrieval_score_threshold`
- 改 `default_retrieval_candidate_k`
- 改 `default_retrieval_mmr_lambda`

---

## 第 3 步：对比三种基础策略

**对应文件**：`scripts/compare_retrievers.py`

### 这一步要解决什么

- 为什么同一个问题在不同策略下会出现不同的上下文组合
- 为什么 `threshold` 更像噪声控制，而 `MMR` 更像多样性控制
- 为什么 metadata filter 不是“额外技巧”，而是检索边界的一部分

### 建议先跑

```bash
python scripts/compare_retrievers.py
python scripts/compare_retrievers.py "Where do we keep source path and chunk index metadata?"
python scripts/compare_retrievers.py "Where do we keep source path and chunk index metadata?" --filename product_overview.md
```

运行后重点看：

- similarity 是否会召回很多高度相似 chunk
- threshold 是否会截掉低分尾部
- MMR 是否会把一些重复结果往后压
- filename filter 是否会缩小结果来源范围

---

## 第 4 步：看坏案例如何帮助判断要不要升级策略

**对应文件**：`evals/retrieval_bad_cases.json`、`scripts/review_bad_cases.py`

### 这一步要解决什么

- 第五章为什么开始正式记录检索坏案例
- 为什么“无答案”“重复召回”“范围过宽”应该被区分开看
- 为什么后面要不要上混合检索或 Rerank，应该由坏案例驱动

### 建议先跑

```bash
python scripts/review_bad_cases.py
```

运行后重点看：

- 事实型问题时 threshold 会不会收缩到更干净的结果
- 重复上下文问题时 MMR 有没有打散结果
- 无答案问题时 threshold 能不能减少无关召回

---

## 第 5 步：看最小服务链路如何接入策略层

**对应文件**：`scripts/query_demo.py`、`app/services/rag_service.py`

### 这一步要解决什么

- 第五章虽然还没进入生成，但服务层已经不再依赖“随便一个查询器”
- `query_demo.py` 现在可以切换策略运行
- 第六章真正接 Prompt 和生成时，会直接吃到这里的 Retriever 输出

### 建议先跑

```bash
python scripts/query_demo.py --strategy similarity
python scripts/query_demo.py --strategy threshold --threshold 0.70
python scripts/query_demo.py --strategy mmr
```

---

## 第 6 步：最后看测试在锁定什么

**对应文件**：`tests/test_retrievers.py`

### 重点观察

- `test_similarity_retriever_returns_relevant_chunk()`
- `test_threshold_retriever_filters_out_low_score_tail()`
- `test_metadata_filter_applies_inside_retriever()`
- `test_mmr_reduces_redundancy_relative_to_similarity()`

测试现在锁定的不是“Retriever 类存在”，而是：

- similarity 能稳定返回相关结果
- threshold 会减少低分尾部
- metadata filter 真正作用在 Retriever 层
- MMR 的结果集平均冗余度低于纯 similarity

---

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. `app/config.py`
2. `app/retrievers/base.py`
3. `app/retrievers/chroma.py`
4. `scripts/compare_retrievers.py`
5. `evals/retrieval_bad_cases.json`
6. `scripts/review_bad_cases.py`
7. `scripts/query_demo.py`
8. `tests/test_retrievers.py`

## 建议主动修改的地方

1. 把 `default_retrieval_score_threshold` 调高或调低，再重新跑坏案例脚本。
2. 把 `default_retrieval_mmr_lambda` 改大或改小，观察 `MMR` 对结果排序的影响。
3. 给 `review_bad_cases.json` 再加一个你自己的问题，看它更像“无答案”“重复召回”还是“范围过宽”。

## 学完这一章后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么很多问题应该先看检索再看 Prompt
- `top_k / threshold / MMR / filter` 各自解决什么问题
- 什么时候只是调参数就够，什么时候才值得升级到混合检索或 Rerank

## 当前真实进度和下一章

- 当前真实进度：第五章已经交付可替换 Retriever 和基础策略实验，但还没有进入真正的生成链
- 完成标准：能稳定返回检索结果，能解释检索失败原因，能判断是否需要增强检索
- 下一章：把当前 Retriever 输出接进 Prompt 和答案生成，形成真正的 RAG Chain
