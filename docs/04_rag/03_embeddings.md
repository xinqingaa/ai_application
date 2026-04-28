# 03. 向量化

> 本章目标：讲清文本向量化的必要性，建立 `SourceChunk -> EmbeddedChunk`、`embed_query / embed_documents` 和同一 embedding space 的最小心智模型，然后在同一章里补上真实 embeddings endpoint 的接入桥。

---

## 1. 概述

### 学习目标

- 理解文本向量化的必要性
- 理解 `SourceChunk -> EmbeddedChunk` 新增的向量层信息
- 理解 `embed_query / embed_documents` 两个入口的职责边界
- 理解 query/document 必须落在同一 embedding space 的约束
- 理解真实 embeddings endpoint 对维度、批量输入和契约稳定性的要求
- 理解 toy provider 和真实 provider 在第三章里的关系
- 能看懂第三章代码里的最小语义排序闭环

### 预计学习时间

- 向量化原理：40 分钟
- provider 契约与 query/document：40 分钟
- 最小排序与回归边界：30-40 分钟
- 真实 embeddings endpoint 桥接：40-60 分钟
- 第三章代码实践：40-60 分钟

### 本章在 AI 应用中的重要性

| 场景 | 本章先解决的内容 |
|------|----------------|
| 语义检索 | 文本到可比较向量的映射 |
| provider 切换 | 模型变了以后，哪些契约必须保持 |
| 检索质量 | 语义向量对纯关键词局限的补足 |
| 后续存储 | 向量进入第四章前的标准形态 |

### 学习前提

- 建议先完成第二章，已经理解稳定 `SourceChunk[]` 的意义
- 建议先完成 `02_llm/02_multi_provider`
- 你应该已经掌握真实 LLM / OpenAI-compatible 平台的基本调用方式

这一章不再重复讲：

- `api_key`
- `base_url`
- 统一客户端
- 多平台差异的通用抽象

第三章只关注 embedding-specific 的问题。

### 本章与前后章节的关系

第二章解决的是：

1. 原始文件怎样进入系统
2. 文本怎样变成稳定 `SourceChunk[]`
3. metadata 和稳定 ID 的前置必要性

第三章接着解决的是：

1. 稳定 chunk 到向量的转换
2. query/document 两个入口的保留
3. provider 契约在向量层的前置建立
4. toy provider 到真实 embeddings endpoint 的过渡

第四章会继续依赖这里：

1. 把 `EmbeddedChunk[]` 写进向量存储
2. 在存储层继续维护 provider/model space 的一致性

### 本章代码入口

本章对应的代码目录是：

- [README.md](../../source/04_rag/03_embeddings/README.md)
- [requirements.txt](../../source/04_rag/03_embeddings/requirements.txt)
- [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py)
- [01_embed_chunks.py](../../source/04_rag/03_embeddings/01_embed_chunks.py)
- [02_compare_similarity.py](../../source/04_rag/03_embeddings/02_compare_similarity.py)
- [03_query_vs_document.py](../../source/04_rag/03_embeddings/03_query_vs_document.py)
- [04_real_embeddings.py](../../source/04_rag/03_embeddings/04_real_embeddings.py)
- [05_semantic_search.py](../../source/04_rag/03_embeddings/05_semantic_search.py)
- [data/source_chunks.json](../../source/04_rag/03_embeddings/data/source_chunks.json)
- [data/search_cases.json](../../source/04_rag/03_embeddings/data/search_cases.json)
- [tests/test_embeddings.py](../../source/04_rag/03_embeddings/tests/test_embeddings.py)

### 本章边界

本章重点解决：

1. 向量化的职责
2. `EmbeddedChunk` 的存在价值
3. `embed_query / embed_documents` 的分离边界
4. provider 契约
5. 最小语义排序
6. 真实 embeddings endpoint 的桥接

本章不展开：

- 向量数据库
- metadata 过滤检索
- rerank
- hybrid retrieval
- 生成回答
- 第四章的存储层 API

这里故意只保留：

- 一组固定样例 `SourceChunk[]`
- 一个 toy provider
- 一个 OpenAI-compatible embeddings provider
- 一个最小 cosine similarity 排序
- 一组显式保留的坏例和契约失败样本

目的不是追求“模型覆盖最多”，而是先把向量层主线讲清楚。

### 本章学习地图

建议按下面这条主线阅读本章，而不是一开始就陷入某个 provider 或某个模型名：

```text
先看完整流程
-> 再看 query/document 的分流建模
-> 再看 provider 契约对不同实现的统一收束
-> 再看 SourceChunk 到 EmbeddedChunk 的转换与排序参与方式
-> 最后看真实 embeddings endpoint 的桥接方式
```

本章后面的 known gap、失败案例和答疑内容，更适合在你已经跑过代码以后回头复盘。

---

## 2. 向量层的完整流程 📌

第三章可以先不要从“哪个模型更强”开始，而是先建立一条完整主线。

这一章做的是把第二章留下来的稳定 `SourceChunk[]`，加工成后续检索与存储可以稳定消费的向量层输入：

```text
SourceChunk[]
-> 选择 embedding provider
-> provider.embed_documents()
-> 得到 document vectors
-> 收束成 EmbeddedChunk[]
-> provider.embed_query()
-> 得到 query vector
-> cosine_similarity(query, chunk.vector)
-> ranked results
```

这条链路里每一步都有明确输入和输出：

| 阶段 | 输入 | 输出 | 对应代码 |
|------|------|------|----------|
| 样例资产加载 | 固定 `source_chunks.json` | `SourceChunk[]` | `demo_source_chunks()` |
| provider 选择 | toy / real / mock | `EmbeddingProvider` 实现 | `LocalKeywordEmbeddingProvider` / `OpenAICompatibleEmbeddingProvider` |
| 文档向量化 | `SourceChunk[]` | `EmbeddedChunk[]` | `embed_chunks()` |
| query 向量化 | `question` | `query vector` | `embed_query()` |
| 相似度计算 | query vector + chunk vectors | score | `cosine_similarity()` |
| 排序收束 | score 列表 | ranked results | `score_query_against_chunks()` |

初学时可以先记住一个判断标准：

> 第二章解决知识片段稳定进入系统的问题，第三章解决稳定片段进入同一个可比较向量空间的问题。

后面的章节会按这条主线展开：先讲向量层本身，再讲 query/document 分流，再讲 provider 契约和 `EmbeddedChunk`，最后讲真实桥接、回归和代码实践。

---

## 3. 主流程拆解：从 `SourceChunk[]` 到排序结果 📌

### 3.1 向量化的目标：把文本变成可比较表示

如果系统只会做字符串匹配，很快会遇到两个问题：

- 同义表达容易漏召回
- 表面词很像但语义不相关的内容可能被误排前面

Embedding 的核心作用不是“把文本变高级”，而是：

> 把文本映射成一个可以计算相似度的表示空间。

### 3.2 第三章新增的标准接口

第三章真正新增的不是新的一套输入层，而是：

```text
SourceChunk[] -> EmbeddedChunk[]
```

这里新增的核心字段只有几类：

- `vector`
- `provider_name`
- `model_name`
- `dimensions`

第二章留下来的这些字段仍然必须保留：

- `chunk_id`
- `document_id`
- `source`
- `filename`
- `suffix`
- `char_start / char_end`

所以你应该把 `EmbeddedChunk` 理解成：

> 保留原始 chunk 身份的向量增强版。

### 3.3 `EmbeddedChunk` 不替代 `SourceChunk`

如果第三章直接把 chunk 内容和 metadata 丢掉，只留下向量，后面会立刻出问题：

- 第四章不知道自己在存哪一个 chunk
- 后续引用和删除没有稳定锚点
- 调试时也不知道是哪个原文片段得分高

所以第三章不是在“用向量替代文本”，而是在“给稳定 chunk 再包一层可比较表示”。

### 3.4 第三章继承第二章的哪些成果

第三章默认直接消费第二章留下来的这些成果：

- 稳定 `SourceChunk[]`
- 稳定 `document_id / chunk_id`
- 稳定 metadata

也就是说，第三章本质上是在建立下面这条向量层主线：

> 已经稳定下来的 chunk 进入同一个可比较的语义空间。

### 3.5 第三章的运行时主链路

这一章最值得先建立手感的，不是某个模型名，而是一条完整的运行时链路：

```text
SourceChunk
-> provider.embed_documents()
-> EmbeddedChunk
-> provider.embed_query()
-> cosine_similarity()
-> ranked results
```

如果你能把这条链路讲清楚，第三章的大部分内容就已经真正掌握了。

### 3.6 稳定向量层的工程价值

很多学习资料会把第三章讲成：

- 调一下 embeddings API
- 拿回一组浮点数
- 结束

这种讲法不够。

更准确的说法是：

> 第三章在定义后续章节要消费的标准向量接口。

后面的向量存储、检索过滤、删除和评估，默认都要建立在这里的输出之上。

所以这里的重点不是“先拿到一组向量”，而是：

- 向量维度要稳定
- chunk 身份不能丢
- provider/model space 要显式
- query/document 要能稳定比较
- 错误要能尽早失败

### 3.7 向量化的职责边界

向量化负责的是：

- 把文本映射成可比较表示
- 保留 chunk 身份
- 给排序和存储提供稳定契约

向量化不负责：

- top-k 存储结构设计
- metadata 过滤执行
- rerank 精排补充
- 最终回答生成

它的职责是“让 chunk 可比较”，不是“替整个 RAG 做决定”。

---

## 4. Query / Document 分流与 Provider 设计 📌

现在先不要急着看真实 provider。第三章更重要的是先建立 query/document 分流进入向量层的判断标准。

### 4.1 query 和 document 在系统中的角色分工

在检索系统里：

- document vector 代表“知识库里的候选依据”
- query vector 代表用户当前查询意图

它们都属于同一个 embedding space，但在系统角色上不是同一件事。

### 4.2 保留两个向量化入口的设计依据

第三章要保留：

- `embed_query()`
- `embed_documents()`

不是因为所有真实 provider 都会给你两个完全不同的 API，而是因为：

1. 教学上，这能把 query/document 的角色差异显式暴露出来
2. 工程上，这给未来切换模型或 provider 留出了更稳的接口边界

### 4.3 分开入口不等于混用不同向量空间

这也是最容易误解的点。

保留两个入口，不代表你可以：

- query 用一个 provider
- documents 用另一个 provider
- 或者 query/document 用不同 model space

更准确的约束是：

> query/document 可以走不同的方法入口，但必须落在同一个 provider/model embedding space 里。

### 4.4 `LocalKeywordEmbeddingProvider` 的教学定位

第三章当前的 `LocalKeywordEmbeddingProvider` 会刻意把 query/document 差异显式做出来。

它的作用不是模拟真实模型细节，而是为了让你先看清这层契约：

- query/document 可以不同
- 但它们仍然必须可比较

这是一种教学放大镜。

这个 toy provider 不是“随便写个假向量”。

它刻意保留了三层信号：

1. `CONCEPT_GROUPS`
   - 把退款、试学、metadata、stable id、embedding、similarity 这些概念组显式暴露出来
2. `HASH_BUCKETS`
   - 让不在概念组里的 token 也有最小分布能力
3. `MODE_BUCKETS`
   - 用尾部两个 bucket 把 query/document 路径差异显式写进向量

所以它真正要教你的不是“怎样造假向量”，而是：

> 向量空间的比较性，依赖共享语义基底和一致契约，而不是依赖接口长得一样。

### 4.5 `_embed()` 的向量构造逻辑

`LocalKeywordEmbeddingProvider._embed()` 是一个教学用的 toy embedding，不是生产级 embedding。它的目标不是语义效果最好，而是把真实 embedding 里不容易直接看见的几个概念拆开演示出来：

- 概念信号
- 弱文本分布
- query/document 两个入口的差异
- 归一化后再做相似度比较

整体可以把它理解成：把一段文本压成一个固定长度的数字列表。

```text
向量 = [概念命中区..., hash 分布区..., query/document 角色区]
```

当前代码中的维度来自：

```python
DEFAULT_DIMENSIONS = len(CONCEPT_GROUPS) + HASH_BUCKETS + MODE_BUCKETS
```

也就是：

```text
7 个概念维度 + 4 个 hash bucket + 2 个角色维度 = 13 维
```

第一步是统一文本格式：

```python
normalized = " ".join(text.lower().split())
```

这一步把文本转小写，并把多余空白压成单个空格。这样 `"Embedding"`、`"embedding"`、`" embedding  "` 这类输入会尽量被当成一样的内容处理。

第二步是创建固定长度向量：

```python
vector = [0.0] * self.dimensions
```

无论输入文本多长，最后都要变成固定维度的向量。这里先创建一个全 0 的 13 维向量。

第三步是写入概念命中区：

```python
for index, (_, keywords) in enumerate(CONCEPT_GROUPS):
    hits = sum(1 for keyword in keywords if keyword in normalized)
    vector[index] = float(hits)
```

`CONCEPT_GROUPS` 把一些教学场景里的概念放到明确维度上：

```text
第 0 维：退款相关
第 1 维：试学相关
第 2 维：metadata / 来源相关
第 3 维：稳定 id 相关
...
```

如果文本是 `如何申请退费？`，它命中了 `退费`，所以退款维度会变大。如果文本是 `每个文档块都应该保留 source、filename 和来源字段`，它命中了 `source`、`filename`、`来源`，所以 metadata 维度会变大。

这一步的作用是：让相似文本在同一个概念维度上有相近的值。

第四步是写入 hash bucket 区：

```python
for token in TOKEN_PATTERN.findall(normalized):
    if token in STOPWORDS:
        continue
    bucket = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % HASH_BUCKETS
    vector[hash_offset + bucket] += 0.25
```

不是所有词都在 `CONCEPT_GROUPS` 里，例如 `购买后 7 天内`、`课程助教`、`工作日`。如果这些词完全丢掉，向量会太粗糙。

所以代码把这些 token 用哈希分到 4 个桶里。每命中一个 token，就给对应桶加 `0.25`。这不是精确语义，只是保留一点文本分布痕迹。两个文本如果有一些相似 token，它们更可能在 hash 区也有接近的值。

第五步是写入 query/document 角色区：

```python
query_mode_index = self.dimensions - 2
document_mode_index = self.dimensions - 1

if kind == "query":
    vector[query_mode_index] = 0.30
else:
    vector[document_mode_index] = 0.30
```

最后两个维度专门表示：

```text
倒数第 2 维：这是 query vector
倒数第 1 维：这是 document vector
```

所以同一段文本分别走下面两个入口时，前面的概念区和 hash 区很像，但尾部角色区不同：

```python
provider.embed_query("Embedding 会把文本映射成向量。")
provider.embed_documents(["Embedding 会把文本映射成向量。"])
```

这一步是为了说明：query embedding 和 document embedding 是两个不同入口。它们可以不同，但必须在同一个 embedding space 里，才能比较相似度。

真实 embedding 服务里，有些模型区分 query/document，有些不区分。这个 toy provider 是故意把差异显式做出来，方便观察。

最后一步是归一化：

```python
return normalize(vector)
```

归一化后，向量长度会变成 1。后面用的是余弦相似度：

```python
cosine_similarity(query_vector, chunk.vector)
```

余弦相似度更关心“方向像不像”，而不是“数字总量大不大”。否则长文本因为 token 更多、数值更大，可能天然更占优势。归一化可以减少这种影响。

以 `如何申请退费？` 为例，它大致会变成：

```text
[
  退款概念较高,
  试学概念为 0,
  metadata 概念为 0,
  ...
  一些 hash bucket 值,
  query 角色值=0.30,
  document 角色值=0
]
```

而退款政策 chunk 大致会变成：

```text
[
  退款概念较高,
  试学概念为 0,
  metadata 概念为 0,
  ...
  一些 hash bucket 值,
  query 角色值=0,
  document 角色值=0.30
]
```

它们的“退款概念维度”方向接近，所以相似度高。

总结一下，`_embed()` 这样计算向量，是为了把 embedding 拆成 4 件事：

- 概念命中：让“退费”和“退款”靠近
- hash bucket：保留一点普通词分布
- 角色 bucket：演示 query/document 两个入口的差异
- normalize：让后续余弦相似度更稳定

真实 embedding 模型不会这样手写规则，它会用神经网络学出来。但这段代码的好处是每一维都能解释，适合学习 RAG 里“文本到可比较向量”的转换过程。

### 4.6 query/document 双路径的可比较性

在 `03_query_vs_document.py` 里，同一段文本会分别走：

- `embed_query(text)`
- `embed_documents([text])`

结果会不同，但不会完全失去可比性。

这是因为：

- 共享概念组还在
- 共享 hash buckets 还在
- 只是在 mode buckets 上刻意留出角色差异

它想让你建立的直觉是：

> “不完全相同” 和 “不可比较” 不是一回事。

---

## 5. 从 Provider 契约到 `EmbeddedChunk[]` 📌

前一节已经建立 query/document 分流建模的边界。这一节开始看第三章真正可运行的对象和收束函数。

### 5.1 第三章的核心运行时对象

在 [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py) 里，最值得先建立手感的不是“函数很多”，而是对象已经很清楚。

你可以先把这些对象看成第三章向量层的运行时骨架：

| 对象 | 作用 |
|------|------|
| `SourceChunk` | 第二章留下来的标准 chunk 输入 |
| `EmbeddedChunk` | 保留 chunk 身份的向量增强对象 |
| `EmbeddingProvider` | query/document 向量化的最小契约 |
| `LocalKeywordEmbeddingProvider` | 把 query/document 差异显式做出来的 toy provider |
| `OpenAICompatibleEmbeddingProvider` | 第三章真实 embeddings endpoint 的最小桥接实现 |
| `MockSemanticOpenAIClient` | 没配真实环境变量时的语义桥接替身 |
| `MockEmbeddingResponse` | 模拟真实 embeddings 响应形状的最小对象 |

这和第二章先看 `DocumentCandidate / LoadedDocument / SourceChunk` 是同一类学习方式：

> 先看清运行时对象，再看函数如何把它们串起来。

### 5.2 最小 provider 契约

这一章里最小 provider 契约至少包含：

- `provider_name`
- `model_name`
- `dimensions`
- `embed_query()`
- `embed_documents()`

这个契约的价值在于：

- 你可以换实现
- 但后面的排序逻辑不用跟着改

### 5.3 `embed_chunks()` 和 `score_query_against_chunks()` 的职责

很多人第一次看第三章时，只会注意“拿到了向量”。

但真正要看的其实是两条收束函数：

`embed_chunks()` 在做：

```text
SourceChunk[] -> provider.embed_documents() -> EmbeddedChunk[]
```

`score_query_against_chunks()` 在做：

```text
question -> provider.embed_query() -> cosine_similarity(query, chunk.vector) -> ranking
```

也就是说，第三章真正交付的不是“一个 embeddings demo”，而是：

> 一组稳定的 document vectors，加上一套稳定的 query-vs-document 比较方式。

### 5.4 向量层错误的前置失败

第三章有几类错误必须尽早失败，而不是传到第四章以后再爆：

- 返回向量数量不对
- 返回维度不对
- query/document 不在同一 provider/model space

这类错误如果在第三章不拦住，后面就会变成更难排查的“检索效果很怪”。

### 5.5 `ensure_vector_dimensions()` 保护的维度契约

这一层很多人会低估。

如果一个 provider 声称自己是固定维度空间，但返回的向量长度时长时短，后面的排序和存储都不成立。

`ensure_vector_dimensions()` 的作用就是把这种漂移尽早拦住。

它不是“额外的防御性代码”，而是在保护：

- 当前 provider 的维度承诺
- 当前模型空间的稳定性
- 后续 cosine similarity 和向量存储的前提

### 5.6 `ensure_same_embedding_space()` 保护的空间契约

这个函数最重要的作用不是比较浮点数，而是比较身份：

- `provider_name`
- `model_name`
- `dimensions`

也就是说，它在防止的不是“相似度计算报错”而已，而是：

> 你以为自己在比较 query 和 chunk，实际上却把两个不同空间的向量混在了一起。

### 5.7 零向量和空输入的边界

第三章还要建立一个很重要的习惯：

- 空输入要有明确边界
- 零向量要有明确处理方式

当前代码里：

- `embed_chunks([])` 会直接返回空列表
- `score_query_against_chunks(..., [])` 会直接返回空列表
- `cosine_similarity()` 遇到零向量时会返回 `0.0`

因为后面相似度、排序、存储都会建立在这些细节之上。

---

## 6. 真实 Embeddings Endpoint 的桥接 📌

前面几节主要解决的是向量层心智模型。这一节开始补真实 provider，但仍然围绕第三章主线收敛，不扩展成完整平台接入教程。

### 6.1 真实 provider 的补充价值

如果第三章永远只停留在 toy provider，你会少掉三种现实感知：

1. 真实 embedding model 会有真实维度
2. 真实 endpoint 天然支持批量输入
3. 真实语义空间会补足 toy provider 的语义缺口

所以第三章现在要补的不是“真实调用入门”，而是：

> embedding-specific 的真实接入桥。

### 6.2 与 `02_llm/02_multi_provider` 的边界

`02_llm/02_multi_provider` 已经覆盖以下通用平台接入内容：

- OpenAI-compatible 平台配置
- `api_key / base_url / model` 切换
- 统一抽象的设计动机

所以第三章不再重讲这些内容。

第三章只关心：

- 真实 embeddings endpoint 的接口形态
- 维度确定方式
- 批量输入处理方式
- `embed_query / embed_documents` 接口的语义保留

### 6.3 Embeddings 和 Chat Completions 的关注点差异

这两类接口虽然都可能使用 OpenAI-compatible SDK，但你在工程上关注的东西不同：

| 接口 | 核心关注点 |
|------|------------|
| `chat.completions` | messages、system、temperature、max_tokens |
| `embeddings` | dimensions、batch count、same space、向量稳定性 |

这就是第三章现在最重要的区分。

### 6.4 真实 provider 下的 `embed_query / embed_documents` 映射

对很多 OpenAI-compatible embeddings endpoint 来说：

- `embed_query()`
- `embed_documents()`

最终会映射到同一个 embeddings API。

这不代表接口分层没有意义。

恰恰相反，它说明：

> 接口语义和底层 endpoint 可以不是一一对应的。

第三章保留这两个方法，是为了保持语义边界，而不是强行追求“方法一定要调不同 API”。

### 6.5 `OpenAICompatibleEmbeddingProvider` 的能力范围

这个 provider 在第三章里真正补的是四类能力：

1. 从环境变量或显式参数构造真实 provider
2. 统一处理批量输入
3. 记录并校验返回维度
4. 在没配置真实环境时回退到 `MockSemanticOpenAIClient`

所以它不是“完整生产封装”，而是：

> 一个足够真实、但仍然围绕教学主线收敛的 embeddings bridge。

### 6.6 模型切换时必须保持的契约

当你把模型从：

- toy provider
- 切到 OpenAI-compatible embedding model
- 或切到本地 HuggingFace / sentence-transformers

最关键要守住的是：

1. `dimensions` 要明确
2. query/document 要保持同一 space
3. 批量输出数量要和输入一致
4. `EmbeddedChunk` 不能丢失原始 chunk 身份

---

## 7. 语义排序与最小回归的治理锚点 📌

前三章到这里，已经不只是“能跑出一个 demo”了。这里开始要明确向量层最小不变量，否则第四章以后很难定位问题到底出在哪一层。

### 7.1 第三章的回归视角

很多人会以为“回归和评估”要等到完整 RAG 才开始。

其实第三章就已经需要最小回归了，因为这里已经有三类会漂移的东西：

- chunk 资产本身
- provider 契约
- 排序结果

如果这里不先锁住，第四章以后你会很难判断：

- 是存储层有问题
- 是检索层有问题
- 还是第三章的向量空间已经悄悄变了

### 7.2 第三章的核心治理锚点

这一章里最值得先立住的锚点至少有四个：

1. `chunk_id / document_id`
2. `provider_name / model_name / dimensions`
3. `data/source_chunks.json`
4. `data/search_cases.json`

它们共同锁定的是：

- 当前是谁的向量
- 当前属于哪个空间
- 当前排序使用的资产
- 当前已知坏例的显式保留状态

### 7.3 `source_chunks.json` 锁定的内容

`source_chunks.json` 锁住的是本章统一 chunk 资产。

它不是完整的知识库，而是第三章最小可重复输入集。

它的价值在于：

- 所有 demo 脚本都在消费同一批 chunk
- `EmbeddedChunk` 的来源稳定
- 你能把“向量漂移”和“样例内容变化”区分开

### 7.4 `search_cases.json` 锁定的内容

`search_cases.json` 锁住的不是“真实世界最优检索结果”，而是当前课程主线下最小可观测行为。

它至少在锁四类现象：

1. local provider 的默认排序结果
2. 一条显式保留的 known gap
3. semantic provider 对这条 known gap 的修正方向
4. 第三章桥接层仍然成立

### 7.5 known gap 的保留价值

第三章里有一条非常重要的坏例：

```json
{
  "question": "为什么文档块要记录出处？",
  "local_expected_top_chunk": "refund:0",
  "semantic_expected_top_chunk": "metadata:0"
}
```

这条样本的价值不在于“证明 toy provider 不够强”，而在于：

> 它明确告诉你，toy provider 和 semantic provider 在第三章是桥接关系，不是互相替代关系。

如果把这类坏例删掉，第三章就会变成“只保留能说明自己正确的样例”，教学价值反而下降。

### 7.6 known gap 误排到 `refund:0` 的流程

从人的语义理解看，`为什么文档块要记录出处？` 明显应该匹配 `metadata:0`：

```text
每个文档块都应该保留 source、filename 和 header_path 这类来源字段，方便引用、过滤和调试。
```

但在 `05_semantic_search.py` 里，本地关键词向量会把它排到 `refund:0`：

```text
购买后 7 天内且学习进度不超过 20%，可以申请全额退款。
```

这不是因为“退款”和“出处”语义相关，而是因为本地 toy provider 的设计边界导致了误排。

本地 provider 的 metadata 概念词是：

```python
("metadata", ("metadata", "source", "filename", "来源"))
```

而 query 是：

```text
为什么文档块要记录出处？
```

它没有命中 `metadata / source / filename / 来源` 中的任何一个词。也就是说，query 在概念区基本是全 0：

```text
refund=0
trial=0
metadata=0
stable_id=0
embedding=0
similarity=0
support=0
```

此时本地 provider 没有意识到“出处”属于 metadata 问题。

接下来，query 只能依赖 hash bucket 这类弱信号。它会被拆成类似这样的单字 token：

```text
为 什 么 文 档 块 要 记 录 出 处
```

这些 token 不在 `CONCEPT_GROUPS` 里，就会进入 hash buckets。hash bucket 只保留一点文本分布痕迹，不理解语义。

反过来看 `metadata:0`，它虽然命中了强 metadata 概念：

```text
source
filename
来源
```

但 query 的 metadata 维度是 0，所以这部分强信号在 cosine similarity 里贡献不上：

```text
query.metadata = 0
metadata_chunk.metadata = 很高
相乘以后仍然是 0
```

这就是这个坏例最关键的反直觉点：

> metadata chunk 自己很像 metadata，但 query 没有被 local provider 识别成 metadata，所以这部分优势没有用上。

最后，`refund:0` 虽然语义不相关，但它的普通 token hash 分布碰巧和 query 更接近，于是被排到了前面。

本地排序大致会变成：

```text
refund:0     分数最高
support:0
metadata:0
support:1
embedding:0
trial:0
```

所以这个结果不是“业务上合理”，而是“教学上有意保留的缺口”：

```text
query 没有命中 metadata 概念
-> 只能靠 hash bucket 弱信号
-> hash bucket 发生误排
-> toy provider 暴露出语义泛化不足
```

真实 embedding 模型更可能理解下面这些表达属于同一类问题：

```text
出处
来源
source
filename
header_path
引用
```

所以真实语义 provider 更容易把这个问题排到 `metadata:0`。这就是 `05_semantic_search.py` 要展示的重点：

```text
toy provider 用来解释机制；
real embedding 用来补足语义泛化。
```

如果想让本地关键词向量也排对，最直接的方法是扩充 metadata 概念词：

```python
("metadata", ("metadata", "source", "filename", "来源", "出处", "引用", "header_path"))
```

这样 query 里的 `出处` 会命中 metadata 维度，`metadata:0` 大概率就会上来。

但课程这里故意没有这么做，是为了保留一个坏例，让你看见：

- 手写关键词 / hash 向量的边界在哪里
- 真实语义 embedding 的增量价值在哪里
- 第三章同时保留 toy provider 和 real provider 的教学必要性

### 7.7 治理锚点缺失后的连锁问题

如果这些锚点没有先立住，后面很快会出现问题：

- 一条向量对应的 chunk 变得不清楚
- 不同 provider 的结果可能被混在一起
- 排序变化难以区分来自模型切换还是样例漂移
- known gap 的修正和删除难以区分

所以第三章的“治理视角”不是企业级平台治理，而是：

> 先把向量层最小不变量立住。

---

## 8. 代码实践：按流程阅读第三章

这一节建议当作复习路径使用。前面已经按概念讲完了完整流程，这里再回到代码目录，把每个脚本对应到向量层流程中的一个阶段。

推荐阅读顺序是：

```text
embedding_basics.py
-> 01_embed_chunks.py
-> 02_compare_similarity.py
-> 03_query_vs_document.py
-> 04_real_embeddings.py
-> 05_semantic_search.py
-> tests/test_embeddings.py
```

这样读的好处是：你不是在记脚本编号，而是在复盘“稳定 chunk 如何一步步变成可排序向量”。

### 8.1 目录结构

本章代码目录是：

```text
source/04_rag/03_embeddings/
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

### 8.2 输入和输出

本章代码的输入是：

- 一组固定样例 `SourceChunk[]`
- 一个 toy provider 或真实 embedding provider
- 一个 query

本章代码的输出是：

- `EmbeddedChunk[]`
- query vector
- document vectors
- similarity scores
- toy vs semantic provider 的桥接现象

### 8.3 本章核心对象和函数

在 [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py) 里，你最值得先看的是：

- `SourceChunk`
- `EmbeddedChunk`
- `EmbeddingProvider`
- `LocalKeywordEmbeddingProvider`
- `OpenAICompatibleEmbeddingProvider`
- `MockSemanticOpenAIClient`
- `demo_source_chunks()`
- `load_search_cases()`
- `build_openai_provider_or_mock()`
- `embed_chunks()`
- `ensure_vector_dimensions()`
- `ensure_same_embedding_space()`
- `score_query_against_chunks()`
- `cosine_similarity()`

### 8.4 运行方式

```bash
cd source/04_rag/03_embeddings

python -m pip install -r requirements.txt
python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python 04_real_embeddings.py
python 05_semantic_search.py
python -m unittest discover -s tests
```

### 8.5 推荐运行顺序

建议先跑：

```bash
python 01_embed_chunks.py
```

你最先要建立的直觉是：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- 第三章先讲向量契约，再讲真实 endpoint
- 真实 embeddings 接入不是为了替换 toy provider，而是为了补桥接层

### 8.6 第一步：`01_embed_chunks.py`

跑 [01_embed_chunks.py](../../source/04_rag/03_embeddings/01_embed_chunks.py) 时：

- `chunk_id / document_id / metadata` 被保留下来
- 第三章新增的是 `provider_name / model_name / dimensions / vector`
- `EmbeddedChunk` 看起来像“保留原始 chunk 的增强版”

这一节真正要看的不是“打印了几个浮点数”，而是：

- 哪些字段是第二章继承来的
- 哪些字段是第三章新增的
- 第三章输出对第四章向量存储的准备作用

### 8.7 第二步：`02_compare_similarity.py`

跑 [02_compare_similarity.py](../../source/04_rag/03_embeddings/02_compare_similarity.py) 时：

- query 会先变成 query vector
- chunk 会先变成 document vectors
- 排序结果仍然保留 chunk 身份
- “如何申请退费？” 应该更接近退款规则 chunk

这里最该建立的直觉不是“相似度分数是多少”，而是：

> 第三章的排序是拿 query vector 和 document vectors 做比较，而不是直接拿原文字符串做比较。

### 8.8 第三步：`03_query_vs_document.py`

跑 [03_query_vs_document.py](../../source/04_rag/03_embeddings/03_query_vs_document.py) 时：

- toy provider 下，同一段文本走 query/document 两条路径时，结果可以不同
- 它们不同不代表不可比较
- query/document 的 mode buckets 可以不同
- 但它们仍然属于同一 provider/model 空间

### 8.9 第四步：`04_real_embeddings.py`

跑 [04_real_embeddings.py](../../source/04_rag/03_embeddings/04_real_embeddings.py) 时：

- 你会看到真实或 mock embeddings endpoint 的 `provider / model / dimensions`
- 你会看到 `embed_query / embed_documents` 仍然保留两个接口
- 你会看到对真实 embeddings 来说，重点已经转成维度、批量和契约
- 你会看到没配环境变量时会自动回退到 mock semantic client

### 8.10 第五步：`05_semantic_search.py`

跑 [05_semantic_search.py](../../source/04_rag/03_embeddings/05_semantic_search.py) 时：

- 你会看到一条 toy provider 的已知缺口
- 你会看到 semantic provider 更可能把它排到 metadata chunk
- 你会看到桥接案例不是为了否定 toy provider，而是为了说明真实语义空间的增量价值

### 8.11 测试：`tests/test_embeddings.py`

测试会锁定第三章最重要的几件事：

1. demo chunks 仍然保留第二章风格的 metadata
2. toy provider 维度固定
3. query/document 两条路径在 toy provider 下不同但可比较
4. `EmbeddedChunk` 保留原始 chunk 身份
5. local search cases 仍然稳定
6. semantic provider 能修正显式保留的 known gap
7. fake client 能走通 OpenAI-compatible provider
8. 错误响应形态、错误数量、维度漂移会直接失败
9. 空输入和零向量边界有明确行为

### 8.12 第三章最小回归集

第三章现在有两层回归样例：

1. [source_chunks.json](../../source/04_rag/03_embeddings/data/source_chunks.json)
2. [search_cases.json](../../source/04_rag/03_embeddings/data/search_cases.json)

其中 `search_cases.json` 里会保留一条明确的桥接坏例：

```json
{
  "question": "为什么文档块要记录出处？",
  "local_expected_top_chunk": "refund:0",
  "semantic_expected_top_chunk": "metadata:0"
}
```

这不是完整评估体系，但已经足够锁定：

1. toy provider 的主线稳定性
2. 最小语义排序的稳定性
3. 真实 embedding adapter 的契约保持情况
4. 已知坏例的显式保留状态

### 8.13 本章代码刻意简化的范围

这一章的实现刻意简化了五件事：

1. toy provider 仍然是本地最小实现
2. 真实 provider 只补 OpenAI-compatible embeddings 桥接
3. 向量比较只做最小 cosine similarity
4. 不写向量数据库
5. 不做复杂模型基准评测

这是故意的。

因为本章要先把下面这件事学会：

> 第三章解决的是“向量来源与可比较性”，不是“向量存储、查询和维护”。

### 8.14 第三章的重点失败案例

第三章至少要刻意看四类失败：

1. provider 契约失败
   - 向量数量和输入数量不匹配
   - 响应形状不符合预期

2. 维度漂移失败
   - query vector 维度不对
   - document vectors 前后维度不一致

3. 向量空间混用失败
   - query 和 document 向量不是同一个 provider/model 空间

4. toy provider 语义缺口
   - `为什么文档块要记录出处？` 在 local provider 下会先命中错误 chunk
   - 这不是 bug 修完就结束，而是第三章真实 embedding 桥接存在的理由

这些失败案例很重要，因为它们会帮你分清：

- 哪些是章节边界
- 哪些是向量层不变量
- 哪些变化会直接影响后续章节

### 8.15 建议你主动改的地方

如果你想把第三章真正学扎实，建议主动改三类地方再跑一遍：

1. 修改 `CONCEPT_GROUPS` 或 `STOPWORDS`，观察 local provider 排序如何变化
2. 改一个 `search_cases.json` 样例问题，观察 local/semantic top result 如何变化
3. 故意制造一个维度或 provider 空间不一致的 provider，观察测试如何直接失败

这样你会真正把“chunk 资产、provider 契约、排序结果、桥接坏例”连在一起。

---

## 9. 常见疑惑与复盘问题

这一节把前面分散出现的“为什么”集中起来，适合在读完代码以后回头复盘。

### 9.1 向量化是不是只是调用一下 embeddings API

不是。第三章真正交付的不是“一组浮点数”，而是一层稳定向量接口：

- `SourceChunk` 身份要保留
- provider/model space 要显式
- query/document 要可比较
- 维度和数量错误要尽早失败

所以这一章解决的是“怎样稳定地把 chunk 变成可比较向量”，不是“怎样随便调一个 endpoint”。

### 9.2 为什么 `EmbeddedChunk` 不能替代 `SourceChunk`

因为向量不是孤立资产。

如果只剩向量，第四章就不知道自己在存哪一个 chunk，后面的引用、删除、回填和调试也没有稳定锚点。`EmbeddedChunk` 的正确理解是：在保留原始 chunk 身份的前提下，再补一层向量表示。

### 9.3 为什么 `embed_query()` 和 `embed_documents()` 不能混成一个接口

因为它们在系统里承担的角色不同。

document vector 代表知识库候选依据，query vector 代表用户当前查询意图。很多真实 provider 底层可能都走同一个 embeddings endpoint，但教学和工程上仍然值得保留两个语义入口，这样未来切模型、切 provider、切检索策略时边界更稳。

### 9.4 分开入口后，query/document 为什么还能比较

因为“入口不同”不等于“空间不同”。

第三章允许 query/document 在本地 toy provider 里保留少量角色差异，例如 mode buckets 不同；但它们仍然共享概念组、共享 hash buckets，并最终落在同一个 provider/model/dimensions 空间里。所以它们可以不同，但仍然可比较。

### 9.5 第三章为什么现在就要讲 provider 契约

因为一旦不在这一章把契约立住，第四章以后就会出现很多难排查的问题：

- 向量维度漂移
- 返回数量和输入不一致
- query/document 混用不同 provider 或 model
- 存储层写入后才发现空间不一致

第三章就是把这些问题尽量前置。

### 9.6 toy provider 和真实 provider 到底是什么关系

它们在第三章里是桥接关系，不是替代关系。

toy provider 用来把 query/document、same space、mode buckets、known gap 这些教学重点显式暴露出来；真实 provider 用来补充真实维度、批量调用和更强语义空间。保留两者并列，教学上反而更清楚。

### 9.7 known gap 为什么要故意保留

因为坏例本身就是第三章教学内容的一部分。

如果只保留“能说明自己正确”的样例，你很难看出 toy provider 的边界，也很难理解真实 semantic provider 的增量价值。显式保留 known gap，能让你区分“可运行的教学模型”和“更强的真实语义空间”。

### 9.8 学这一章需要大量数学知识吗

做 RAG 工程应用，不需要先掌握大量高等数学。

你真正需要建立的是几个数学直觉：

- 向量：一串固定长度的数字
- 维度：这串数字里的每一个位置
- 相似度：两个向量方向越接近，文本越可能相关
- 归一化：把向量长度统一，减少文本长短带来的干扰
- 余弦相似度：看两个向量“方向像不像”

如果目标是训练 embedding 模型、研究模型结构，那会需要更多线性代数、概率、优化和神经网络知识。

但如果目标是把 RAG 系统搭起来，先记住这条链路就够用了：

```text
文本 -> embedding model -> 固定长度向量 -> 相似度计算 -> 排序结果
```

### 9.9 向量是不是在判断用户问题偏向什么类型

这个理解方向基本是对的，但要稍微修正一下。

Embedding 不是直接判断：

```text
这是退款问题 / 这是试学问题 / 这是 metadata 问题
```

它更像是把问题放进一个向量空间里，然后看它和哪些文档块的向量更接近。

比如用户问：

```text
如何申请退费？
```

系统会先把它变成 query vector。知识库里的每个 chunk 也会提前变成 document vector。

然后比较：

```text
query vector vs 退款政策 chunk vector
query vector vs 试学政策 chunk vector
query vector vs metadata 规则 chunk vector
```

谁更接近，谁就排在前面。

所以 embedding 更准确的理解是“相似度空间”，不是简单分类器。

### 9.10 向量维度是不是只要和业务匹配就可以

要分两种情况。

在本章的 toy provider 里，维度确实是人为设计的：

```text
第 0 维：退款
第 1 维：试学
第 2 维：metadata
第 3 维：stable id
...
```

这种情况下，维度设计当然应该服务于教学目标和业务概念。

但生产级 embedding 通常不是这样。

真实 embedding 模型里，维度不是人工定义成“第几维代表什么”。比如某个模型输出 1536 维，另一个模型输出 1024 维，这些维度是模型训练出来的，单独某一维通常没有稳定、可解释的人类含义。

可以这样区分：

```text
toy embedding：维度是人手动设计的，可解释
真实 embedding：维度是模型训练得到的，不一定单维可解释
```

所以真实开发中，通常不是自己设计每一个维度，而是：

- 选择合适的 embedding 模型
- 控制 chunk 切分方式
- 保留 metadata
- 设计检索策略
- 设计 rerank 或 hybrid search
- 必要时微调模型或换模型

业务匹配主要体现在围绕 embedding 的系统设计，而不是手工规定“第几维代表什么”。

### 9.11 hash bucket 和角色区是不是也是向量设计方案

是。

本章代码里的 hash bucket 是一种明确的向量设计方案：

```python
bucket = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % HASH_BUCKETS
vector[hash_offset + bucket] += 0.25
```

它的作用是：

```text
概念组里没有覆盖到的词，不要完全丢掉。
把它们压缩进几个 hash bucket，保留一点文本分布痕迹。
```

这和机器学习里的 feature hashing 思想相近，可以理解成“特征哈希”。

比如代码没有专门给这些词设计概念维度：

```text
购买后
7 天
学习进度
工作日
助教
```

如果完全丢掉，文本就太粗糙。所以 hash bucket 相当于说：

```text
我不知道这些词具体属于哪个业务概念，
但我仍然希望它们对向量有一点影响。
```

这不是精确语义，只是弱信号。

最后的 query/document 角色区也是向量设计方案：

```text
倒数第 2 维：query 角色
倒数第 1 维：document 角色
```

它不是为了提高真实检索效果，而是为了教学上让你看到：

```text
query 和 document 可以走不同入口，
但仍然要落在同一个向量空间里。
```

真实模型里也有类似思想，但实现方式不同。有些模型会要求你给文本加前缀：

```text
query: 如何申请退费？
passage: 购买后 7 天内可以申请退款
```

这和本章代码里的 role bucket 在思想上有点像：都是在告诉模型“这段文本现在扮演什么角色”。

### 9.12 embedding 和线性代数有什么关系

你的直觉是对的。embedding 和线性代数有很强关系，因为它核心就是：

```text
高维向量空间里的点、方向、距离、相似度
```

一些对应关系：

| 本章概念 | 线性代数直觉 |
|----------|--------------|
| embedding vector | 向量 |
| dimensions | 向量维度 |
| cosine similarity | 夹角余弦 |
| normalize | 单位向量 |
| dot product | 点积 |
| nearest neighbors | 向量空间中找最近的点 |

不过你不需要先把线性代数完整学一遍才能做 RAG。

先建立这个直觉就够了：

```text
语义相近的文本，在向量空间里方向更接近。
```

后面再遇到 cosine、dot product、ANN、向量数据库，就不会完全陌生。

### 9.13 生产级 embedding 是不是有专门工具或库

是的。真实开发中一般不会像本章 toy provider 这样手写 `_embed()`。

常见做法是直接使用已经训练好的 embedding 模型或服务，例如：

- OpenAI embeddings API
- DashScope / 通义千问 embedding
- Cohere embedding
- Voyage embedding
- Jina embedding
- BGE 系列模型
- E5 系列模型
- sentence-transformers
- HuggingFace 上的 embedding 模型

这些模型或服务负责：

```text
文本 -> 高维向量
```

公司内部更多是在做这些事情：

- 选择哪个 embedding 模型
- 怎么切 chunk
- metadata 怎么保留
- query 怎么改写
- top_k 取多少
- 是否加关键词检索
- 是否加 rerank
- 是否根据业务过滤
- 是否做模型微调

所以生产里大多数时候不是自己设计向量每一维，而是选择一个已经训练好的 embedding 模型，然后围绕它设计业务检索流程。

### 9.14 公司会不会根据业务动态决定向量处理逻辑

会，但通常不是“动态设计维度”。

更常见的是在这些层面做业务处理：

1. 文档切分策略
   合同、客服 FAQ、代码文档、论文，切法不同。

2. metadata 设计
   `source`、`tenant_id`、`product_id`、权限、时间、类别。

3. 检索策略
   只做向量检索，还是 keyword + vector 混合检索。

4. rerank
   先召回 50 条，再用 reranker 精排前 5 条。

5. query rewrite
   把用户问题改写得更适合检索。

6. 过滤规则
   只检索当前用户有权限看的文档。

7. 模型选择或微调
   法律、医疗、代码、金融可能选择不同 embedding 模型。

所以业务匹配主要体现在“围绕 embedding 的系统设计”，而不是手动规定“第几维代表什么”。

### 9.15 本章是不是在学 embedding 底层

是，但要加一个限定：

```text
这里学的是 embedding 的底层思想，不是真实神经网络 embedding 的完整内部实现。
```

当前 toy provider 相当于把真实 embedding 里黑盒的东西拆成了可解释版本：

```text
真实模型里的语义学习
-> 这里用 CONCEPT_GROUPS 模拟

真实模型里的词分布和上下文信息
-> 这里用 hash buckets 模拟

真实模型里的 query/document 角色差异
-> 这里用 mode buckets 模拟

真实模型里的向量空间比较
-> 这里用 normalize + cosine similarity 演示
```

所以它不是生产实现，但它非常适合学习底层心智模型。

你可以把它理解成：

```text
这不是一台真正的发动机，
而是一台透明教学模型，
让你看见发动机大概有哪些关键部件。
```

更准确地总结是：

```text
embedding 是把文本映射到固定长度向量空间里的过程。

toy embedding 可以人为设计维度，让每一维对应某些业务概念，方便教学和观察。

真实 embedding 通常不是人工设计每一维，而是由模型训练得到高维表示。

业务系统通常不直接设计向量维度，而是选择 embedding 模型，并设计 chunk、metadata、检索、过滤、rerank 等流程。

向量之间通过 cosine similarity / dot product 等方式比较，越接近的文本越可能语义相关。

当前代码是在把 embedding 的关键概念拆开，让学习者看清楚 query/document、same space、维度、归一化和相似度排序这些底层思想。
```

---

## 10. 本章掌握检查清单

- 第三章只增加向量层，不重做输入管道
- `EmbeddedChunk` 必须保留 `SourceChunk` 的身份和 metadata
- `embed_query()` 和 `embed_documents()` 不应混成模糊接口
- query/document 必须落在同一向量空间里
- 真实 embeddings 和 chat completions 虽然都走 OpenAI-compatible，但工程关注点完全不同
- provider 契约错误应该在第三章直接失败
- 第三章开始建立最小回归和 known gap 视角
- toy provider 和真实 provider 在同一章里形成桥接关系，而不是互相替代

---

## 11. 下一章

第四章开始进入向量存储主题：

- 向量写入
- top-k 查询
- 删除和过滤

也就是说，第四章处理的是“向量存储、查询和维护”。
