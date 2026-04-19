# 05. 检索策略 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md) 学完第五章，并在不依赖第六章以后的前提下，看懂 Retriever 为什么存在，以及 `similarity / threshold / MMR / filter` 分别在解决什么问题。

---

## 核心原则

```text
先看 Vector Store 能查什么 -> 再看 Retriever 怎么收束这些查询 -> 最后用坏案例对比不同策略
```

- 在 `source/04_rag/05_retrieval_strategies/` 目录下操作
- 本章只讲 Retriever 层，不讲 Prompt 和生成
- 为了保持章节独立，代码自带一个最小内存向量存储和固定样例 `EmbeddedChunk[]`
- 本章重点不是“多写几个参数”，而是建立可复现的检索判断能力
- 旧的 `labs/phase_5_retrieval_strategies/` 只作为迁移期备份，不再是当前学习入口

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
└── tests/
    └── test_retrievers.py
```

- `retrieval_basics.py`
  放本章所有最小对象、样例 `EmbeddedChunk[]`、向量存储、Retriever 和策略逻辑
- `01_compare_retrievers.py`
  对比同一问题在不同策略下的差异
- `02_review_bad_cases.py`
  用固定坏案例回归策略行为
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
python 03_query_demo.py --strategy threshold --threshold 0.60
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
- `top_k / threshold / MMR / filter` 都应该归到 Retriever 层来管理
- 检索策略对比要靠同一问题下的可重复实验，而不是凭印象

---

## 第 1 步：看同一问题在不同策略下会发生什么

**对应文件**：`01_compare_retrievers.py`

重点观察：

- `similarity` 是否会召回很多高度相似的 chunk
- `threshold` 是否会截掉低分尾部
- `MMR` 是否会把重复结果往后压
- `filename filter` 是否会缩小结果来源范围

---

## 第 2 步：看坏案例如何帮助判断要不要升级策略

**对应文件**：`02_review_bad_cases.py`、`evals/retrieval_bad_cases.json`

重点观察：

- 为什么“无答案”“重复召回”“范围过宽”应该区分开看
- 为什么坏案例记录会成为后续优化入口
- 为什么不是所有问题都要直接上更复杂策略

---

## 第 3 步：看最小服务式检索入口

**对应文件**：`03_query_demo.py`

重点观察：

- `strategy / top_k / threshold / filename` 如何组合成一份检索配置
- 为什么 Retriever 返回的是稳定 `RetrievalResult[]`
- 为什么第六章生成层会直接吃这里的输出

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_retrievers.py`

测试只锁定本章最重要的几件事：

1. `similarity` 能稳定返回相关结果
2. `threshold` 会减少低分尾部
3. `metadata filter` 真正作用在 Retriever 层
4. `MMR` 的结果集平均冗余度低于纯 `similarity`

---

## 建议学习顺序

1. 先读 [05_retrieval_strategies.md](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md)
2. 再跑 `python 01_compare_retrievers.py`
3. 再跑 `python 02_review_bad_cases.py`
4. 最后跑 `python 03_query_demo.py --strategy similarity`

---

## 学完这一章后你应该能回答

- 为什么 Vector Store 和 Retriever 最好继续拆层
- 为什么很多问题应该先看检索再看 Prompt
- `top_k / threshold / MMR / filter` 各自解决什么问题
- 什么时候只是调参数就够，什么时候才值得升级到更复杂检索

---

## 当前真实进度和下一章

- 当前真实进度：第五章已经改成独立学习单元
- 完成标准：能稳定返回检索结果，能解释检索失败原因，能判断是否需要增强检索
- 下一章：进入 [source/04_rag/06_rag_generation/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/README.md)，把当前 Retriever 输出接进 Prompt 和答案生成，形成真正的 RAG Chain
