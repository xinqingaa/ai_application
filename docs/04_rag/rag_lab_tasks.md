# rag_lab 任务拆解

> 本节目标：把 `04_rag` 的九章学习文档对应到当前真实代码结构，明确每章代码职责、完成标准和最终项目收口方式。

---

## 1. 总任务顺序

`04_rag` 按九章推进，但当前仓库不是九个快照目录，而是“前六章独立代码 + 后三章正文待实现 + 最终 rag_lab 收口”的结构：

| 章节 | 对应主题 | 当前代码目录 | 状态 |
|------|----------|--------------|------|
| 1 | RAG 基础概念 | `source/04_rag/01_rag_basics/` | 已实现 |
| 2 | 文档处理 | `source/04_rag/02_document_processing/` | 已实现 |
| 3 | 向量化 | `source/04_rag/03_embeddings/` | 已实现 |
| 4 | 向量数据库 | `source/04_rag/04_vector_databases/` | 已实现 |
| 5 | 检索策略 | `source/04_rag/05_retrieval_strategies/` | 已实现 |
| 6 | RAG 生成 | `source/04_rag/06_rag_generation/` | 已实现 |
| 7 | RAG 优化 | 暂无代码目录 | 文档已完成，代码待实现 |
| 8 | 进阶 RAG 方向 | 暂无代码目录 | 文档已完成，代码待实现 |
| 9 | 综合项目 | `source/04_rag/rag_lab/` | 占位，整合待实现 |

最终完整项目：

```plain
source/04_rag/rag_lab/
```

只在第九章后整理形成。

## 2. 第一章：RAG 基础概念

### 对应文档

- [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)

### 对应代码

- `source/04_rag/01_rag_basics/`

### 目标

- 建立问题路由和方案边界意识
- 固定最小 RAG 数据流
- 区分直接回答、查系统和走 RAG

### 完成标准

- 能运行最小示例脚本
- 能解释路由为什么先于检索
- 能说明第一章为什么还不接真实 provider

## 3. 第二章：文档处理

### 对应文档

- [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)

### 对应代码

- `source/04_rag/02_document_processing/`

### 目标

- 实现文档加载
- 实现文本切分
- 实现 metadata 注入
- 实现稳定 `document_id / chunk_id`

### 完成标准

- 能加载至少一种文档格式
- 能打印切分结果
- 能验证 chunk id 稳定

## 4. 第三章：向量化

### 对应文档

- [03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md)

### 对应代码

- `source/04_rag/03_embeddings/`

### 目标

- 接入最小 Embedding Provider
- 区分 query/document embedding
- 实现最小相似度对比
- 保持对第二章 `SourceChunk` 输出的直接复用

### 完成标准

- 能生成向量
- 能计算相似度
- 能说明模型选择的基本取舍
- 能把 `EmbeddedChunk` 作为下一章向量数据库输入

## 5. 第四章：向量数据库

### 对应文档

- [04_vector_databases.md](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md)

### 对应代码

- `source/04_rag/04_vector_databases/`

### 目标

- 写入向量存储
- 查询 Top-K 文档
- 支持 metadata 过滤
- 支持最小删除入口

### 完成标准

- 能写入、查询、删除
- 能解释 Vector Store 和 Retriever 的区别

## 6. 第五章：检索策略

### 对应文档

- [05_retrieval_strategies.md](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md)

### 对应代码

- `source/04_rag/05_retrieval_strategies/`

### 目标

- 封装基础 Retriever
- 对比 `top_k / mmr / threshold`
- 记录检索坏案例
- 支持 metadata filter

### 完成标准

- 能稳定返回检索结果
- 能解释检索失败原因
- 能判断是否需要增强检索

## 7. 第六章：RAG 生成

### 对应文档

- [06_rag_generation.md](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md)

### 对应代码

- `source/04_rag/06_rag_generation/`

### 目标

- 构建 RAG Prompt
- 构建最小 Chain
- 返回答案和来源
- 处理无答案问题

### 完成标准

- 能跑通完整问答链路
- 答案包含来源
- 能区分检索问题和生成问题

## 8. 第七章：RAG 优化

### 对应文档

- [07_rag_optimization.md](/Users/linruiqiang/work/ai_application/docs/04_rag/07_rag_optimization.md)

### 对应代码

- 当前暂无代码目录
- 后续如果落地，建议保持独立章节命名，例如 `source/04_rag/07_rag_optimization/`

### 目标

- 建立 Golden Set
- 实现最小评估器
- 对比配置变化
- 记录坏案例

### 完成标准

- 能重复运行评估
- 能说明改动是否变好
- 能用坏案例驱动优化

## 9. 第八章：进阶 RAG 方向

### 对应文档

- [08_advanced_rag.md](/Users/linruiqiang/work/ai_application/docs/04_rag/08_advanced_rag.md)

### 对应代码

- 当前暂无代码目录
- 后续如果落地，建议保持独立章节命名，例如 `source/04_rag/08_advanced_rag/`

### 目标

- 理解 GraphRAG
- 理解 Agentic RAG
- 判断复杂方案的升级条件

### 完成标准

- 能说明哪些场景不该上复杂 RAG
- 能把 Agentic RAG 留到 `05_agent`

## 10. 第九章：综合项目

### 对应文档

- [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md)

### 对应代码

- `source/04_rag/rag_lab/`

### 目标

- 整合前八章能力
- 形成最终完整项目
- 补 README、运行命令、测试和评估说明

### 完成标准

- `rag_lab` 能作为最终参考项目
- 有统一运行和评估入口
- 学习入口仍然保持在九章文档和独立章节代码

## 11. 执行原则

每次推进只做当前章节。

不要提前把后续章节的功能塞进当前目录。

如果后续要补第七章到第九章代码，继续保持独立章节入口，而不是恢复已经删除的旧目录结构。

## 12. 最终验收

- 九章文档全部存在
- 第一章到第六章目录全部存在并可运行
- 第七章到第九章的代码状态在文档里被明确说明
- `rag_lab` 最终项目只在第九章后完成
- `source/04_rag/README.md` 能作为代码总导航
