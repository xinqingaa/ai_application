# 03. 向量化

## 1. 本章目标

- 能解释 Embedding 为什么能用于语义检索
- 能区分 query embedding 和 document embedding
- 能接入至少一个 Embedding Provider
- 能用最小示例比较文本相似度

## 2. 本章在 04_rag 中的位置

本章把第二章得到的文本块转换成向量，是连接文档处理和向量数据库的桥梁。

## 3. 学习前提

- 已完成文档加载、切分和 metadata 处理
- 已理解文本块是后续检索的基本单位

## 4. 本章边界

本章不比较所有 Embedding 模型，也不展开模型训练或本地推理优化。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“三、向量化”
2. 再进入 `phase_3_embeddings`
3. 先跑 mock 或本地占位 Embedding
4. 再接真实 Provider
5. 最后对比相似文本和不相似文本的距离

## 6. 核心知识点

- 文本向量表示
- 余弦相似度
- `embed_query`
- `embed_documents`
- 维度、成本和效果的取舍
- 中文场景下模型选择的注意点

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| Embedding 接口 | `source/04_rag/labs/phase_3_embeddings/app/embeddings/` | 主示例 |
| 文档向量化 | `source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py` | 第一运行入口 |
| 相似度计算 | `source/04_rag/labs/phase_3_embeddings/scripts/compare_similarity.py` | 对照实验 |
| 配置切换 | `source/04_rag/labs/phase_3_embeddings/app/config.py` | 工程骨架 |

## 8. 实践任务

1. 对三段文本生成 embedding
2. 计算两两相似度
3. 比较 query 和 document 的调用差异
4. 记录模型、维度和调用成本

## 9. 完成标准

- 能解释为什么相似语义的文本向量距离更近
- 能封装一个最小 Embedding Provider
- 能为向量数据库阶段提供可写入的向量数据
