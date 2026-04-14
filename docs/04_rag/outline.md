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

## 与前后课程的衔接

### 与 02_llm 的关系

- `02_llm` 解决的是：怎么稳定调用模型、怎么管理消息、怎么做结构化输出、怎么控制成本与错误。
- 本课程承接这些基础能力，把“单次模型调用”升级成“检索 + 生成”的完整知识系统。
- 如果前面的 `Prompt / Structured Output / Token / Reliability` 不熟，这门课会很容易只停留在“能跑通”，很难进入优化阶段。

### 与 03_foundation 的关系

- `03_foundation` 提供的是本课程最重要的抽象底座：`Document / Retriever / Runnable / LCEL`。
- 本课程不再系统解释这些抽象为什么存在，而是默认你已经理解它们，并把它们用在真实 RAG 链路里。
- 可以把这门课理解成：把 `03_foundation` 里的通用抽象，落成一个可评估、可治理、可部署的检索系统。

### 与 06_application 的关系

- 后面的 [06_application/outline.md](/Users/lrq/work/ai_application/docs/06_application/outline.md) 不会重新讲一遍 RAG 原理，而是直接把这里的能力装进真实业务系统。
- 本课程产出的核心能力，会在后续项目里落到：知识库接入、检索链路、引用回答、效果回归、知识治理。
- 换句话说，这门课要先把“知识系统底座”做稳，后面的项目课才能把重点放在业务闭环和产品落地上。

### 本课程的边界

- 本课程重点是 **固定检索链路** 的设计、优化与治理。
- 多步骤动态决策、状态机编排、复杂工具协作，不在这里系统展开，放到 [05_agent/outline.md](/Users/lrq/work/ai_application/docs/05_agent/outline.md)。
- 业务系统级的权限、审计、工作台、人工协作、前后端整合，放到 [06_application/outline.md](/Users/lrq/work/ai_application/docs/06_application/outline.md)。

## 本课程回答什么问题

- 文档怎么切，切多大，怎么保留结构和元数据？
- Embedding 和向量数据库怎么选？
- 什么情况下应该用 `2-step RAG`、混合检索、Hosted File Search，什么时候不该过早上 `Agentic RAG`？
- 检索效果不好时该调哪里？
- Rerank、混合检索、多查询、HyDE 在什么情况下值得用？
- 如何从第一天就建立最小评估集，避免“调了很多但不知道是否变好”？
- 文档解析、增量更新、版本、删除一致性、ACL、多租户这些生产问题怎么处理？
- 如何把 RAG 做成可运行、可评估、可优化的业务系统？

## 开始前：先建立最小评估集 📌

### 1. RAG 评估与测试前置

#### 本节与前后课程的关系

- 承接前面的 `02_llm`：你已经学过结构化输出、错误处理、成本意识，这一节把这些能力收束成“可重复评估”的工程习惯。
- 依赖 `03_foundation`：后面每换 `Retriever / Runnable / Prompt`，都需要同一套评估尺子来判断变化是否有效。
- 服务后面的 `06_application`：项目实战里会真正需要离线评估、坏案例回流和版本回归，这一节先把方法论立住。
- 边界：这里先建立最小评估集，不展开完整 LLMOps 平台或企业级观测体系。

#### 知识点

1. **为什么评估要前置**
   - RAG 是系统工程，不是“换个 Prompt 看感觉”
   - 如果没有基线，后续改 `chunk_size / retriever / rerank / prompt` 都无法判断是否真的变好
   - 评估不是最后补作业，而是整个课程的实验尺子

2. **最小 Golden Set 怎么建**
   - 先收集 20-50 个真实问题
   - 每条样本至少包含：`question / expected_answer / expected_sources`
   - 对难题单独标记：多跳问题、模糊问题、无答案问题、需拒答问题

3. **要评什么**
   - 检索评估：召回率、MRR、命中来源
   - 生成评估：准确性、完整性、引用质量、拒答正确性
   - 端到端评估：答案是否解决业务问题，响应时间是否可接受

4. **什么时候回归**
   - 改切分策略时跑一次
   - 换 Embedding / Vector DB / Retriever 时跑一次
   - 改 Prompt / Rerank / 上下文压缩时跑一次
   - 上线前做一次固定回归

#### 实践练习

```python
# 1. 建一个最小 RAG golden set
golden_set = [
    {
        "question": "如何退款？",
        "expected_answer": "根据退款规则，用户需要先提交申请...",
        "expected_sources": ["refund_policy.md"],
    },
    {
        "question": "产品价格是多少？",
        "expected_answer": "标准版价格为 299 元",
        "expected_sources": ["pricing.pdf"],
    },
]

# 2. 先不追求自动打分完美
# 先把测试样本固定下来，并能重复跑

# 3. 记录每一轮实验配置
experiment_config = {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "embedding_model": "text-embedding-3-small",
    "retrieval_strategy": "similarity",
}

# 4. 后续每改一项，就在这套样本上回归
```

## 一、RAG 基础概念

### 2. 什么是 RAG

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

### 3. RAG 架构选型与边界判断 📌

#### 本节与前后课程的关系

- 承接 `02_llm` 的上下文窗口、成本控制和结构化输出认知，帮助你理解为什么不是所有问题都该直接做 RAG。
- 承接 `03_foundation` 的组件认知，把抽象层面的 `Retriever / Chain / Runnable` 转成真正的架构判断。
- 为 `06_application` 服务：后面的项目里会同时遇到 FAQ、规则库、公告解析等不同场景，这一节决定你选固定 RAG、混合检索，还是升级到更复杂方案。
- 边界：这里强调“什么时候该用什么”，不是展开讲 Agent 编排；动态决策留到 `05_agent`。

#### 知识点

1. **常见方案梯度**
   - 直接长上下文：材料少、问题少、无需索引时
   - 直接查现有知识源：本来就有 SQL / Elasticsearch / CMS / FAQ 系统时
   - `2-step RAG`：先召回，再生成，默认主线方案
   - `Hybrid RAG`：关键词 + 向量混合，适合术语、编号、产品名很多的场景
   - Hosted File Search：快速验证产品价值、减少自建检索工程时
   - `Agentic RAG`：需要动态判断、查询改写、多知识源路由时

2. **选型维度**
   - 数据是否经常更新
   - 是否需要来源引用
   - 是否需要复杂检索策略
   - 是否已有成熟数据系统
   - 团队是否真的有能力维护检索链路

3. **默认决策顺序**
   - 先判断能否直接用长上下文解决
   - 再判断能否直接查现有知识系统
   - 默认优先做稳定的 `2-step RAG`
   - 检索不稳时再加混合检索、Rerank、查询变换
   - 只有固定链路明显不够时，才升级到 `Agentic RAG`

4. **常见误区**
   - 还没把基础 RAG 做稳，就急着上 Agent
   - 本来结构化数据查询更合适，却硬塞进向量库
   - 只是想快速做 Demo，却过早搭整套索引平台

#### 实践练习

```python
# 判断以下场景更适合哪种方案
#
# 1. 用户上传 10 份 PDF，快速做问答 Demo
#    - 长上下文 / Hosted File Search / 自建 RAG？
#
# 2. 公司 FAQ 已经在 Elasticsearch 里
#    - 直接查现有系统 / 向量化重建？
#
# 3. 金融问答，问题里大量包含代码、简称、产品编号
#    - 向量检索 / 混合检索？
#
# 4. 复杂研究问题，需要判断是否继续检索、改写查询、拆分子问题
#    - 固定 RAG / Agentic RAG？
```

---

## 二、文档处理

### 4. 文档加载

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

### 5. 文本切分

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

### 6. 元数据管理

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

### 7. 数据生命周期与知识库治理 📌

#### 本节与前后课程的关系

- 前面的章节已经解决“如何把文档放进索引”，这一节开始解决“索引如何长期活着且不出错”。
- 它依赖前面文档处理、元数据、向量存储这些基础模块，但视角从“单次构建”切到“持续运营”。
- 后面的 `06_application` 会真正落地文档上传、删除、版本更新、知识库隔离、多租户管理，这一节是在为项目课的知识底座做准备。
- 边界：这里只建立治理意识和核心设计点，不把课程拉成完整后台平台开发课。

#### 知识点

1. **数据接入与增量更新**
   - 首次全量导入
   - 文档新增后的增量索引
   - 文档修改后的局部重建
   - 文档失效后的下线策略

2. **版本与删除一致性**
   - 文档版本号设计
   - `document_id / chunk_id` 如何稳定生成
   - 删除原文时，如何确保向量、缓存、元数据同步删除
   - 避免“旧文档还在召回、新文档已经展示”的不一致

3. **权限隔离与多租户**
   - 按用户 / 部门 / 知识库做 ACL
   - 检索阶段先做权限过滤，再做生成
   - 多租户环境避免知识串库

4. **复杂文档解析**
   - OCR 文档
   - 表格、图片、版面结构
   - 扫描件和网页混合内容
   - 非结构化和半结构化文档的不同处理策略

5. **生产环境常见难点**
   - 文档很多但质量不齐
   - 文档更新频繁
   - 同一内容多副本
   - 线上权限和知识库管理复杂

#### 实践练习

```python
# 设计一个知识库生命周期方案
#
# 要求：
# 1. 文档上传后生成稳定的 document_id 和 chunk_id
# 2. 文档更新时只重建受影响的块
# 3. 文档删除时同步删除向量索引和缓存
# 4. 支持按 tenant_id / department 过滤
# 5. 支持 OCR 文档和普通 PDF 两条处理链路
```

---

## 三、向量化

### 8. Embedding 基础

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

### 9. 基于 LangChain 的 Embedding 接入

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

### 10. 向量数据库基础

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

### 11. Chroma 实践

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

### 12. 基于 LangChain 的向量数据库接入

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

### 13. 基础检索

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

### 14. 高级检索策略

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

### 15. Rerank 重排序

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

### 16. 高级 Retriever（选读）

#### 本节与前后课程的关系

- 这一节建立在你已经掌握基础检索、查询变换、Rerank 之后，属于“在基础方案做稳之后的增强项”。
- 它和 `03_foundation` 的关系在于：你已经知道 Retriever 是统一抽象，这里进一步看到不同 Retriever 是如何在同一接口下解决不同问题。
- 对 `06_application` 来说，这些内容主要服务复杂知识库的召回优化，而不是第一版系统的必选项。
- 边界：这部分是选读增强，不应该取代前面稳定的基础 RAG 主线。

#### 知识点

1. **Self-Query Retriever**
   - 让 LLM 先把用户问题解析成“语义查询 + 元数据过滤”
   - 适合带分类、时间、作者、部门等字段的知识库

2. **Parent Document Retriever**
   - 检索时用小块提高召回
   - 返回时回到更大的父文档，降低碎片化上下文

3. **Multi-Vector Retriever**
   - 同一文档保存多种向量表示
   - 适合标题、摘要、正文分别表达不同语义的场景

4. **什么时候值得上**
   - 基础相似度检索已经稳定，但边界问题仍多
   - 知识库元数据足够丰富
   - 业务允许更复杂的索引构建和维护成本

#### 实战案例

```python
# 1. 对同一批文档，对比：
# - 普通 similarity retriever
# - self-query retriever
# - parent-document retriever
#
# 2. 观察哪类问题在高级 retriever 下明显受益
#
# 3. 记录复杂度代价：
# - 构建成本
# - 检索延迟
# - 配置复杂度
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

### 17. Prompt 模板设计

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

### 18. 基于 LCEL 的 RAG Chain 构建

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

### 19. 完整 RAG 应用

#### 知识点

1. **应用架构**
   ```
   用户请求 → FastAPI → RAG Pipeline → 响应
                     ↓
              向量数据库 ← 文档索引
   ```

2. **功能模块**
   - 文档上传与处理
   - 增量索引与版本管理
   - 向量索引管理
   - 问答接口
   - 对话历史
   - 权限与知识库隔离

3. **工程化考虑**
   - 异步处理
   - 错误处理
   - 日志记录
   - API 设计
   - 删除一致性
   - 权限校验

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

### 20. 检索效果优化

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
   - 基于课程开头建立的 golden set 做回归
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

### 21. 生成质量优化

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
# # 加载固定 golden set，后续所有实验都复用
# # evaluator.load_golden_set("evals/rag_golden_set.jsonl")
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

## 八、进阶 RAG 方向

### 22. GraphRAG ⚡

#### 本节与前后课程的关系

- 这一节是在传统 RAG 主线学完之后，补一个“什么时候需要更复杂知识表示”的进阶视角。
- 它承接 `03_foundation` 里关于上下文组织和信息表示的认知，也承接本课程前面关于检索链路的完整主线。
- 对 `06_application` 来说，只有当业务问题明显存在跨文档、多跳、实体关系推理时，才可能考虑这类方案。
- 边界：这里只做概念认知与场景判断，不在本课程里展开完整实现，避免主线发散。

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

### 23. Agentic RAG（概念认知，详细实现放到 Agent 课程）📌

#### 本节与前后课程的关系

- 这节是本课程和 [05_agent/outline.md](/Users/lrq/work/ai_application/docs/05_agent/outline.md) 的桥梁章节。
- 前面你已经学完固定 RAG，本节的目标不是立刻实现 Agent，而是先判断：什么时候固定链路已经不够，什么时候值得引入动态决策。
- 到 `05_agent` 中，你会真正把检索包装成工具、接入状态机和条件路由；到 `06_application` 中，它会进一步服务复杂业务流程。
- 边界：本课程只讲价值、边界和升级条件，不把主线从“稳定 RAG”带偏到“复杂编排”。

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

## 九、综合项目

### 24. PDF 文档问答系统

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

### 25. 企业知识库

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
# - 文档版本与删除一致性
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
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) - 评估与回归
- [OpenAI File Search](https://platform.openai.com/docs/guides/tools-file-search) - Hosted File Search 参考

---

## 验收标准

完成本阶段学习后，你应该能够：

1. **解释** RAG 的原理和适用场景
2. **实现** 文档加载、切分、向量化、存储的完整流程
3. **构建** 基础的 RAG 问答系统
4. **判断** 长上下文 / 现有知识源 / `2-step RAG` / Hybrid / Hosted File Search / Agentic RAG 的适用边界
5. **优化** 检索效果（切分策略、Rerank、混合检索、高级 Retriever）
6. **部署** 一个可用的文档问答 API
7. **评估** RAG 系统的效果，并基于 golden set 做回归
8. **理解** 增量索引、版本、删除一致性、ACL、多租户这些生产问题
