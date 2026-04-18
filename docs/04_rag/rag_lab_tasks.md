# rag_lab 任务拆解

> 本节目标：把 `04_rag` 的九章学习文档拆成九个可执行代码快照，明确每章对应的 phase、代码职责、完成标准和最终项目收口方式

---

## 1. 总任务顺序

`04_rag` 按九章推进，每一章对应一个 phase：

| Phase | 对应章节 | 代码目录 | 状态 |
|-------|----------|----------|------|
| Phase 1 | RAG 基础概念 | `labs/phase_1_scaffold/` | 已建立骨架 |
| Phase 2 | 文档处理 | `labs/phase_2_document_processing/` | 已实现 |
| Phase 3 | 向量化 | `labs/phase_3_embeddings/` | 已实现 |
| Phase 4 | 向量数据库 | `labs/phase_4_vector_databases/` | 已实现 |
| Phase 5 | 检索策略 | `labs/phase_5_retrieval_strategies/` | 已实现 |
| Phase 6 | RAG 生成 | `labs/phase_6_rag_generation/` | 待实现 |
| Phase 7 | RAG 优化 | `labs/phase_7_rag_optimization/` | 待实现 |
| Phase 8 | 进阶 RAG 方向 | `labs/phase_8_advanced_rag/` | 待实现 |
| Phase 9 | 综合项目 | `labs/phase_9_project_integration/` | 待实现 |

最终完整项目：

```plain
source/04_rag/rag_lab/
```

只在 Phase 9 后整理形成。

## 2. Phase 1：RAG 基础概念

### 对应文档

- [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)

### 对应代码

- `source/04_rag/labs/phase_1_scaffold/`

### 目标

- 固定项目骨架
- 固定基础数据结构
- 固定 RAG 主数据流的形状

### 完成标准

- 能运行占位脚本
- 能通过最小测试
- 能说明各目录职责

## 3. Phase 2：文档处理

### 对应文档

- [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)

### 对应代码

- `source/04_rag/labs/phase_2_document_processing/`

### 目标

- 实现文档加载
- 实现文本切分
- 实现 metadata 注入
- 实现稳定 `document_id / chunk_id`

### 完成标准

- 能加载至少一种文档格式
- 能打印切分结果
- 能验证 chunk id 稳定

## 4. Phase 3：向量化

### 对应文档

- [03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md)

### 对应代码

- `source/04_rag/labs/phase_3_embeddings/`

### 目标

- 接入 Embedding Provider
- 区分 query/document embedding
- 实现最小相似度对比
- 保持对 Phase 2 `SourceChunk` 输出的直接复用

### 完成标准

- 能生成向量
- 能计算相似度
- 能说明模型选择的基本取舍
- 能把 `EmbeddedChunk` 作为下一章向量数据库输入

## 5. Phase 4：向量数据库

### 对应文档

- [04_vector_databases.md](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md)

### 对应代码

- `source/04_rag/labs/phase_4_vector_databases/`

### 目标

- 写入向量存储
- 查询 Top-K 文档
- 支持 metadata 过滤
- 支持最小删除入口

### 完成标准

- 能写入、查询、删除
- 能解释 Vector Store 和 Retriever 的区别

## 6. Phase 5：检索策略

### 对应文档

- [05_retrieval_strategies.md](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md)

### 对应代码

- `source/04_rag/labs/phase_5_retrieval_strategies/`

### 目标

- 封装基础 Retriever
- 对比 `top_k / mmr / threshold`
- 记录检索坏案例
- 支持 metadata filter

### 完成标准

- 能稳定返回检索结果
- 能解释检索失败原因
- 能判断是否需要增强检索

## 7. Phase 6：RAG 生成

### 对应文档

- [06_rag_generation.md](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md)

### 对应代码

- `source/04_rag/labs/phase_6_rag_generation/`

### 目标

- 构建 RAG Prompt
- 构建最小 Chain
- 返回答案和来源
- 处理无答案问题

### 完成标准

- 能跑通完整问答链路
- 答案包含来源
- 能区分检索问题和生成问题

## 8. Phase 7：RAG 优化

### 对应文档

- [07_rag_optimization.md](/Users/linruiqiang/work/ai_application/docs/04_rag/07_rag_optimization.md)

### 对应代码

- `source/04_rag/labs/phase_7_rag_optimization/`

### 目标

- 建立 Golden Set
- 实现最小评估器
- 对比配置变化
- 记录坏案例

### 完成标准

- 能重复运行评估
- 能说明改动是否变好
- 能用坏案例驱动优化

## 9. Phase 8：进阶 RAG 方向

### 对应文档

- [08_advanced_rag.md](/Users/linruiqiang/work/ai_application/docs/04_rag/08_advanced_rag.md)

### 对应代码

- `source/04_rag/labs/phase_8_advanced_rag/`

### 目标

- 理解 GraphRAG
- 理解 Agentic RAG
- 判断复杂方案的升级条件

### 完成标准

- 能说明哪些场景不该上复杂 RAG
- 能把 Agentic RAG 留到 `05_agent`

## 10. Phase 9：综合项目

### 对应文档

- [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md)

### 对应代码

- `source/04_rag/labs/phase_9_project_integration/`
- `source/04_rag/rag_lab/`

### 目标

- 整合前八章能力
- 形成最终完整项目
- 补 README、运行命令、测试和评估说明

### 完成标准

- `phase_9_project_integration` 能展示整合过程
- `rag_lab` 能作为最终参考项目
- 学习入口仍然保持在九章文档和 labs 快照

## 11. 执行原则

每次推进只做当前 Phase。

不要提前把后续 Phase 的功能塞进当前目录。

如果当前 Phase 需要复用上一 Phase，可以复制上一阶段代码后增量修改，保留学习快照的完整性。

## 12. 最终验收

- 九章文档全部存在
- 九个 phase 目录全部存在
- 每个 phase README 都说明对应文档和当前边界
- `rag_lab` 最终项目只在 Phase 9 后完成
- `source/04_rag/README.md` 能作为代码总导航
