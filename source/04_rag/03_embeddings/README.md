# 03. 向量化 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/04_rag/03_embeddings.md) 学完第三章，并在不依赖第四章以后的前提下，看懂 `SourceChunk -> EmbeddedChunk`、最小相似度排序，以及 toy provider 和真实 embeddings endpoint 之间的桥接关系。

---

## 核心原则

```text
先看稳定 chunk 如何变成向量 -> 再看 query/document 契约 -> 最后补真实 embeddings endpoint 的接入桥
```

- 在 `source/04_rag/03_embeddings/` 目录下操作
- 本章只讲向量化和最小语义排序，不讲向量数据库、检索策略和生成
- 默认仍然先用 toy provider 讲清原理，再用真实或 mock embeddings endpoint 做桥接
- 本章不重复 `02_llm/02_multi_provider` 已经讲过的 provider 配置和统一客户端
- 第三章重点是 embedding-specific 的差异：维度、批量输入、同一 embedding space

---

## 项目结构

```text
03_embeddings/
├── README.md
├── requirements.txt
├── embedding_basics.py
├── 01_embed_chunks.py
├── 02_compare_similarity.py
├── 03_query_vs_document.py
├── 04_real_embeddings.py
├── 05_semantic_search.py
├── data/
│   ├── source_chunks.json
│   └── search_cases.json
└── tests/
    └── test_embeddings.py
```

- `embedding_basics.py`
  放本章对象、toy provider、OpenAI-compatible embedding provider、相似度、契约校验和 mock semantic client
- `01_embed_chunks.py`
  看 `SourceChunk` 如何变成 `EmbeddedChunk`
- `02_compare_similarity.py`
  看 query 如何和 chunk vectors 做最小排序
- `03_query_vs_document.py`
  看为什么 toy provider 仍然保留 query/document 两个入口
- `04_real_embeddings.py`
  看真实或 mock embeddings endpoint 的返回形态、维度和契约
- `05_semantic_search.py`
  看 toy provider 和真实语义 provider 在同一查询上的排序差异
- `data/source_chunks.json`
  本章统一 chunk 资产
- `data/search_cases.json`
  本章回归样例和桥接坏例

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/03_embeddings
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 如果你要跑真实 embeddings

你已经在 `02_llm/02_multi_provider` 学过真实多平台调用，所以这里不再重讲。

第三章只需要这三个 embedding-specific 变量：

```bash
export EMBEDDING_API_KEY=...
export EMBEDDING_BASE_URL=...
export EMBEDDING_MODEL=...
```

如果没配环境变量，`04_real_embeddings.py` 和 `05_semantic_search.py` 会自动回退到内置 mock semantic client，方便你先看接口形状和桥接现象。

### 4. 当前命令

```bash
python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python 04_real_embeddings.py
python 05_semantic_search.py
python -m unittest discover -s tests
```

### 5. 先跑哪个

建议先跑：

```bash
python 01_embed_chunks.py
```

你最先要建立的直觉是：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- 第三章先讲向量契约，再讲真实 endpoint
- 真实 embeddings 接入不是为了替换 toy provider，而是为了补桥接层

---

## 第 1 步：看 `SourceChunk -> EmbeddedChunk`

**对应文件**：`01_embed_chunks.py`

重点观察：

- 向量化前后哪些字段被保留
- `provider_name / model_name / dimensions / vector` 是第三章新增的什么信息
- 为什么第二章的 `source / filename / suffix / range` 不能丢

---

## 第 2 步：看 query 如何和 chunk 做相似度排序

**对应文件**：`02_compare_similarity.py`

重点观察：

- query 先被变成 query vector
- chunk 先被变成 document vectors
- 排序结果仍然保留原始 chunk 身份
- 相似度比较必须发生在同一 provider/model 空间里

---

## 第 3 步：看为什么 toy provider 还保留 query/document 两个入口

**对应文件**：`03_query_vs_document.py`

重点观察：

- 同一段文本走 query path 和 document path 时，结果可以不同
- 它们不同不代表不可比较
- toy provider 用 mode buckets 把契约差异显式暴露出来
- 真实 provider 即使映射到同一个 embeddings endpoint，也不应该把接口语义抹平

---

## 第 4 步：看真实 embeddings endpoint 的桥接

**对应文件**：`04_real_embeddings.py`

这一节不再教你怎么配置多平台调用，而是只看 embedding-specific 的新增点。

重点观察：

- `OpenAICompatibleEmbeddingProvider` 如何复用你已经熟悉的 OpenAI-compatible 调用方式
- 为什么 `embed_query / embed_documents` 仍然保留两个方法
- 为什么真实 endpoint 的关键关注点变成了 `dimensions / batch count / same space`
- 为什么脚本在没配置环境变量时会回退到 mock semantic client

---

## 第 5 步：看 toy provider 和真实语义排序的差异

**对应文件**：`05_semantic_search.py`

这一节的重点不是“真实 provider 一定更强”，而是让你看到：

- toy provider 解决的是原理教学
- 真实语义 provider 解决的是更自然的语义泛化

重点观察：

- 为什么 `为什么文档块要记录出处？` 这种问题会成为 toy provider 的已知缺口
- 为什么真实或 mock semantic provider 更可能把它排到 metadata chunk
- 这正是第三章要补真实 embedding 桥的原因

---

## 第 6 步：最后看测试在锁定什么

**对应文件**：`tests/test_embeddings.py`

测试会锁定第三章最重要的几件事：

1. toy provider 维度固定
2. `EmbeddedChunk` 保留原始 chunk 身份
3. query/document 两条路径在 toy provider 下不同但可比较
4. local search cases 仍然稳定
5. `OpenAICompatibleEmbeddingProvider` 能通过 fake client 走通
6. 已知缺口样本在 semantic provider 下会被修正
7. 错误响应形态、错误数量、维度漂移会直接失败

---

## 建议学习顺序

1. 先读 [03_embeddings.md](../../../docs/04_rag/03_embeddings.md)
2. 跑 `python 01_embed_chunks.py`
3. 再跑 `python 02_compare_similarity.py`
4. 再跑 `python 03_query_vs_document.py`
5. 再跑 `python 04_real_embeddings.py`
6. 最后跑 `python 05_semantic_search.py`

---

## 第三章最小回归集

第三章现在有两层回归样例：

1. `data/source_chunks.json`
   - 锁定本章统一 chunk 资产
2. `data/search_cases.json`
   - 锁定 local provider 结果
   - 同时保留一条 semantic bridge 坏例

这份回归样例主要回答四个问题：

- toy provider 的教学主线还在不在
- 最小语义排序有没有明显跑偏
- 真实 embedding adapter 有没有保持同一契约
- 已知坏例有没有被明确保留下来而不是被悄悄删除

---

## 失败案例也要刻意观察

第三章至少要刻意看三类失败：

1. provider 契约失败
   - 向量数量和输入数量不匹配
   - 向量维度漂移

2. 向量空间混用失败
   - query 和 document 向量不是同一个 provider/model 空间

3. toy provider 语义缺口
   - `为什么文档块要记录出处？` 在 local provider 下会先命中错误 chunk
   - 这不是 bug 修完就结束，而是第三章真实 embedding 桥接存在的理由

---

## 学完这一章后你应该能回答

- 为什么第三章只增加向量层，而不是重做输入管道
- 为什么 `EmbeddedChunk` 要保留 `SourceChunk`
- 为什么 `embed_query()` 和 `embed_documents()` 不该混成一个模糊接口
- 为什么真实 embeddings 和 chat completions 虽然都走 OpenAI-compatible，但关注点完全不同
- 为什么维度、批量数量和同一 embedding space 必须在第三章就立住
- 为什么 toy provider 和真实 provider 应该在同一章内形成桥接，而不是互相替代

---

## 当前真实进度和下一章

- 当前真实进度：第三章已经补上真实 embeddings endpoint 的桥接层
- 完成标准：能看懂向量化增量、相似度排序、provider 契约和 toy -> real 的过渡关系
- 下一章：进入 [04_vector_databases](../04_vector_databases/README.md)，把 `EmbeddedChunk[]` 写进向量存储，做最小查询、过滤和删除
