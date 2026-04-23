# 05. 检索策略 - 实践指南

> 这份 README 负责把第五章跑通为一个完整章节：先理解基础 Retriever，再观察 hybrid 和 rerank，最后进入统一的 `SmartRetrievalEngine`。

---

## 核心原则

```text
先看基础 Retriever -> 再看 hybrid / rerank -> 最后用统一引擎和评估把能力收束
```

- 在 `source/04_rag/05_retrieval_strategies/` 目录下操作
- 本章只讲检索层，不讲 Prompt 和生成
- 第五章不会再重写 provider 或 store，而是直接复用第四章的对象与向量空间
- `chroma_retriever.py` 是从旧 `phase_5` 扁平化提炼出来的真实实践层
- `hybrid` 和 `rerank` 不再是附录 demo，而是第五章正式内容

---

## 项目结构

```text
05_retrieval_strategies/
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
├── store/
│   ├── .gitignore
│   ├── demo_retrieval_store.json
│   └── chroma/
└── tests/
    ├── test_retrievers.py
    ├── test_chroma_retrievers.py
    ├── test_retrieval_metrics.py
    └── test_smart_retrieval_engine.py
```

- `retrieval_basics.py`
  放第五章共享基础策略层：策略配置、JSON retriever、MMR、BM25、toy reranker、demo store 构建
- `chroma_retriever.py`
  放第五章真实 `ChromaRetriever`
- `retrieval_metrics.py`
  放固定评估集与 `Recall@K / MRR / Hit Rate` 计算
- `smart_retrieval_engine.py`
  放统一检索引擎：`similarity / threshold / mmr / hybrid + optional rerank`
- `01_compare_retrievers.py`
  对比同一问题在不同策略和不同 backend 下的差异
- `02_review_bad_cases.py`
  用固定坏案例跑最小 `PASS / FAIL / INFO` 回归
- `03_query_demo.py`
  用单一策略跑一次完整检索实验
- `04_hybrid_retrieval.py`
  单独观察 BM25、向量检索和混合检索的差异
- `05_rerank_demo.py`
  单独观察两阶段检索和 Rerank 重排
- `06_smart_retrieval_engine.py`
  从统一引擎入口运行检索和评估

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/05_retrieval_strategies
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python 01_compare_retrievers.py --backend json --reset
python 01_compare_retrievers.py --backend chroma --reset
python 01_compare_retrievers.py "为什么 metadata 很重要？" --backend chroma --filename metadata_rules.md
python 02_review_bad_cases.py --backend chroma
python 03_query_demo.py --backend chroma --strategy similarity
python 03_query_demo.py --backend chroma --strategy threshold --threshold 0.80 "火星首都是什么？"
python 03_query_demo.py --backend chroma --strategy mmr --candidate-k 4
python 04_hybrid_retrieval.py --backend chroma --alpha 0.3 "退费申请流程"
python 05_rerank_demo.py --backend chroma --fetch-k 6 --top-n 3
python 06_smart_retrieval_engine.py --backend chroma --strategy hybrid --rerank --evaluate
python -m unittest discover -s tests
```

---

## 建议学习顺序

### 第 1 步：先跑 JSON 原理层

```bash
python 01_compare_retrievers.py --backend json --reset
```

你最先要建立的直觉是：

- Vector Store 能查，不等于应用层就已经“检索做好了”
- `top_k / candidate_k / threshold / MMR / filename_filter` 都归 Retriever 层管理
- 检索策略对比要靠同一问题下的可重复实验，而不是凭印象

### 第 2 步：再跑真实 Chroma

```bash
python 01_compare_retrievers.py --backend chroma --reset
python 03_query_demo.py --backend chroma --strategy mmr --candidate-k 4 --mmr-lambda 0.35 "购买后多久还能退款？"
```

重点观察：

- 第四章的真实 `ChromaVectorStore` 现在直接成了第五章的检索底座
- `MMR` 会在重复退款 chunk 中更容易带出 `refund_process`
- `candidate_k` 不只是个附属参数，它决定了 MMR 有没有选择空间

### 第 3 步：跑坏案例回归

```bash
python 02_review_bad_cases.py --backend chroma
```

重点观察：

- `duplicate_refund_chunks`
- `candidate_pool_for_mmr`
- `metadata_scope`
- `no_answer`

这四类 case 已经把第五章最关键的策略差异变成了机器可判定现象。

### 第 4 步：观察 hybrid 和 rerank

```bash
python 04_hybrid_retrieval.py --backend chroma --reset
python 05_rerank_demo.py --backend chroma --reset
```

重点观察：

- 关键词和语义相似度各自擅长什么
- `alpha` 怎样改变混合排序
- `fetch_k` 为什么必须大于最终 `top_n`

### 第 5 步：进入统一引擎

```bash
python 06_smart_retrieval_engine.py --backend chroma --strategy hybrid --rerank --evaluate
```

这一层开始，你看到的已经不是零散 demo，而是统一应用接口：

- `retrieve(question, config)`
- `evaluate(test_cases, config)`

### 第 6 步：最后看测试

```bash
python -m unittest discover -s tests
```

测试现在锁定的不是“Retriever 类存在”，而是：

1. JSON 路径能稳定返回相关结果
2. Chroma 路径也能稳定返回相关结果
3. `threshold` 会清空无答案场景的弱相关尾部
4. `filename_filter` 真正作用在 Retriever 层
5. `MMR` 的平均冗余度低于纯 `similarity`
6. `candidate_k` 会改变 MMR 的可选候选池
7. `Recall@K / MRR` 能在固定评估集上稳定计算
8. `SmartRetrievalEngine` 能统一跑 `hybrid` 和可选 `rerank`

---

## Mini 回归集

第五章当前最值得反复观察的几条 case：

1. `购买后多久还能退款？`
   `similarity` 会拉回多个高度相似的退款块，`MMR` 更容易带出流程块
2. `为什么 metadata 很重要？`
   加上 `filename_filter=metadata_rules.md` 后，结果范围应明显收缩
3. `火星首都是什么？`
   `threshold` 应尽量把弱相关尾部清掉
4. `candidate_pool_for_mmr`
   说明 `candidate_k` 不够大时，MMR 根本没有可选择空间

---

## 本章边界

- 不展开 LangChain 内建高级 Retriever 的完整工程实现
- 不把 toy reranker 当成真实生产方案
- 不展开 Prompt 和生成

第五章当前真正要立住的是：

> 同一份底层向量数据，在应用层怎样查得更稳、更可控、更可评估。

---

## 学完这一章后你应该能回答

- 为什么 Retriever 不能等同于 Vector Store
- 为什么第五章应该复用第四章的 store 契约
- 为什么第五章现在默认要跑真实 Chroma
- 为什么坏案例回归和固定评估集都必须存在
- 为什么 `hybrid` 和 `rerank` 最后要进入统一引擎而不是继续做散落脚本

---

## 下一章

下一章进入 [../06_rag_generation/README.md](../06_rag_generation/README.md)。

第六章开始，你才会把当前 Retriever 输出接进 Prompt 和答案生成，形成真正的 RAG Chain。
