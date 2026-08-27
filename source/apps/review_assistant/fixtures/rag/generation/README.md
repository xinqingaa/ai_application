# 第一阶段 trusted-generation fixtures

`trusted_generation_probes.json` 为可信生成提供一条正常但与售后 Requirement 无关的当前材料，用于真实模型生成对照。它不包含模型输出、期望答案或 mock 结果。

`rag_evidence` 仍来自真实 Loader、Chunker、PostgreSQL FTS、pgvector 和固定 Retriever；`empty_evidence` 由 Context Builder 显式构造。噪声材料不会写入售后知识范围，也不改变 Retriever Contract 的 Metadata Filter 契约。

这些探针用于理解生成边界，不是冻结的第一阶段 acceptance 或评估集。
