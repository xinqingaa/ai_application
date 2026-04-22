# 05. 检索策略 - 实践指南

> 这份 README 只负责一件事：带你按正确顺序跑完第五章，先用 JSON 看清策略逻辑，再切到真实 `Chroma`，把第四章的存储层真正接到 Retriever 上。

---

## 核心原则

```text
先看策略原理 -> 再看真实 Chroma -> 最后用坏案例和测试把策略锁住
```

- 在 `source/04_rag/05_retrieval_strategies/` 目录下操作
- 本章只讲 Retriever 层，不讲 Prompt 和生成
- 第五章不会再重写 provider 或 store，而是直接复用第四章的对象与向量空间
- `chroma_retriever.py` 是从旧 `phase_5` 扁平化提炼出来的真实实践层
- 旧的 `labs/phase_5_retrieval_strategies/` 只作为迁移期备份，不再是当前学习入口

---

## 项目结构

```text
05_retrieval_strategies/
├── README.md
├── requirements.txt
├── retrieval_basics.py
├── chroma_retriever.py
├── 01_compare_retrievers.py
├── 02_review_bad_cases.py
├── 03_query_demo.py
├── evals/
│   └── retrieval_bad_cases.json
├── store/
│   ├── .gitignore
│   ├── demo_retrieval_store.json
│   └── chroma/
└── tests/
    ├── test_retrievers.py
    └── test_chroma_retrievers.py
```

- `retrieval_basics.py`
  放第五章共享策略层：策略配置、JSON retriever、MMR、坏案例评估、demo store 构建
- `chroma_retriever.py`
  放第五章真实 `ChromaRetriever`
- `01_compare_retrievers.py`
  对比同一问题在不同策略和不同 backend 下的差异
- `02_review_bad_cases.py`
  用固定坏案例跑最小 `PASS / FAIL / INFO` 回归
- `03_query_demo.py`
  用单一策略跑一次完整检索实验

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

### 第 4 步：最后看测试

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

- 不展开 LangChain Retriever
- 不展开 rerank
- 不展开 hybrid retrieval
- 不展开 Prompt 和生成

第五章当前真正要立住的是：

> 同一份底层向量数据，在应用层怎样查得更稳、更可控、更可回归。

---

## 学完这一章后你应该能回答

- 为什么 Retriever 不能等同于 Vector Store
- 为什么第五章应该复用第四章的 store 契约
- 为什么第五章现在默认要跑真实 Chroma
- 为什么坏案例回归是检索调优的起点，而不是可有可无的附件

---

## 下一章

下一章进入 [../06_rag_generation/README.md](../06_rag_generation/README.md)。

第六章开始，你才会把当前 Retriever 输出接进 Prompt 和答案生成，形成真正的 RAG Chain。
