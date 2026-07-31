# rag_retrieval_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 10 起。步骤 10 先读 [Embedding 表示与向量相似度](../../../course/mechanisms/embedding-and-similarity.md)。本 lab 后续还会承接 lexical、dense、RRF 与 retrieval 诊断实验。

本实验负责运行方式、输出解读和代码阅读路径。机制原理在课程正文；真实 Embedding HTTP 调用位于 [`llm_core.LLMClient.embed`](../../packages/llm_core/client/service.py)，RAG 侧表示与成对相似度位于 [`rag_core.embedding`](../../packages/rag_core/embedding/)。

## 步骤 10：成对相似度

在仓库根目录运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py
```

主路径必须显式配置真实 Embedding 凭证 `OPENAI_EMBEDDING_API_KEY`，并按需要配置 `OPENAI_EMBEDDING_BASE_URL` / `OPENAI_EMBEDDING_MODEL`。Embedding 不自动复用 chat 的 key 或 base URL。

注意：`OPENAI_BASE_URL` 只服务 chat。若 chat 使用 DeepSeek 等不提供 `/embeddings` 的平台，必须为 Embedding 单独选择支持该端点的服务。缺少专用 key 时返回 `AUTH`；显式配置了不支持 `/embeddings` 的 endpoint 或不存在的模型时可能返回 `404` / `PROVIDER_ERROR`。实验不会静默改用 mock。

默认输出展示：

- 使用的 embedding Provider、模型、维度、预处理版本、latency 和 usage
- 探针文本及其分组
- 若干 focus pairs 的成对分数与预期说明

这些分数只描述表示空间距离，不代表已经完成知识库检索，也不代表证据充分或评审正确。

查看全部成对分数：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --verbose
```

切换度量：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --metric euclidean
```

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --log-format json
```

探针材料位于 [`review_assistant/fixtures/v0/retrieval/embedding_probes.json`](../../../review_assistant/fixtures/v0/retrieval/embedding_probes.json)，继续使用“售后入口与订单状态”业务域。

## Demo 调用路径

```text
main
→ 读取 embedding_probes.json
→ LLMClient.embed（真实服务）
→ EmbeddingRecord[]
→ pairwise_similarity
→ focus pairs / compact / verbose / json 呈现
```

本步只观察探针句对的表示距离。匹配一整库候选、持久化向量、多路融合和检索诊断，由课表后续步骤再进入。

## 从 Demo 进入核心代码

1. [`inspect_embedding.py`](inspect_embedding.py)：看探针如何进入公共 API。
2. [`llm_core/client/service.py`](../../packages/llm_core/client/service.py)：看 `embed` 的 role 守卫与空文本拒绝。
3. [`llm_core/providers/openai_compat.py`](../../packages/llm_core/providers/openai_compat.py)：看真实 `embeddings.create` 与错误映射。
4. [`rag_core/embedding/models.py`](../../packages/rag_core/embedding/models.py)：看 `EmbeddingRecord`、度量方向和 Embedding 空间一致性校验。
5. [`tests/test_client_embed.py`](../../packages/llm_core/tests/test_client_embed.py) 与 [`tests/test_embedding.py`](../../packages/rag_core/tests/test_embedding.py)：看离线契约。

## 运行测试

```bash
uv run pytest source/packages/llm_core/tests/test_client_embed.py source/packages/rag_core/tests/test_embedding.py -q
```

## 当前实验不观察什么

- 不对知识库候选做匹配与排名
- 不持久化向量，也不建立全文索引
- 不装配模型上下文，也不用最终评审回答判断 Embedding 质量
- 不允许主路径 mock embedding 结果冒充真实模型效果
