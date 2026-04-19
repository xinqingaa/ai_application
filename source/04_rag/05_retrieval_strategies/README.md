# 05. 检索策略 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/04_rag/05_retrieval_strategies.md) 学完第五章，并在不依赖第六章以后的前提下，看懂 Retriever 为什么存在，以及 `similarity / threshold / MMR / filename filter` 分别在解决什么问题。

---

## 核心原则

```text
先复用第四章 store 契约 -> 再看 Retriever 怎么收束这些查询 -> 最后用坏案例回归不同策略
```

- 在 `source/04_rag/05_retrieval_strategies/` 目录下操作
- 本章只讲 Retriever 层，不讲 Prompt 和生成
- 本章不会再重写一套 provider 或 store，而是直接复用第四章的对象与向量空间
- 为了保证策略实验可重复，脚本会在本章目录下重建一份固定 demo store
- 本章目录就是当前学习入口

---

## 项目结构

```text
05_retrieval_strategies/
├── README.md
├── retrieval_basics.py
├── 01_compare_retrievers.py
├── 02_review_bad_cases.py
├── 03_query_demo.py
├── evals/
│   └── retrieval_bad_cases.json
├── store/
│   └── demo_retrieval_store.json
└── tests/
    └── test_retrievers.py
```

- `retrieval_basics.py`
  放本章策略层对象、demo corpus、store 重建逻辑、Retriever、MMR 和 bad-case evaluation
- `01_compare_retrievers.py`
  对比同一问题在不同策略下的差异
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

### 2. 当前命令

```bash
python 01_compare_retrievers.py
python 01_compare_retrievers.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 02_review_bad_cases.py
python 03_query_demo.py --strategy similarity
python 03_query_demo.py --strategy threshold --threshold 0.80 "火星首都是什么？"
python 03_query_demo.py --strategy mmr
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_compare_retrievers.py
```

你现在最该先建立的直觉是：

- Vector Store 能查，不等于应用层就已经“检索做好了”
- `top_k / candidate_k / threshold / MMR / filename_filter` 都应该归到 Retriever 层来管理
- 第五章当前仍然只支持 `filename` 过滤
- 检索策略对比要靠同一问题下的可重复实验，而不是凭印象

---

## 第 1 步：看同一问题在不同策略下会发生什么

**对应文件**：`01_compare_retrievers.py`

重点观察：

- `similarity` 是否会召回很多高度相似的退款 chunk
- `threshold` 是否会截掉一部分低分尾部
- `MMR` 是否会更容易带出流程类 chunk
- `filename filter` 是否会缩小结果来源范围

这里的 compare 脚本会把 threshold 设成 `0.88`，方便你直接看到截尾效果。

---

## 第 2 步：看坏案例如何帮助判断要不要升级策略

**对应文件**：`02_review_bad_cases.py`、`evals/retrieval_bad_cases.json`

重点观察：

- 为什么“无答案”“重复召回”“范围过宽”应该区分开看
- 为什么 bad-case file 里要开始放 machine-checkable assertions
- 为什么脚本输出 `PASS / FAIL / INFO` 比纯人工观察更稳

---

## 第 3 步：看最小服务式检索入口

**对应文件**：`03_query_demo.py`

重点观察：

- `strategy / top_k / candidate_k / threshold / filename` 如何组合成一份检索配置
- 为什么 Retriever 返回的是稳定 `RetrievalResult[]`
- 为什么 MMR 会额外提示“显示分数是 similarity score”

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_retrievers.py`

测试不是本章重点，但可以锁定几个关键边界：

1. `similarity` 能稳定返回相关退款 chunk
2. `threshold` 会在无答案场景下清空弱相关尾部
3. `filename_filter` 真正作用在 Retriever 层
4. `MMR` 的结果集平均冗余度低于纯 `similarity`
5. query 和 store 不能跨 embedding space 混查

---

## 建议学习顺序

1. 先读 [第五章学习文档](../../../docs/04_rag/05_retrieval_strategies.md)
2. 再跑 `python 01_compare_retrievers.py`
3. 再跑 `python 02_review_bad_cases.py`
4. 最后跑 `python 03_query_demo.py --strategy similarity`

---

## 学完这一章后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么第五章应该复用第四章 store 契约
- `top_k / candidate_k / threshold / MMR / filename_filter` 各自解决什么问题
- 为什么第五章当前只支持 `filename` 过滤
- 为什么坏案例回归应该开始变成可判定的最小实验

---

## 当前真实进度和下一章

- 当前真实进度：第五章已经改成建立在第四章之上的独立学习单元
- 完成标准：能稳定比较检索策略，能解释检索失败原因，能跑通最小 bad-case regression
- 下一章：进入 [../06_rag_generation/README.md](../06_rag_generation/README.md)，把当前 Retriever 输出接进 Prompt 和答案生成，形成真正的 RAG Chain
