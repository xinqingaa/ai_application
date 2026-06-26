# 00. LLM 应用问题空间

> 从「LLM 是什么」出发，理解需求评审助手为什么需要 LLM 应用工程，以及 `llm_core` 在整个项目里负责什么、不负责什么。

---

## 真实问题

本篇是 `02_llm` 的入口。如果你已经用过 ChatGPT 网页版或调通过 API，你会熟悉「问一句、答一句」；如果你主要做前端或客户端，可能还不清楚：**把 LLM 接进一个真实产品，和「打开聊天网页」差在哪里**。下面分三层说明「真实问题」——先说你作为学习者为什么要读这一篇，再说产品为什么需要 LLM 层，最后说工程上会踩哪些坑。

### 学习者真实问题：我遇到的困惑

- **LLM 到底是什么？** 是一个网站、一个 API、还是一个可以部署的模型文件？和我写的 Python / Flutter 代码是什么关系？
- **为什么需求评审助手要用 LLM？** 不能像传统软件一样写死规则「如果 PRD 里没有验收标准就报错」吗？
- **ChatGPT 已经能评审需求了，为什么还要学一门「LLM 课」？** 网页聊天和「需求评审助手」是一回事吗？
- **后面会学的 RAG、Agent 和 LLM 是什么关系？** 会不会重复学很多东西？

读完全篇，你应能回答：LLM 在本项目里是**生成与推理引擎**；RAG / Agent 是在 LLM 之上叠加**知识**与**行动**；`02_llm` 只负责把引擎用得**稳定、可配置、可观测**，不负责知识库和工具执行。

### 产品真实问题：需求评审助手里发生什么

下面是一段**连续业务场景**（虚构但贴近真实研发流程）：

产品同学小周提交一份 PRD 片段：「订单详情页新增『申请售后』按钮，点击后进入售后申请流程，需对接售后接口 v2。」评审负责人希望助手帮忙：**列出潜在风险、说明依据、输出能进评审会议的结构化结论**。

若团队第一次做 AI 功能，最容易的做法是：把 PRD 全文复制到 ChatGPT，粘贴一句「请评审这份需求」。短期内「看起来能用」，但很快会遇到：

1. **小周第二次提交相似需求，风险列表和上次完全不一样**——会议里无法对比「这次比上次多发现了什么」。
2. **助手说「可能与支付模块冲突」**，问依据是哪一段，回答模糊或引用不存在——**无法用于正式评审**。
3. **PRD 很长，还希望带上接口文档、历史评审**，一次性粘贴超过模型上下文或中间段落被模型忽略。
4. **前端要把「风险等级、分类、建议」展示成卡片**，模型返回一大段 Markdown，**程序无法稳定解析**。
5. **开发阶段用便宜模型、演示用强模型**，代码里写死一个模型名，**换供应商要改很多文件**。
6. **用户只看到转圈 30 秒**，不知道是在「读文档」「查知识库」还是「已经失败」——体验像黑盒。

这些痛点**不全是「模型不够聪明」**。很多是：**没有把 LLM 当作应用系统里的一层来设计**——缺少统一的调用方式、任务描述（Prompt）、输出格式（Schema）、日志与成本记录。这就是「LLM 应用工程」要解决的问题；`02_llm` 整门课都在建这一层，沉淀为 `llm_core` 包。

### 工程真实问题：只调一次 API 为什么不够

当需求评审助手从 Demo 走向可迭代产品时，工程上必须提前考虑：

| 工程问题 | 若只「调一次 API」会怎样 | `02_llm` 方向 |
| --- | --- | --- |
| 输出不稳定 | 无法回归对比，改 Prompt 不知好坏 | Harness 样例 + 版本记录（专题 07） |
| 上下文超限 | 长 PRD 被截断或漏看中间段 | Context 预算（专题 05）；RAG 按需检索（`03_rag`） |
| 不可解析 | 前端 / DB / Workflow 接不住 | Structured Outputs（专题 03） |
| 成本不可控 | 多轮、多 Agent 后账单失控 | usage 记录 + 成本基线（专题 08） |
| 供应商绑定 | 换模型改遍业务代码 | Provider 抽象（专题 01） |
| 失败不可观测 | 不知超时是网络还是模型 | 统一错误类型 + 日志（专题 06） |
| 体验黑盒 | 用户只能干等 | 流式事件（专题 04）；检索态由 RAG + 前端展示 |

注意：**检索是否命中、引用是否正确、工具是否越权**——LLM 层单独解决不了，需要 RAG（`03_rag`）、Agent（`04_agent`）、Eval（`05_eval`）。本篇只建立边界，避免以为「学好 LLM 课就够了」。

### 和「打开 ChatGPT 网页」的对比

| | ChatGPT 网页 | 需求评审助手（AI 应用） |
| --- | --- | --- |
| 谁组织上下文 | 产品方 + 用户手动粘贴 | 应用：PRD、检索片段、历史摘要 |
| 谁规定输出格式 | 用户每次口头要求 | 应用：Schema + Prompt 模板 |
| 谁保证有依据 | 无强制 | 应用 + RAG：引用、拒答（V1 起） |
| 谁记录每次调用 | 平台内部 | 你的服务：usage、latency、版本 |
| 谁对结果负责 | 用户自己判断 | 团队：eval、bad case、人工确认 |

---

## 基础原理

### LLM 是什么（应用开发者版）

**LLM（Large Language Model，大语言模型）** 是一个通过海量文本训练得到的**文本生成模型**。你给它一段输入（通常叫 **Prompt** 或 **上下文**），它**逐 token（词元）预测下一个最可能出现的 token**，直到结束。

关键直觉（不需要会推公式）：

- 它**不是在数据库里查标准答案**，而是根据读过的模式「续写」看起来合理的文本。
- 所以同一问题**可能答对，也可能编造**——尤其当材料里没有依据时。
- **温度（temperature）** 等参数控制随机性：越低越稳定，越高越发散。

在本项目里，LLM 的**输入**通常是：系统指令 + 用户问题 +（可选）PRD 片段 / 检索到的证据。  
**输出**通常是：自然语言，或按 Schema 生成的 JSON（专题 03）。

**和已有概念的区别：**

| 概念 | 做什么 | 和 LLM 的分工 |
| --- | --- | --- |
| 传统程序 / 规则引擎 | 按 if-else 执行确定逻辑 | 适合硬规则；不适合开放式「读 PRD 找风险」 |
| 搜索引擎 | 关键词匹配文档 | 返回链接，不帮你写评审结论 |
| 数据库 | 存取结构化数据 | 存评审结果；不生成分析 |
| LLM | 读文本、生成文本 / 结构化内容 | 需求理解、风险描述、报告草稿 |
| RAG（后续课） | 先检索再生成 | 解决「模型不知道公司内部文档」 |
| Agent（后续课） | 多步决策 + 调工具 | 解决「需要查系统、走流程」 |

需求评审助手**需要 LLM**，是因为评审内容大量是**非结构化文本**（PRD、规则、会议纪要），要产出**自然语言 + 结构化字段**的混合结果；纯规则难以覆盖「这份 PRD 在弱网场景有没有风险」这类开放问题。

### LLM 在需求评审助手中的位置

```text
用户 / 前端
    ↓ 提交 PRD、提问
API 服务（FastAPI，06 / 07）
    ↓
llm_core（02_llm）          ← 本篇定义的「模型层」
    · 选哪个模型、怎么调
    · 用什么 Prompt、什么 Schema
    · 记录 usage / 错误
    ↓
（可选）rag_core 提供 evidence   ← 03_rag
（可选）agent_core 多步执行       ← 04_agent
    ↓
评审结论、报告、引用展示          ← 06_ai_native / 07_projects
```

**`02_llm` 不负责：** 文档上传与向量索引、检索策略、工具执行、人工审批流程、完整质量平台。  
**`02_llm` 负责：** 无论上层是固定 RAG 还是多 Agent，都通过**同一套** `LLMClient`、Prompt 集、Schema 去调用模型。

### 四要素：为什么「看起来能答」却不可信

一次 LLM 调用是否可用于评审，取决于四要素是否一起设计：

```text
Prompt（任务协议：你是谁、要做什么、不能做什么）
+ 模型与参数（用哪个 model、temperature、max_tokens）
+ 上下文（PRD 片段、检索证据、历史摘要——放进 Prompt 的材料）
+ 输出 Schema（ReviewRisk、ReviewReport 等字段契约）
→ 应用校验后的结果（才能进 DB / 前端 / eval）
```

**反例：** 只写好 Prompt「请输出 JSON 风险列表」，没有 Schema 校验——模型可能 JSON 语法对，但字段缺失或 `source_id` 造假。  
**反例：** 上下文塞进 10 万字 PRD，没有裁剪——模型可能忽略中间的接口约束段落。

### 应用侧必须承担的职责

| 职责 | 通俗解释 | 在本项目的落点 |
| --- | --- | --- |
| 上下文管理 | 什么材料进 Prompt、多长、如何编号引用 | 05 context；RAG context builder |
| 约束与校验 | 输出是否符合 schema、引用是否存在于材料中 | 03 schema；RAG citation checker |
| 回归与对比 | 改 Prompt / 换模型后，同一批问题结果是否变好 | 07 harness；05_eval |
| 观测 | 花了多少 token、多久、失败原因 | 01 LLMResponse；06 reliability |

**常见误区：**

- **误区 1：**「Prompt 写得好就不会胡说」——没有外部知识时，模型仍会编造；需要 RAG 或拒答。
- **误区 2：**「用最强模型就不用工程化」——强模型也会超限、也会 JSON 格式错误、也更贵。
- **误区 3：**「LLM 课学完就能做完整助手」——助手 = LLM + 知识 + 流程 + 前端 + eval。
- **误区 4：**「网页聊天体验 = 产品体验」——产品要状态、引用、权限、日志，网页不负责这些。

更底层的「下一个 token 预测 / Transformer」属于按需查阅：[99_foundation/outline.md](../99_foundation/outline.md)（非主链路，默认不读）。

---

## 最小实现

目标：**亲手看清一次调用里有什么**，建立「模型返回的不是魔法，是一串可记录的响应」的直觉。  
本篇允许用**设计草图**；M1 代码完成后回链到 `source/demos/02_*`（见 [outline 代码里程碑](outline.md)）。

### 前置

- 根目录 `.venv` 已创建，`pip install -r requirements.txt` 含 OpenAI SDK。
- 根目录 `.env` 配置（示例）：
  ```bash
  OPENAI_API_KEY=sk-...
  # 若用国内 OpenAI 兼容平台，还可设 OPENAI_BASE_URL=https://...
  ```

### 一次 Chat 调用里有什么

HTTP 层面：你的 Python 程序 `POST` 到 `/v1/chat/completions`（或兼容地址），Body 核心是 **messages** 数组：

```json
[
  {"role": "system", "content": "你是需求评审助手，只基于用户提供的材料回答。"},
  {"role": "user", "content": "【PRD 片段】... 请列出 3 条潜在风险。"}
]
```

响应里你至少要会找：

- `choices[0].message.content` —— 模型生成的文本
- `usage.prompt_tokens` / `usage.completion_tokens` —— 计费用
- `model` —— 实际使用的模型 id

### 设计草图：第一次调用 `[CODE-GATE: M1]`

> 以下为设计草图；M1 实现后见 `source/demos/02_provider_switching/`。

```python
import os
import time
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    # base_url=os.environ.get("OPENAI_BASE_URL"),  # 兼容平台时打开
)

messages = [
    {"role": "system", "content": "你是需求评审助手。只根据用户材料分析，不要编造未出现的功能。"},
    {"role": "user", "content": (
        "【PRD 片段】订单详情页增加「申请售后」按钮，点击跳转售后申请页，对接售后接口 v2。\n"
        "请列出 3 条研发侧潜在风险（交互、状态、接口各至少考虑一点）。"
    )},
]

t0 = time.perf_counter()
resp = client.chat.completions.create(
    model="gpt-4o-mini",  # 开发阶段可用便宜模型
    messages=messages,
    temperature=0,        # 先固定为 0，便于对比
)
latency_ms = (time.perf_counter() - t0) * 1000

print("model:", resp.model)
print("usage:", resp.usage)
print("latency_ms:", round(latency_ms, 1))
print("content preview:", resp.choices[0].message.content[:300])
```

### 建议做的两个对比实验

用**同一条 user 消息**：

1. **`temperature=0` vs `0.7`** —— 观察风险表述是否更「飘」、是否出现材料里没有的模块名。
2. **换 model**（如 `gpt-4o-mini` vs 更强模型）—— 观察 `usage`、`latency_ms`、风险是否更贴材料。

记录到一个简单表格（笔记本或 CSV 即可），字段：`model`, `temperature`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `notes`。这就是专题 07 harness 的雏形。

### 观察重点（写进实验笔记）

- 材料里**没写**的内容，模型是否**仍然断言**（例如「需要兼容 iOS 12」）—— 体会「概率生成 ≠ 有依据」。
- `prompt_tokens` 如何随 PRD 变长而增加—— 体会后面为什么要 context 预算和 RAG。
- 要求「只输出 JSON」时，是否仍夹带 Markdown 说明—— 体会为什么要 Schema + 校验（专题 03）。

---

## 主流框架实现

| 方式 | 是什么 | 在本项目中的位置 |
| --- | --- | --- |
| **OpenAI SDK** | 官方 Python 客户端，也支持 `base_url` 对接兼容 API | M1 起封装进 `llm_core`（专题 01） |
| **OpenAI 兼容 HTTP** | 同一 JSON 格式，换 base_url / key | 国内多数平台；由 Provider 适配 |
| **LangChain ChatModel** | 框架对 Chat API 的再封装 | `03_rag` 组合链时，**配置仍读 `llm_core`**，避免两套 model 名 |
| **LangGraph** | 带状态的图执行 | `04_agent`；节点内调用 `LLMClient` |

原则：**业务代码只依赖 `llm_core`，不 scattered 地 `OpenAI(...)`**。这样换供应商、记日志、统一错误类型只需改一处。

---

## 失败分析与能力边界

### 在本场景下常见的「看起来能用其实不行」

| 现象 | 可能原因 | 谁来解决 |
| --- | --- | --- |
| 风险列表每次不同 | 概率生成 + 参数 | temperature、固定 Prompt、eval 回归 |
| 编造接口/规则 | 材料未提供 | RAG + 拒答（V1） |
| 回答变短、漏后半段 PRD | 上下文截断 | Context 工程；RAG 只检索相关 chunk |
| 前端接不住结果 | 自由文本 | Schema（V1） |
| 429 / 超时 | 平台限流、网络 | 错误分类、fallback（专题 06） |

### LLM 层**单独**无法可靠负责的 5 类事

1. **企业内部知识从哪来、是否最新** → `03_rag` 知识库与入库  
2. **答案是否有依据、引用是否真实** → RAG 检索 + citation checker（V1）  
3. **查工单、调接口、多步流程** → `04_agent` Tool / Workflow  
4. **改 Prompt 后是否真的变好** → `05_eval` golden set / bad case  
5. **用户看到进度、人工确认** → `06_ai_native` 工作台  

### 不在本篇展开

- RAG 主链路、LangChain Document / Retriever  
- FastAPI、SSE、Docker  
- 评审维度矩阵全文 → [07_projects/03](../07_projects/outline.md)  

---

## 评估观测

从**第一次**调用开始就记录，避免「感觉变好了」却无法证明。

### 最小日志字段

| 字段 | 用途 |
| --- | --- |
| `timestamp` | 对比不同天的实验 |
| `model` / `provider` | 选型 |
| `temperature` 等 | 复现 |
| `usage.prompt_tokens` / `completion_tokens` | 成本 |
| `latency_ms` | 体验 |
| `input_summary` | 样例标识（如「售后 PRD 片段」） |
| `output_preview` | 人工回看 |
| `notes` | 是否编造、是否可用 |

### 最小调用样例集（建议先收 5 条）

| id | 类型 | 输入概要 |
| --- | --- | --- |
| S1 | 需求摘要 | 短 PRD 提炼模块与目标 |
| S2 | 风险识别 | 售后按钮 + 接口 v2 |
| S3 | 无材料 | 只有一句「这个需求有什么问题」—— 观察是否胡编 |
| S4 | 约束输出 | 要求 JSON 列表—— 观察格式遵守度 |
| S5 | 长文本 | 较长 PRD 片段—— 观察 token 与遗漏 |

不必等 RAG 完成再建样例；后续 RAG / Schema 改动都应用同一批样例对比。

---

## 小项目实战

为**需求评审助手**定义 LLM 层职责边界（本专题不写代码实现，只定契约）：

| 任务 | LLM 层做什么 | LLM 层不做什么 |
| --- | --- | --- |
| 需求摘要 | 压缩 PRD、提取目标与范围 | 不补充材料里没有的功能 |
| 风险识别 | 按 Prompt 维度描述风险 | 不做最终过会结论 |
| 结构化输出 | 按 Schema 填字段 | 不跳过 Pydantic 校验 |
| 引用说明 | 在 Prompt 要求下绑定 source_id | 不验证 id 真假（校验在 RAG/应用） |
| 拒答建议 | 输出「证据不足」类结论 | 无依据时不强答 |

### 与项目版本

| 版本 | LLM 层支撑 |
| --- | --- |
| **V0** | 能调模型 + 固定 Prompt 生成（配合 RAG 检索上下文） |
| **V1** | + Schema 评审报告 + 拒答结构（专题 02、03） |

---

## 项目收敛

### 能力边界总表

| 能力 | `02_llm` | 下游 |
| --- | --- | --- |
| 统一模型调用 | 01–10 `llm_core` | — |
| Prompt 任务协议 | 02 | — |
| Structured Output | 03 | — |
| 流式 / 上下文 / 可靠性 / harness | 04–07 | — |
| 检索 / 引用 / 拒答逻辑 | 概念 | `03_rag` |
| Tool / Agent / Workflow | 认知 | `04_agent` |
| 系统化 eval / trace | 铺垫 | `05_eval` |
| 运行态 UI | 事件格式铺垫 | `06_ai_native` |

### `llm_core` 目标结构（设计输入）

```text
source/packages/llm_core/
├── client.py           # LLMClient（01）
├── providers/          # 多供应商（01）
├── prompts/            # 模板 registry（02）
├── schemas/            # Pydantic（03）
├── context/            # 上下文构造（05）
├── streaming/          # 事件（04）
├── reliability/        # 错误与降级（06）
└── harness/            # 回归样例（07）
```

### 交给专题 01–03 的设计清单

1. `LLMResponse` 统一响应 + 错误枚举  
2. `models.yaml`：Chat / Embedding / Rerank 分角色  
3. 命名 Prompt：`requirement_summary`、`risk_review` 等  
4. 核心 Schema：`ReviewRisk`、`ReviewReport`、`Citation`、`RefusalResponse`  
5. 上文 5 条样例集 + 日志字段约定  

---

## 完成标准

- **能解释**：LLM 是什么（应用开发者版）；它和规则程序、搜索、数据库的分工。  
- **能解释**：为什么需求评审助手不能只做「复制 PRD 到 ChatGPT」。  
- **能讲述**：小周提交售后 PRD 时，只做一次 API 调用会在产品/工程上出哪些问题（至少 3 点）。  
- **能画出**：用户 → API → `llm_core` →（RAG / Agent）→ 报告 的数据流。  
- **能运行**：一次最小 chat 调用，并解读 `usage` 与 `latency_ms`。  
- **能列举**：5 类 LLM 层无法单独解决的事及对应课程/模块。  

### 自检题（不看正文能否答）

1. LLM 的「生成」和数据库「查询」本质区别是什么？  
2. 为什么 `temperature=0` 仍然可能产生与材料不符的风险描述？  
3. 需求评审助手里，`02_llm` 和 `03_rag` 各解决哪一类问题？  

---

## 相关专题

- 下一篇：[01_model_api_and_provider_abstraction.md](01_model_api_and_provider_abstraction.md)  
- 课程大纲与代码里程碑：[outline.md](outline.md)  
- RAG 为何需要单独一门课：[03_rag/outline.md](../03_rag/outline.md)  
- 评审业务场景：[07_projects/03](../07_projects/outline.md)  
- Transformer 原理补充（按需）：[99_foundation/outline.md](../99_foundation/outline.md)  
