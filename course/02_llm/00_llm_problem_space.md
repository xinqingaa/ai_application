# 00. LLM 应用问题空间

> 建立需求评审助手的 LLM 应用工程视角，明确 `llm_core` 模块边界与设计输入，而不是停留在「调一次模型接口」。

---

## 真实问题

需求评审助手要处理 PRD、接口文档、业务规则和历史评审记录。如果只把 LLM 当作「发一条 HTTP 请求拿文本」，很快会在真实场景里失控：

- **输出不稳定**：同一需求两次评审，风险列表差异大，无法回归对比。
- **上下文超限**：一份 PRD + 检索片段 + 历史对话很容易撑爆 context window。
- **不可解析**：模型返回自然语言，前端、数据库、Workflow 无法消费。
- **成本不可控**：多轮追问、多 Agent 分析会放大 token 消耗。
- **供应商切换困难**：开发用便宜模型、演示用高质量模型、eval 用批处理模型，接口和能力标签不一致。
- **失败不可观测**：超时、限流、JSON 解析失败没有统一记录，无法定位是 Prompt、模型还是 schema 的问题。
- **流式体验缺失**：用户只能等最终答案，不知道系统是在检索、分析还是已失败。

这些不是「模型不够聪明」能单独解决的，而是 **LLM 应用工程** 问题：应用侧必须负责上下文、约束、校验、回归和观测。

### 「调一次 API」与「应用工程」的差距

| 调一次 API | LLM 应用工程 |
| --- | --- |
| 固定 prompt + 固定 model | 多任务 prompt 集 + 多模型角色 + 能力标签 |
| 打印 `content` | 统一 `LLMResponse`（content / usage / latency / provider） |
| 失败就重试 | 错误分类、降级、兜底模型（见专题 06） |
| 自然语言输出 | Schema 契约 + 本地校验（见专题 03） |
| 无记录 | Harness 样例集 + 版本对比（见专题 07） |

---

## 基础原理

### LLM 是概率生成系统

大模型不是在数据库里「查答案」，而是根据上下文预测下一个 token。因此：

- 同一输入在不同模型、参数、上下文下结果可能不同。
- Prompt 改一个词、多塞一段噪声上下文，输出可能明显变化。
- **应用侧**负责把概率输出变成可控、可验证、可交付的结果。

应用开发者需要理解的深度：**知道为什么会不稳定即可**，不必深入 Transformer 训练细节（按需查阅 [99_foundation](../99_foundation/outline.md)，非主链路）。

### 四要素决定结果稳定性

```text
Prompt（任务协议）
+ 模型与参数（model / temperature / max_tokens）
+ 上下文（需求材料、检索证据、历史摘要）
+ 输出 Schema（结构化契约）
→ 应用可校验、可观测的最终结果
```

四要素缺任何一环，都会出现「看起来能答、实际上不可信」的情况。

### 应用侧职责

| 职责 | 说明 |
| --- | --- |
| 上下文管理 | 什么进 prompt、什么被裁剪、引用如何编号 |
| 约束与校验 | Schema 解析、引用是否存在、拒答规则 |
| 回归与对比 | 固定样例集、Prompt/模型版本对比 |
| 观测 | usage、latency、失败类型、调用日志 |

Prompt 不能替代：知识库治理、权限控制、RAG 检索、Tool Runtime、完整 eval 平台——这些由下游课程与项目模块承担。

---

## 最小实现

目标：用最小代码验证「一次调用发生了什么」，并为后续 harness 建立对比基础。

### 前置

- 根目录 `.venv` 与 `requirements.txt` 已就绪。
- `.env` 配置 `OPENAI_API_KEY`（或任意 OpenAI 兼容平台的 key / base_url / model）。

### 步骤

1. 发起一次 chat 请求（system + user 两条消息即可）。
2. 打印：`model`、`usage`（prompt_tokens / completion_tokens）、耗时（ms）。
3. 用**同一 user 消息**，分别尝试：
   - 换 model（如 dev vs structured 模型）；
   - 换 `temperature`（0 vs 0.7）。
4. 观察：输出长度、风格、是否遵守简单约束（如「只输出 JSON」）的差异。

### 示例（伪代码）

```python
import os, time
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
messages = [
    {"role": "system", "content": "你是需求评审助手，只基于给定材料回答。"},
    {"role": "user", "content": "请列出该 PRD 片段中的 3 个潜在风险。"},
]

start = time.perf_counter()
resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0)
latency_ms = (time.perf_counter() - start) * 1000

print(resp.model, resp.usage, latency_ms, resp.choices[0].message.content[:200])
```

### 观察重点

- `usage` 是否随上下文长度变化。
- 换 model 后 latency 和 cost 如何变化。
- 低 temperature 是否更稳定（不一定更「正确」）。

代码后续收敛到 `source/02_llm/demos/provider_switching/`；本篇不要求完整 package。

---

## 主流框架实现

| 方式 | 在本项目中的位置 |
| --- | --- |
| OpenAI SDK / OpenAI 兼容 HTTP | `llm_core` 默认底层（专题 01） |
| LangChain ChatModel | `03_rag` 组合 RAG 链时复用统一 `LLMClient` 思路，不在本课系统学习 |
| LangGraph | `04_agent` Workflow 运行时 |

原则：**先统一 `llm_core` 接口，再让框架适配项目**，而不是让项目绑死在某一框架 API 上。

---

## 失败分析与能力边界

### 常见失败

- 模型编造风险或引用不存在的条款。
- 输出遗漏约束（如要求 JSON 却返回 Markdown）。
- 上下文过长导致截断或中间证据被忽略。
- 限流、超时、内容安全拦截。

### LLM 层单独无法可靠解决的事

1. **企业知识从哪来、是否最新** → RAG / 知识库（`03_rag`）
2. **答案是否有依据、引用是否正确** → 检索 + citation checker（`03_rag` V1）
3. **多步骤工具调用与权限** → Agent Tool Runtime（`04_agent`）
4. **质量是否变好、哪次改动回退** → eval / harness / trace（`05_eval`）
5. **流式状态、人工确认 UI** → AI Native 工作台（`06_ai_native`）

单次 chat 调用也**不能**替代：长期记忆治理、Multi-Agent 协作、完整 Workflow 状态机。

### 不在本篇展开

- RAG 主链路与 LangChain 组件
- FastAPI 服务层与 SSE（`06_ai_native`）
- 评审维度矩阵全文（见 [07_projects/03](../07_projects/outline.md)）

---

## 评估观测

从第一次调用开始就应记录，为专题 07 harness 铺路：

| 字段 | 用途 |
| --- | --- |
| `model` / `provider` | 对比不同供应商 |
| `temperature` 等参数 | 复现与回归 |
| `prompt_version`（后续） | Prompt A/B |
| `input_hash` | 样例去重 |
| `usage` | 成本基线 |
| `latency_ms` | 体验与瓶颈 |
| `raw_output` / 失败类型 | 调试 |

最小调用样例集：先收集 5–10 条需求评审相关问题（摘要、风险、追问各几条），不必等 RAG 完成。

---

## 小项目实战

为**需求评审助手**定义 LLM 层职责（不写实现，只写边界）：

| 任务 | LLM 做什么 | 不做什么 |
| --- | --- | --- |
| 需求摘要 | 压缩材料、提取模块与目标 | 不编造未出现的功能 |
| 风险识别 | 按维度输出结构化风险项 | 不替代人工最终结论 |
| 结构化评审项 | 输出 schema 字段 | 不跳过 schema 校验 |
| 引用解释 | 说明依据来自哪条 source | 不虚构 source_id |
| 拒答 / 人工确认 | 证据不足时明确拒答或建议人工 | 无依据不强答 |

与项目版本关系：

- **V0**：固定 RAG + 生成（LLM 提供调用与 prompt 底座）
- **V1**：结构化输出 + 拒答（依赖专题 02、03）

---

## 项目收敛

### 能力边界表

| 能力 | `02_llm` 负责 | 下游负责 |
| --- | --- | --- |
| 模型调用 / Provider 抽象 | 01 | — |
| Prompt 任务协议 | 02 | — |
| Structured Output / Schema | 03 | — |
| 流式 / 对话 / 上下文预算 | 04–05 | — |
| 可靠性 / 降级 | 06 | — |
| Harness 样例外壳 | 07 | 05 系统化 eval |
| 成本 / 缓存 | 08 | — |
| Function Calling API 边界 | 09 | 04 Tool Runtime |
| 检索 / 引用 / 拒答逻辑 | 概念铺垫 | `03_rag` |
| Tool Runtime / Agent Loop | 认知 | `04_agent` |
| Golden set / Trace 平台 | 铺垫 | `05_eval` |
| SSE / 状态机 UI | 事件格式铺垫 | `06_ai_native` |

### `llm_core` 目标目录

```text
source/02_llm/packages/llm_core/
├── client.py           # 统一 LLMClient（01）
├── providers/          # 多供应商适配（01）
├── prompts/            # 模板 registry（02）
├── schemas/            # Pydantic 契约（03）
├── context/            # 上下文构造（05）
├── streaming/          # 事件格式（04）
├── reliability/        # 错误与降级（06）
└── harness/            # 调用记录与回归（07）
```

### 设计输入清单（供 01–10 实现）

1. 统一 `LLMResponse` 与错误类型枚举。
2. 模型配置文件：Chat / Embedding / Rerank 角色分离。
3. 命名 Prompt 集：requirement_summary、risk_review 等。
4. 核心 Schema：ReviewRisk、ReviewReport、Citation、RefusalResponse。
5. 最小调用样例集与日志字段约定。

---

## 完成标准

- 能解释：为什么 AI 应用不能只做「一次 API 调用」。
- 能画出：用户提问 → `llm_core` →（RAG / Agent / 前端）的数据流。
- 能列举：至少 5 类 LLM 层单独无法可靠解决的问题及对应下游模块。
- 能运行：一次最小 chat 请求并解读 `usage` 与 latency。
- 能说明：`llm_core` 各子模块职责及与 V0–V1 的关系。

---

## 相关专题

- 下一篇：[01_model_api_and_provider_abstraction.md](01_model_api_and_provider_abstraction.md)
- 课程大纲：[outline.md](outline.md)
- RAG 定位：[03_rag/outline.md](../03_rag/outline.md)
- 项目评审场景：[07_projects/03](../07_projects/outline.md)
- LLM 原理补充（非主链路，按需）：[99_foundation/outline.md](../99_foundation/outline.md)
