# 第一阶段生成与 Citation 校验 fixtures

`trusted_generation_probes.json` 为来源声明集合检查实验提供一条正常但与售后 Requirement 无关的当前材料，用于真实模型生成对照。它不包含模型输出、期望答案或 mock 结果。

`rag_evidence` 仍使用 `surface_match=申请售后`，来自真实 Loader、Chunker、PostgreSQL FTS、pgvector、固定 Retriever 和 `full_context` Policy；生成的 Requirement 固定为同主题的 `after_sale_entry_v2` PRD。`empty_evidence` 由 Context Builder 显式构造。噪声材料不会写入售后知识范围，也不改变 Retriever Contract 的 Metadata Filter 契约。

这些探针用于理解生成边界，不是冻结的第一阶段 acceptance 或评估集。

`citation_support_probes.json` 为第 17 节固定一条需要外部资料支持的说法和一段逐字引文，只改变引文周围的来源范围、版本与适用条件。前三组进入真实模型支持判断，`missing_quote` 由确定性定位拦截。文件不保存模型 verdict；当前 Provider 仍须真实完成判断。
