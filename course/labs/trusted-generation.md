# 结构化生成与 Citation Candidate 实验

配套机制：[可信生成、Sources、Citation Candidate 与证据不足](../mechanisms/trusted-generation.md)。本实验从真实 PostgreSQL Retriever 和 Context 开始，调用真实结构化模型，检查模型声明的 source ID 是否属于本轮 Citation Candidate。

本实验只完成候选集合 membership 检查。合法 ID 仍可能引用错误内容；Citation 支持性、证据充分性、Refusal 和补充问题由后续课程完成。

## 1. 前置与真实依赖

需要：

- 已执行 PostgreSQL FTS 和 pgvector migration。
- 有效 `DATABASE_URL`。
- 真实 Embedding 配置。
- 真实 Chat / Structured Output 配置和 Key。
- Retriever 与 Context 实验已经跑通。

默认运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py
```

主路径不会在数据库、Embedding 或模型失败时使用静态结果继续生成。

## 2. 三种固定 Context

默认比较：

| variant | 输入事实 | 观察重点 |
| --- | --- | --- |
| `rag_evidence` | 真实 Retriever 产生的当前证据 | 模型是否声明允许的 Chunk source ID |
| `normal_noise` | 与当前需求主题相邻但不支持结论的材料 | 候选 membership 为什么仍不能证明支持性 |
| `empty_evidence` | 没有 Evidence Source | 模型怎样处理无可引用证据 |

运行前预测每个 variant：

- Context 中有哪些 Citation Candidate。
- 模型可能生成哪些风险。
- 哪些 source ID 声明会被接受或拒绝。
- 哪些结论即使状态为 succeeded，也不能宣称已经有内容支持。

## 3. 只运行一个变量

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py \
  --variants rag_evidence \
  --verbose
```

可用参数：

| 参数 | 默认 | 作用 |
| --- | --- | --- |
| `--variants` | 三种全跑 | 逗号分隔选择 Context 变体 |
| `--structured-mode` | `json_schema` | 选择真实结构化模式 |
| `--config-ref` | `chat.structured_chat` | 选择生成模型配置 |
| `--candidate-k` | `5` | 上游每路候选数量 |
| `--final-top-k` | `5` | 最终 Retriever 候选数量 |
| `--verbose` | 关闭 | 展开 Context、模型输出和逐项检查 |

比较 Context 变体时，不同时更换模型、structured mode 和候选数量。

## 4. 怎样读一次完整结果

按下面顺序：

1. 确认 case、variant、模型和 structured mode。
2. 查看本轮 Context 和允许的 Citation Source IDs。
3. 查看模型原始结构化风险和 claimed source IDs。
4. 查看每个声明是否属于 allowlist。
5. 查看最终 generation status 和错误。
6. 最后回查 Retriever 与 Context 报告，而不是先猜模型问题。

输出中的三种事实不能混淆：

- `Citation Candidate`：应用允许模型声明的来源。
- `Claimed Citation`：模型实际声明的来源。
- membership validation：声明是否属于候选集合。

内容支持性尚未在本实验验证。

## 5. Structured Mode 对照

若 Provider 支持，默认使用 `json_schema`。可建立独立对照：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py \
  --structured-mode json_object \
  --variants rag_evidence
```

这次主要变量是模型侧结构化模式，不能与 Context 变体实验混成同一结论。Provider 不支持 `json_schema` 时保留真实能力错误；`json_object` 成功不能改写为 `json_schema` 已通过。

## 6. JSON Lines、退出状态与失败

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py \
  --log-format json
```

结构化解析失败、未知 source ID 或非成功 generation status 应反映在结果和退出状态中。

| 表现 | 可能层次 | 验证方式 |
| --- | --- | --- |
| 缺少数据库或 Embedding | Retrieval 准备 | 先跑 Retriever 实验，不生成假 Context |
| Context 没有预期来源 | Retriever 或 Context | 查看两层报告和 locator |
| Provider 不支持模式 | 真实模型能力 | 保留 LLMError，另建模式对照 |
| JSON / Schema 失败 | Structured Output | 查看原始响应与 error stage |
| claimed ID 不在 allowlist | 应用 Citation Candidate 校验 | 检查最终状态，不自动猜最近来源 |
| 合法 ID 引用错误内容 | 支持性尚未验证 | 记录为后续 Citation 支持性问题 |
| 空 Evidence 仍有强结论 | 证据充分性尚未实现 | 不把 succeeded 误写为可信结论 |

## 7. 读码顺序

1. `inspect_trusted_generation.py`：真实 RAG Context 和三种变体怎样进入生成。
2. `rag_core` 的可信生成公共入口：允许 ID、结构化调用和最终报告。
3. `llm_core` Context：模型实际看到的 Evidence block。
4. Review Schema 与解析：结果形状怎样守住。
5. Citation Candidate membership 检查：未知 ID 怎样失败。
6. `source/packages/rag_core/tests/test_trusted_generation.py`：确定性生成边界。

## 8. 修改与验证

选择一个受控修改：

- 增加一个未知 source ID 的确定性测试。
- 修改一个正常噪声 probe，但保持它不支持当前售后结论。
- 调整上游 `final-top-k`，记录 allowlist 怎样变化。

先预测 Context、allowlist、模型声明和最终状态哪些可能变化，哪些 Schema 和未知 ID 拒绝规则不应变化。

运行：

```bash
uv run pytest source/packages/rag_core/tests/test_trusted_generation.py \
  source/packages/rag_core/tests/test_rag_context.py \
  source/packages/llm_core/tests/test_client_structured.py -q
```

测试证明候选身份、结构化结果和错误契约，不证明真实模型一定引用正确内容。真实变体实验和后续支持性课程共同完成证据链。
