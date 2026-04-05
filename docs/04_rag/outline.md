# RAG 学习大纲

> 目标：掌握检索增强生成技术，系统理解文档处理、索引构建、检索优化、评估与 RAG 工程落地

---

## 课程定位

- 本课程聚焦 **检索系统工程**，不是系统学习 LangChain 全家桶。
- 你会在本课程里使用 LangChain，但重点是把它当成 **RAG 组件的工程封装层**，而不是框架本身。
- LangChain 的核心抽象与 LCEL 统一放在 [03_foundation/outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md) 系统学习。
- `Agentic RAG` 在本课程只做概念认知和边界判断，详细实现放到 [05_agent/outline.md](/Users/linruiqiang/work/ai_application/docs/05_agent/outline.md)。

## 学习前提

- 已完成 [02_llm/outline.md](/Users/linruiqiang/work/ai_application/docs/02_llm/outline.md)
- 建议先完成 [03_foundation/outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md)
- 已理解 `Document / Retriever / Runnable` 这些基础抽象

## 本课程回答什么问题

- 文档怎么切，切多大，怎么保留结构和元数据？
- Embedding 和向量数据库怎么选？
- 检索效果不好时该调哪里？
- Rerank、混合检索、多查询、HyDE 在什么情况下值得用？
- 如何把 RAG 做成可运行、可评估、可优化的业务系统？

## 一、RAG 基础概念

### 1. 什么是 RAG

#### 知识点

1. **RAG 定义**
   - Retrieval-Augmented Generation（检索增强生成）
   - 为什么需要 RAG：解决 LLM 的知识局限性
   - RAG vs 微调 vs 长上下文

2. **RAG 的优势**
   - 知识可更新
   - 减少幻觉
   - 可追溯来源
   - 成本可控

3. **RAG 应用场景**
   - 企业知识库问答
   - 文档问答
   - 客服机器人
   - 法律/医疗辅助

4. **RAG 架构概览**
   ```
   文档 → 切分 → 向量化 → 向量数据库
                              ↓
   用户问题 → 向量化 → 相似度检索 → Top-K 文档
                              ↓
   问题 + 检索结果 → LLM → 生成答案
   ```

#### 实践练习

```python
# 1. 画出 RAG 架构图
# 理解数据流向

# 2. 对比分析
# 列出 RAG vs 微调 的 5 个区别点

# 3. 场景判断
# 以下场景适合 RAG 还是微调？
# - 客服机器人（产品更新频繁）
# - 代码补全（固定语言风格）
# - 法律文书生成（需要引用法条）
# - 角色扮演聊天（固定人设）
```

---

### 综合案例：RAG 架构设计

```python
# 为一个在线教育平台设计 RAG 架构
#
# 需求分析：
# 1. 支持课程资料问答（PDF、PPT、视频字幕）
# 2. 需要显示答案来源（课程名、章节）
# 3. 支持多语言（中英文）
# 4. 响应时间 < 3 秒
#
# 设计要求：
# 1. 画出完整架构图
# 2. 选择合适的技术栈（向量数据库、Embedding 模型）
# 3. 设计文档处理流程
# 4. 设计检索策略
# 5. 估算成本
```

---

## 二、文档处理

### 2. 文档加载

#### 知识点

1. **常见文档格式**
   - TXT / Markdown
   - PDF
   - Word / Excel
   - HTML / 网页

2. **加载工具**
   - LangChain DocumentLoaders
   - PyPDF2 / pdfplumber
   - python-docx
   - BeautifulSoup

3. **文档结构**
   - Document 对象：page_content + metadata
   - 元数据的作用

#### 实战案例

```python
# 1. 加载 TXT 文件
from langchain_community.document_loaders import TextLoader

loader = TextLoader("example.txt")
documents = loader.load()

# 2. 加载 PDF 文件
# 使用 PyPDFLoader 或 pdfplumber

# 3. 加载目录下所有文档
# 使用 DirectoryLoader

# 4. 提取网页内容
# 使用 WebBaseLoader 或自定义爬虫
```

---

### 3. 文本切分

#### 知识点

1. **为什么需要切分**
   - 模型上下文限制
   - 检索精度
   - 噪声控制

2. **切分策略**
   - 固定长度切分
   - 递归字符切分（推荐）
   - 语义切分
   - 按段落/章节切分

3. **关键参数**
   - chunk_size：块大小
   - chunk_overlap：重叠大小
   - 分隔符选择

4. **LangChain 切分器**
   - RecursiveCharacterTextSplitter
   - CharacterTextSplitter
   - MarkdownHeaderTextSplitter
   - 代码切分器

#### 实战案例

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 基础切分
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)

chunks = text_splitter.split_text(long_text)

# 2. 切分 PDF 文档
# 加载 PDF → 切分 → 查看切分结果

# 3. Markdown 按标题切分
# 使用 MarkdownHeaderTextSplitter
# 保留标题层级信息

# 4. 对比不同 chunk_size 的效果
# 同一文档，chunk_size=200 vs 500 vs 1000
# 观察检索效果差异
```

---

### 4. 元数据管理

#### 知识点

1. **元数据的作用**
   - 过滤检索结果
   - 显示来源
   - 排序依据

2. **常见元数据字段**
   - source：文件路径
   - page：页码
   - title：标题
   - timestamp：时间戳
   - category：分类

3. **元数据注入**
   - 加载时自动提取
   - 切分后添加
   - 自定义字段

#### 实战案例

```python
# 1. 为文档块添加元数据
from langchain_core.documents import Document

chunk = Document(
    page_content="这是文档内容",
    metadata={
        "source": "doc.pdf",
        "page": 1,
        "category": "产品手册"
    }
)

# 2. 批量添加元数据
# 为所有切分后的块添加统一元数据

# 3. 基于元数据过滤
# 只检索特定分类的文档
```

---

### 综合案例：文档处理流水线

```python
# 实现一个通用的文档处理流水线
#
# 功能要求：
# 1. 支持多种格式（PDF、Word、TXT、Markdown）
# 2. 自动检测文件类型
# 3. 智能切分（根据文档类型选择策略）
# 4. 自动提取和注入元数据
# 5. 输出处理统计信息
#
# 使用示例：
# pipeline = DocumentPipeline(
#     chunk_size=500,
#     chunk_overlap=50
# )
#
# result = pipeline.process("document.pdf")
# print(f"共处理 {result.total_pages} 页")
# print(f"生成 {result.total_chunks} 个文档块")
# for chunk in result.chunks[:3]:
#     print(f"- {chunk.metadata}")
#
# 技术要点：
# - 文件类型检测
# - 多种 Loader 封装
# - 切分策略选择
# - 元数据提取
#
# 扩展方向：
# - 添加更多格式支持
# - 添加 OCR 支持
# - 添加表格提取
```

---

## 三、向量化

### 5. Embedding 基础

#### 知识点

1. **什么是 Embedding**
   - 文本的向量表示
   - 语义相似度 = 向量距离
   - 维度：通常 768-1536 维

2. **相似度计算**
   - 余弦相似度（最常用）
   - 欧氏距离
   - 点积

3. **Embedding 模型选择**

| 模型 | 维度 | 特点 |
|------|------|------|
| OpenAI text-embedding-3-small | 1536 | 性价比高 |
| OpenAI text-embedding-3-large | 3072 | 效果最好 |
| BGE-large-zh | 1024 | 中文优秀 |
| M3E | 768 | 国产开源 |

#### 实践练习

```python
from openai import OpenAI
import numpy as np

client = OpenAI()

# 1. 生成 Embedding
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="你好，世界"
)
embedding = response.data[0].embedding

# 2. 计算相似度
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 对比相似文本和不同文本的相似度
text1 = "苹果是一种水果"
text2 = "香蕉是一种水果"
text3 = "今天天气很好"

# 3. 找最相似的文档
# 给定问题和多个文档，找出最相似的一个
```

---

### 6. 基于 LangChain 的 Embedding 接入

#### 知识点

1. **LangChain Embedding 接口**
   - embed_documents：批量文档
   - embed_query：单个查询

2. **支持的模型**
   - OpenAIEmbeddings
   - HuggingFaceEmbeddings
   - 自定义模型

3. **本地模型**
   - sentence-transformers
   - BGE / M3E 中文模型

#### 实战案例

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# 1. 使用 OpenAI Embedding
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector = embeddings.embed_query("你好")

# 2. 使用本地模型
local_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-zh-v1.5"
)

# 3. 批量 Embedding
texts = ["文本1", "文本2", "文本3"]
vectors = embeddings.embed_documents(texts)

# 4. 对比不同模型效果
# 同一批文本，对比 OpenAI vs BGE 的检索效果
```

---

### 综合案例：语义搜索引擎

```python
# 实现一个简单的语义搜索引擎
#
# 功能要求：
# 1. 支持添加文档到索引
# 2. 支持语义搜索（返回最相似的 N 个文档）
# 3. 支持相似度阈值过滤
# 4. 支持本地模型和 API 模型切换
#
# 使用示例：
# engine = SemanticSearchEngine(embedding_model="bge")
#
# # 添加文档
# engine.add_documents([
#     "Python 是一种编程语言",
#     "机器学习是人工智能的分支",
#     "向量数据库用于存储嵌入向量"
# ])
#
# # 搜索
# results = engine.search("什么是 AI", top_k=2)
# for doc, score in results:
#     print(f"{score:.3f}: {doc}")
#
# 技术要点：
# - Embedding 模型封装
# - 向量计算和比较
# - 结果排序和过滤
#
# 扩展方向（下一章完善）：
# - 集成向量数据库
# - 添加持久化
# - 添加批量处理
```

---

## 四、向量数据库

### 7. 向量数据库基础

#### 知识点

1. **什么是向量数据库**
   - 专门存储和检索向量的数据库
   - 支持 ANN（近似最近邻）搜索
   - 高效的向量索引

2. **主流向量数据库**

| 数据库 | 特点 | 适用场景 |
|--------|------|----------|
| Chroma | 轻量、易用 | 开发/小项目 |
| FAISS | Meta开源、纯内存 | 本地高性能 |
| Pinecone | 云服务、免运维 | 生产环境 |
| Milvus | 开源、分布式 | 大规模生产 |
| Weaviate | 开源、功能丰富 | 企业级 |

3. **核心操作**
   - 插入向量
   - 相似度搜索
   - 删除/更新
   - 元数据过滤

#### 实践练习

```python
# 1. 理解向量索引
# ANN vs 精确搜索的权衡

# 2. 选择合适的向量数据库
# 根据场景选择：
# - 个人项目，10万文档
# - 企业项目，1000万文档
# - 需要云部署，不想运维
```

---

### 8. Chroma 实践

#### 知识点

1. **Chroma 基础**
   - 安装与初始化
   - 创建集合
   - 持久化存储

2. **CRUD 操作**
   - 添加文档
   - 查询文档
   - 更新文档
   - 删除文档

3. **元数据过滤**
   - where 条件
   - 复合过滤

#### 实战案例

```python
import chromadb
from chromadb.utils import embedding_functions

# 1. 初始化 Chroma
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection("my_docs")

# 2. 添加文档
collection.add(
    documents=["文档1内容", "文档2内容"],
    metadatas=[{"source": "a.txt"}, {"source": "b.txt"}],
    ids=["doc1", "doc2"]
)

# 3. 查询
results = collection.query(
    query_texts=["搜索内容"],
    n_results=3
)

# 4. 带元数据过滤的查询
results = collection.query(
    query_texts=["搜索内容"],
    where={"category": "产品手册"},
    n_results=3
)

# 5. 更新和删除
collection.update(ids=["doc1"], documents=["新内容"])
collection.delete(ids=["doc2"])
```

---

### 9. 基于 LangChain 的向量数据库接入

#### 知识点

1. **LangChain VectorStore 接口**
   - 统一的向量存储抽象
   - from_documents：从文档创建
   - similarity_search：相似度搜索
   - as_retriever：转为检索器

2. **支持的数据库**
   - Chroma
   - FAISS
   - Pinecone
   - Milvus

3. **最佳实践**
   - 批量插入
   - 增量更新
   - 错误处理

#### 实战案例

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 完整流程：加载 → 切分 → 向量化 → 存储
loader = TextLoader("doc.txt")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 2. 检索
results = vectorstore.similarity_search("查询内容", k=3)

# 3. 带分数的检索
results = vectorstore.similarity_search_with_score("查询内容", k=3)

# 4. 转为 Retriever
retriever = vectorstore.as_retriever(
    search_type="mmr",  # 或 "similarity"
    search_kwargs={"k": 3}
)
```

---

### 综合案例：向量存储管理器

```python
# 实现一个向量存储管理器（可扩展框架）
#
# 功能要求：
# 1. 支持多种向量数据库（Chroma、FAISS）
# 2. 统一的文档添加/删除/查询接口
# 3. 自动 Embedding 处理
# 4. 增量更新支持
# 5. 元数据管理
#
# 使用示例：
# manager = VectorStoreManager(
#     store_type="chroma",
#     embedding_model="openai",
#     persist_dir="./vector_db"
# )
#
# # 添加文档
# manager.add_documents(
#     documents=["文档1", "文档2"],
#     metadatas=[{"source": "a.txt"}, {"source": "b.txt"}],
#     ids=["1", "2"]
# )
#
# # 搜索
# results = manager.search("查询", top_k=5)
#
# # 删除
# manager.delete_document("1")
#
# 技术要点：
# - 数据库适配器模式
# - Embedding 模型封装
# - 增量更新逻辑
#
# 扩展方向（后续章节完善）：
# - 添加更多数据库支持（Pinecone、Milvus）
# - 添加批量导入
# - 添加索引优化
```

---

## 五、检索策略

### 10. 基础检索

#### 知识点

1. **检索方式**
   - similarity：相似度
   - mmr：最大边际相关性（多样性）
   - similarity_score_threshold：阈值过滤

2. **检索参数**
   - k：返回数量
   - fetch_k：MMR 候选数量
   - score_threshold：分数阈值

3. **检索评估**
   - 准确率
   - 召回率
   - MRR

#### 实战案例

```python
# 1. 对比不同检索方式
# 同一查询，对比 similarity vs mmr 的结果多样性

# 2. 调整 k 值
# k=1 vs k=5 vs k=10，观察答案质量变化

# 3. 设置分数阈值
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8, "k": 5}
)
# 观察阈值过高/过低的效果
```

---

### 11. 高级检索策略

#### 知识点

1. **Query 变换策略** 📌
   - **多查询生成**：LLM 生成多个相关查询，合并检索结果
   - **HyDE**（Hypothetical Document Embeddings）：先生成假设性答案再检索
   - **Query Decomposition**：复杂问题拆分为多个子问题
   - **Step-back Prompting**：先问更宽泛的问题再精确检索

2. **上下文压缩**
   - 压缩检索结果
   - 只保留相关部分
   - 减少噪声

3. **重排序（Rerank）**
   - 第一阶段：向量检索（粗筛）
   - 第二阶段：Rerank 模型（精排）
   - 提高准确率

4. **混合检索**
   - 关键词检索 + 向量检索
   - BM25 + Embedding
   - 取长补短

#### 实战案例

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers import EnsembleRetriever

# 1. 多查询检索
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)

# 1.5 HyDE 检索
# 用户问题 → LLM 生成假设性答案 → 用答案做 Embedding 检索
# 原理：假设性答案和真实文档在向量空间中更接近
hyde_prompt = "请回答以下问题（即使你不确定）：{question}"
# 生成假设答案 → Embedding → 检索

# 2. 上下文压缩
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# 3. 混合检索（需要 BM25）
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5]
)

# 4. 对比不同策略效果
# 使用相同测试集，评估各策略准确率
```

---

### 12. Rerank 重排序

#### 知识点

1. **为什么需要 Rerank**
   - 向量检索是粗筛
   - Rerank 模型更精确
   - 平衡速度和准确率

2. **Rerank 模型**
   - Cohere Rerank（API）
   - BGE Reranker（本地）
   - ColBERT

3. **Rerank 流程**
   ```
   Query → 向量检索 Top-K (K=50)
         → Rerank 模型重排
         → 返回 Top-N (N=5)
   ```

#### 实战案例

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank

# 1. 使用 Cohere Rerank
compressor = CohereRerank()
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# 2. 使用本地 BGE Reranker
from FlagEmbedding import FlagReranker
reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True)

scores = reranker.compute_score(
    [['query', 'doc1'], ['query', 'doc2']]
)

# 3. 对比有无 Rerank 的效果
# 记录检索时间和准确率
```

---

### 综合案例：智能检索引擎

```python
# 实现一个智能检索引擎（可扩展框架）
#
# 功能要求：
# 1. 支持多种检索策略（similarity、mmr、混合检索）
# 2. 可选 Rerank 加持
# 3. 元数据过滤
# 4. 检索结果缓存
# 5. 检索效果评估
#
# 使用示例：
# engine = SmartRetrievalEngine(
#     vectorstore=vectorstore,
#     strategy="hybrid",  # similarity / mmr / hybrid
#     rerank=True,
#     rerank_model="bge"
# )
#
# # 基础检索
# results = engine.retrieve("产品价格", top_k=5)
#
# # 带过滤的检索
# results = engine.retrieve(
#     "产品价格",
#     filter={"category": "产品手册"},
#     top_k=5
# )
#
# # 评估检索效果
# metrics = engine.evaluate(test_cases)
# print(f"召回率: {metrics.recall}")
# print(f"MRR: {metrics.mrr}")
#
# 技术要点：
# - 检索策略模式
# - Rerank 集成
# - 缓存机制
# - 评估指标计算
#
# 扩展方向：
# - 添加更多检索策略
# - 添加自适应策略选择
# - 添加 A/B 测试支持
```

---

## 六、RAG 生成

### 13. Prompt 模板设计

#### 知识点

1. **RAG Prompt 结构**
   ```
   系统角色
   + 检索到的上下文
   + 用户问题
   + 输出要求
   ```

2. **常见模板**
   - 基础问答
   - 带引用来源
   - 多轮对话

3. **Prompt 优化技巧**
   - 明确使用上下文
   - 处理"不知道"情况
   - 引用来源格式

#### 实战案例

```python
from langchain_core.prompts import ChatPromptTemplate

# 1. 基础 RAG Prompt
template = """
你是一个有帮助的助手。请根据以下上下文回答问题。
如果上下文中没有答案，请说"我不知道"。

上下文：
{context}

问题：{question}

答案：
"""

prompt = ChatPromptTemplate.from_template(template)

# 2. 带引用的 Prompt
template_with_citation = """
根据以下文档片段回答问题。
在答案中标注信息来源，格式为 [文档1]、[文档2]。

文档：
{context}

问题：{question}
"""

# 3. 多语言 Prompt
# 根据问题语言自动匹配模板
```

---

### 14. 基于 LCEL 的 RAG Chain 构建

#### 知识点

1. **LangChain Chain**
   - 检索 + 生成 的完整流程
   - LCEL（LangChain Expression Language）

2. **基础 RAG Chain**
   ```
   retriever → context → prompt → llm → answer
   ```

3. **自定义 Chain**
   - 添加处理步骤
   - 返回中间结果

#### 实战案例

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. 基础 RAG Chain
template = """根据上下文回答问题：
{context}

问题：{question}
"""
prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(model="gpt-4o-mini")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

response = rag_chain.invoke("你的问题")

# 2. 返回来源的 Chain
# 同时返回答案和来源文档

# 3. 流式输出 Chain
for chunk in rag_chain.stream("你的问题"):
    print(chunk, end="", flush=True)
```

---

### 15. 完整 RAG 应用

#### 知识点

1. **应用架构**
   ```
   用户请求 → FastAPI → RAG Pipeline → 响应
                     ↓
              向量数据库 ← 文档索引
   ```

2. **功能模块**
   - 文档上传与处理
   - 向量索引管理
   - 问答接口
   - 对话历史

3. **工程化考虑**
   - 异步处理
   - 错误处理
   - 日志记录
   - API 设计

#### 实战案例

```python
# 实现完整的 RAG 问答 API

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    question: str
    top_k: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]

# 1. 文档上传接口
@app.post("/documents/upload")
async def upload_document(file: UploadFile):
    # 接收文件 → 处理 → 切分 → 向量化 → 存储
    pass

# 2. 问答接口
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # 检索 → 生成 → 返回答案和来源
    pass

# 3. 流式问答接口
@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    # SSE 流式返回
    pass

# 4. 文档管理接口
@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    # 删除文档及其向量
    pass
```

---

### 综合案例：RAG 问答服务

```python
# 实现一个完整的 RAG 问答服务（可扩展框架）
#
# 功能要求：
# 1. 文档管理（上传、删除、列表）
# 2. 问答接口（普通 + 流式）
# 3. 多轮对话支持
# 4. 来源追溯
# 5. 错误处理
#
# 使用示例：
# service = RAGService(
#     vectorstore=vectorstore,
#     llm_model="gpt-4o-mini"
# )
#
# # 上传文档
# service.upload_document("manual.pdf")
#
# # 问答
# result = service.query("产品价格是多少？")
# print(result.answer)
# print(result.sources)
#
# # 流式问答
# for chunk in service.query_stream("如何退款？"):
#     print(chunk, end="")
#
# 技术要点：
# - 文档处理流水线
# - RAG Chain 构建
# - 流式输出
# - 错误处理
#
# 扩展方向（下一章完善）：
# - 添加检索优化
# - 添加评估功能
# - 添加多知识库支持
```

---

## 七、RAG 优化

### 16. 检索效果优化

#### 知识点

1. **常见问题**
   - 检索不到相关文档
   - 检索结果噪声多
   - 上下文超长

2. **优化方向**
   - 切分策略优化
   - Embedding 模型选择
   - 检索参数调优
   - Rerank 加持

3. **评估方法**
   - 人工评估
   - 自动化评估
   - A/B 测试

#### 实战案例

```python
# 1. 评估检索效果
test_cases = [
    {"question": "产品价格是多少？", "expected_docs": ["price.txt"]},
    {"question": "如何退款？", "expected_docs": ["refund.txt"]},
]

def evaluate_retrieval(test_cases, retriever):
    # 计算召回率
    pass

# 2. 调优实验
# 实验不同参数组合，找出最佳配置

configs = [
    {"chunk_size": 300, "overlap": 30, "k": 5},
    {"chunk_size": 500, "overlap": 50, "k": 5},
    {"chunk_size": 500, "overlap": 50, "k": 10},
]

# 3. 对比不同 Embedding 模型
# OpenAI vs BGE vs M3E
```

---

### 17. 生成质量优化

#### 知识点

1. **常见问题**
   - 幻觉（编造信息）
   - 不引用来源
   - 答案过于简略/冗长

2. **优化方法**
   - Prompt 工程
   - 引用验证
   - 答案校验

3. **后处理**
   - 事实核查
   - 格式规范化
   - 敏感词过滤

#### 实战案例

```python
# 1. 幻觉检测
def detect_hallucination(answer: str, sources: list[str]) -> bool:
    # 检查答案是否在来源中有依据
    pass

# 2. 强制引用
prompt = """
回答问题时必须引用来源，格式：[来源1][来源2]
如果无法从给定文档中找到答案，请回答"根据现有资料无法回答"。
"""

# 3. 答案质量评估
def evaluate_answer(answer: str, question: str, ground_truth: str) -> dict:
    # 返回评分：相关性、准确性、完整性
    pass
```

---

### 综合案例：RAG 效果评估工具

```python
# 实现一个 RAG 效果评估工具
#
# 功能要求：
# 1. 检索效果评估（召回率、MRR）
# 2. 生成质量评估（相关性、准确性）
# 3. 端到端效果评估
# 4. 生成评估报告
# 5. 支持不同配置对比
#
# 使用示例：
# evaluator = RAGEvaluator(rag_service)
#
# # 添加测试用例
# evaluator.add_test_case(
#     question="产品价格是多少？",
#     expected_answer="产品价格为299元",
#     expected_sources=["price.txt"]
# )
#
# # 运行评估
# report = evaluator.run()
# print(f"检索召回率: {report.retrieval_recall}")
# print(f"答案准确率: {report.answer_accuracy}")
#
# # 对比不同配置
# evaluator.compare_configs([
#     {"chunk_size": 300, "model": "openai"},
#     {"chunk_size": 500, "model": "bge"}
# ])
#
# 技术要点：
# - 测试用例管理
# - 评估指标计算
# - 报告生成
# - 配置对比
```

---

## 7.5、进阶 RAG 方向

### 17.5 GraphRAG ⚡

#### 知识点

1. **什么是 GraphRAG**
   - 微软提出的知识图谱 + RAG 方案
   - 解决多跳推理问题（"A 公司 CEO 的母校是哪里？"）
   - 构建实体关系图，辅助向量检索

2. **与传统 RAG 的区别**

| 维度 | 传统 RAG | GraphRAG |
|------|---------|----------|
| 数据结构 | 平铺文档块 | 实体-关系图 |
| 检索方式 | 向量相似度 | 图遍历 + 向量 |
| 多跳推理 | 弱 | 强 |
| 构建成本 | 低 | 高 |

3. **适用场景**
   - 需要跨文档关联推理
   - 实体关系复杂的领域（法律、医疗、金融）
   - 知识图谱已有的场景

#### 实践练习

```python
# 1. 理解 GraphRAG 架构
# 画出 GraphRAG 的数据流：
# 文档 → 实体提取 → 关系构建 → 知识图谱
#                                    ↓
# 用户问题 → 实体识别 → 图检索 + 向量检索 → 生成答案

# 2. 场景判断
# 以下场景适合传统 RAG 还是 GraphRAG？
# - 单文档 FAQ 问答（传统 RAG）
# - "某公司所有子公司的营收总和"（GraphRAG）
# - 产品手册查询（传统 RAG）
```

---

### 17.6 Agentic RAG（概念认知，详细实现放到 Agent 课程）📌

#### 知识点

1. **什么是 Agentic RAG**
   - 用 Agent 增强 RAG 流程
   - Agent 动态决策：是否需要检索、检索结果是否足够、是否需要换策略

2. **与传统 RAG 的区别**
   - 传统 RAG：固定流程（检索 → 生成）
   - Agentic RAG：动态流程（Agent 自主决定何时检索、如何检索）

3. **典型流程**
   ```
   用户问题 → Agent 判断
     ├── 直接回答（无需检索）
     ├── 检索 → 评估结果
     │     ├── 结果足够 → 生成答案
     │     └── 结果不够 → 改写查询 → 重新检索
     └── 拆分子问题 → 分别检索 → 合并答案
   ```

4. **实现方式**
   - LangGraph 状态机实现
   - 检索作为 Agent 的 Tool
   - 本课程重点理解边界与价值，详细实现放到 Agent 课程

#### 实战案例

```python
# 1. 用 LangGraph 实现 Agentic RAG
# 定义节点：判断节点、检索节点、评估节点、生成节点
# 定义条件边：根据评估结果决定下一步

# 2. 检索质量评估
# Agent 判断检索结果是否回答了用户问题
# 不够 → 自动改写查询重试

# 3. 对比传统 RAG 和 Agentic RAG
# 同一批测试问题，对比两种方式的答案质量
```

---

## 八、综合项目

### 18. PDF 文档问答系统

```python
# 实现一个完整的 PDF 文档问答系统
#
# 功能要求：
# 1. 上传 PDF 文件
# 2. 自动切分和索引
# 3. 问答接口（支持流式）
# 4. 显示答案来源
# 5. 支持多文档
# 6. 文档管理（增删查）
#
# 技术要求：
# - FastAPI 后端
# - Chroma 向量数据库
# - LangChain RAG Chain
# - 错误处理和日志
#
# 进阶功能：
# - 支持多用户/多知识库
# - 支持混合检索
# - 添加 Rerank
# - 评估检索效果
```

---

### 19. 企业知识库

```python
# 实现一个企业知识库系统（可扩展框架）
#
# 功能模块：
# 1. 知识库管理
#    - 创建/删除知识库
#    - 上传多种格式文档（PDF/Word/TXT/Markdown）
#
# 2. 问答功能
#    - 单知识库问答
#    - 跨知识库问答
#    - 多轮对话
#
# 3. 管理后台
#    - 文档列表
#    - 问答日志
#    - 效果统计
#
# 4. API 接口
#    - RESTful API
#    - API Key 认证
#    - 限流控制
#
# 技术要求：
# - 分层架构
# - 配置管理
# - 日志和监控
# - 单元测试
#
# 扩展方向：
# - 前端界面
# - 多租户支持
# - 权限管理
# - 数据分析
```

---

## 学习资源

### 官方文档
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [Chroma 文档](https://docs.trychroma.com/)
- [LlamaIndex RAG](https://docs.llamaindex.ai/)

### 向量数据库
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [Milvus 文档](https://milvus.io/docs)
- [Pinecone 文档](https://docs.pinecone.io/)

### Embedding 模型
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) - 模型排行榜
- [BGE Models](https://huggingface.co/BAAI)
- [M3E Models](https://huggingface.co/moka-ai)

### 评估工具
- [Ragas](https://docs.ragas.io/) - RAG 评估框架
- [TruLens](https://www.trulens.org/) - LLM 应用评估

---

## 验收标准

完成本阶段学习后，你应该能够：

1. **解释** RAG 的原理和适用场景
2. **实现** 文档加载、切分、向量化、存储的完整流程
3. **构建** 基础的 RAG 问答系统
4. **优化** 检索效果（切分策略、Rerank、混合检索）
5. **部署** 一个可用的文档问答 API
6. **评估** RAG 系统的效果
