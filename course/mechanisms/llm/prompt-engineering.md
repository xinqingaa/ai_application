# 面向应用的 Prompt Engineering

> 机制篇：解释任务描述如何成为可命名、可版本化、可回归的 Prompt 协议，以及它如何与 Schema 和检索证据分工。
>
> 课程位置：[标准学习路径](../../learning-path.md) V0 第四步。必要前置是 [模型输入输出契约](../../concepts/model-input-output-contracts.md)和 [模型 API 与 Provider](model-api-and-provider.md)；本文交付可命名、可版本化、可比较的任务协议。

---

## 为什么随手写 Prompt 无法持续迭代

同一个模型、同一份售后 PRD，只改下面两段指令就可能产生完全不同的产品行为：

```text
版本 A：帮我评审这份需求。

版本 B：只依据 Requirement 和 Evidence，
从状态、接口、多端一致性和验收标准识别风险；
证据不足时输出待确认问题，不得补充不存在的接口。
```

差异不只是“第二段写得更详细”。版本 B 已经开始定义任务、材料边界、禁止行为和结果意图。若这些内容继续散落在 Python 字符串里，应用无法知道线上使用了哪一版，也无法固定变量比较改动。

本文直接解决三件事：

```text
Prompt 如何成为命名任务协议
→ 变量怎样被渲染成 messages
→ 版本变化怎样被真实样例比较
```

Schema 负责最终接受什么结构，RAG 负责提供真实证据；Prompt 不替代它们。

## 把 Prompt 变成任务协议

### 本节方案性质

Prompt Engineering 没有一套放之四海而皆准的“标准答案”。本节给出的做法，是在需求评审助手场景下比较适合学习和工程演进的一套实践。

需要区分三层：

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | Prompt 应该有清晰任务边界、变量来源、版本记录和可回归对比；不能把所有失败都靠“多写几句提示”解决 |
| **工程实践** | 用 YAML 保存 Prompt，用 `prompt_id@version` 定位，用固定样例 + 固定 temperature 对比版本 |
| **项目取舍** | 本节只落地 `review.risk_review`，用静态 `evidence_block` 模拟后续 RAG，不代表所有业务都要先这样组织 |

因此，六段式任务协议、三版 Prompt、YAML 模板和 `prompt_compare.py` 都不是行业八股答案。它们的价值在于帮助你形成判断：一个 Prompt 是否可解释、可修改、可对比、可进入项目闭环。换到客服、合同审查或测试用例生成场景，原则仍然适用，但任务段落、变量、示例和版本策略都应重新设计。

### Prompt 是什么：任务协议，不是咒语

```text
messages = 任务协议（Prompt 模板 + 变量）
         + 模型参数（temperature、max_tokens）
         + 引擎（config_ref）
```

**Prompt 不负责选模型**（Provider 调用层），**不负责检索**（RAG），**不负责工具**（Agent）。它负责：角色、任务、材料边界、约束、（可选）示例、输出形态。

把 Prompt 看成「任务协议」之后，写法会发生一个明显变化：你不再追求某一句神奇提示词，而是把模型这一轮必须完成的工作拆成可检查的组成部分。协议里要写清楚：模型扮演什么角色、只处理什么材料、产出什么、不能做什么、结果如何被后续程序消费。

这和聊天框里的临时提示不同。临时提示只需要让当前回答看起来不错；任务协议要能被版本管理、能被回归比较、能在不同模型上复现，并且能让后续 Schema、RAG、Eval 接上来。需求评审助手不是聊天玩具，它需要把「风险识别」「缺失追问」「报告汇总」这些任务做成稳定能力。

一个实用判断是：如果这段 Prompt 改动会影响产品输出质量，就不应该只藏在 Python 字符串里；它应该有 `prompt_id`、`version`、变量契约和对比样例。

### 从硬编码到可回归：机制递进

**第 1 步 · 代码里写死字符串（Provider 调用层 `provider_switching` 顶部）**

```python
SYSTEM_PROMPT = "你是需求评审助手。只根据用户材料分析..."
messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prd}]
```

能跑，但改约束要改代码、难 diff、难绑定 eval，多任务易互相污染。

**第 2 步 · f-string / format 拼 user**

```python
user = f"【PRD】\n{prd}\n【证据】\n{evidence}"
```

材料与代码略分离，**任务语义仍散落在 Python**，版本不可见。

**第 3 步 · YAML 模板 + `{{variable}}`**

任务正文进 `prompts/review/*.yaml`，`requirement_text`、`evidence_block` 由调用方注入。Git diff 可见约束变化。

**第 4 步 · `prompt_id` + `version`**

业务只引用 `review.risk_review@2.0.0`，对比实验只换 version，不换代码路径。

**第 5 步 · 受控对比（`prompt_compare.py`）**

固定 `SAMPLE_ID`、`TEMPERATURE`、`config_ref`，只扫 `PROMPT_VERSIONS`——这是 Prompt 工程里最小的「科学方法」，完整 harness 在 调用 Harness。

```text
硬编码 → 拼字符串 → YAML 模板 → prompt_id@version → 固定样例对比
```

### 六段式任务协议

| 段落 | 作用 | `review.risk_review` 要点 |
| --- | --- | --- |
| **role** | 角色与边界 | 「研发视角」「只基于材料」 |
| **task** | 原子目标 | 「识别研发侧风险，标明类别与依据」 |
| **context** | 材料占位 | `{{requirement_text}}`、`{{evidence_block}}` |
| **constraints** | 必须/禁止 | 不得编造；证据不足不硬答；维度 checklist |
| **examples** | few-shot 参考 | v3：一条合格风险风格（注明勿照搬） |
| **output_format** | 输出形态 | v2：自然语言列表；v3：JSON 字段描述 |

**为什么要拆段？** 方便受控实验：v1→v2 通常只加 **constraints + evidence**；v2→v3 通常只动 **example + output_format**。糊成一段则无法判断「是哪类修改起了作用」。

六段式不是固定格式，更不是每个 Prompt 都必须写成六个标题。它的价值在于提供一种拆解视角：当模型输出不好时，你能判断问题来自哪里。

如果模型角色错了，风险审查可能变成产品建议；如果 task 太大，模型会把摘要、风险、解决方案揉成一团；如果 context 边界不清，模型会用常识补材料；如果 constraints 缺失，模型会编造接口和流程；如果 example 质量差，模型会照搬旧规则；如果 output_format 只写「尽量结构化」，后续程序就很难稳定解析。

所以 Prompt 工程不是越写越长，而是让任务边界更硬、变量来源更清、输出预期更可检查。

### Few-shot：何时有用、怎么写才不污染

**适合**：输出风格、字段粒度、类别划分方式——模型靠示例对齐「合格长什么样」。  
**不适合**：用示例偷偷塞进**会变的业务规则**（旧接口名、过期状态机），模型会照搬。

v3 的 Example 段写法要点：

- 只示范**结构与表述深度**，并写明「勿照搬内容」；
- 示例进 YAML 与 **version** 一起管理，过时则升版本或删示例；
- 系统化淘汰靠 调用 Harness eval，本节用肉眼对比 v2 vs v3 即可。

**反例**：示例里写死「接口必须走 v1」，PRD 已改 v2，模型仍反复强调 v1——这是 **Few-shot 污染**，不是模型「笨」。

Few-shot 的本质不是“给模型更多材料”，而是“用样例定义边界”。例如风险等级到底写 `high / medium / low`，风险理由需要一句话还是一段话，引用依据要不要带 `source_id`，这些很难只靠抽象规则说清楚。一个好示例能让模型快速理解“合格答案长什么样”。

但 Few-shot 也有代价。示例越具体，越容易被模型照搬；示例越多，Prompt 越长，成本越高，噪声也越多。对需求评审助手来说，初期更推荐少量高质量示例，而不是堆很多历史评审记录。历史评审记录更适合进入 RAG 或 eval，而不是直接塞进 Prompt。

判断是否需要 Few-shot，可以问三个问题：

1. 当前失败是不是“边界不清”导致的？例如风险类别总是混乱。
2. 用文字规则是否已经说不清？例如“理由要具体但不要过度展开”。
3. 示例是否稳定不过期？例如输出风格稳定，业务规则不稳定。

如果失败来自缺少证据，Few-shot 解决不了；应该去做 RAG。如果失败来自字段漂移，Few-shot 只能缓解；应该去做 Schema。如果失败来自不同样例质量不稳定，应该准备 eval/harness，而不是继续加示例。

### Prompt 与 Schema 的分工

| 层 | 谁定义 | 做什么 | 本节 |
| --- | --- | --- | --- |
| Prompt | 产品 / 提示工程师 | 任务目标、材料边界、输出**描述** | v3 文字要求 JSON 字段 |
| Schema | 应用 / 后端 | 字段名、类型、枚举、必填 | **结构化输出** 实现 `ReviewRisk` 等 |
| 校验器 | 应用 | `model_validate`、业务规则、citation 检查 | **结构化输出** |

类比：Prompt 像「请按报名表填写」；Schema 像「报名表表格本身」。只改 Prompt 而不做 Schema，模型仍可能字段漂移——v3 你会看到「像 JSON 但不一定能 `json.loads` / 字段不全」，这正是 结构化输出 存在的理由。

### Prompt 与 RAG 证据的分工

| 层 | 职责 |
| --- | --- |
| **RAG（RAG）** | 从知识库检索，格式化出带 `source_id` 的片段 |
| **Prompt** | 通过 `{{evidence_block}}` 接收片段，并要求结论绑定材料、证据不足时拒答或追问 |
| **应用** | 校验 citation 是否指向真实 source（RAG / 结构化输出 结构化课深化） |

本节使用静态文件 [`evidence_s2.json`](../../../source/demos/model_contract_lab/evidence_s2.json) 模拟检索结果，观察 **有 Evidence 约束时输出如何变化**——不实现向量检索。

这里有一个常见误区：在 Prompt 里写“请依据公司规范回答”，并不等于模型真的拥有公司规范。Prompt 只能规定“如果有证据，应该如何使用证据；如果没有证据，应该如何拒答或追问”。证据从哪里来，是 RAG 的职责。

所以本节的 `evidence_block` 是一个过渡设计。它让你提前感受“把证据显式放进上下文后，Prompt 应该如何约束模型使用证据”，但它不是知识库。到 RAG 时，`evidence_block` 会从静态 JSON 变成检索结果；到结构化输出和评估阶段，还要检查引用是否真的存在。

对前端体验来说，这个分工也很关键。用户最终看到的不应该只是“模型说有风险”，而应该能看到风险背后的证据来源。Prompt 负责要求模型绑定证据，RAG 负责提供证据，应用负责校验证据和展示证据。

### 变量与模板渲染

常用变量（需求评审助手）：

| 变量 | 含义 | 本节来源 |
| --- | --- | --- |
| `requirement_text` | 用户 PRD / 需求描述 | `samples.json` 样例 `user_content` |
| `evidence_block` | 检索到的证据格式化文本 | `evidence_s2.json`（静态） |
| `review_dimensions` | 可选维度标签 | 后续 workflow 用 |
| `previous_summary` | 多步工作流上游摘要 | Agent / workflow 用 |

渲染规则（实现见 [`registry.py`](../../../source/packages/llm_core/prompts/registry.py)）：

- YAML 中 `system` / `user` 字符串里的 `{{variable}}` 由 `render_prompt(template, variables)` 替换。
- 未提供的占位符替换为空字符串（应避免漏传关键变量）。
- 输出为 OpenAI 风格 `[{"role":"system",...},{"role":"user",...}]`，直接交给 `LLMClient.chat`。

### 版本管理：`prompt_id` + `version`

每个 YAML 文件包含：

```yaml
prompt_id: review.risk_review
version: "2.0.0"
model_config_ref: chat.dev_chat
```

- **`prompt_id`**：逻辑名，业务代码只引用它。
- **`version`**：语义化版本字符串；改约束或示例应**升版本**，便于对比与回滚。
- **`model_config_ref`**：该 Prompt **默认**用哪条模型配置（可与 Provider 调用层 的 `chat.dev_chat` 对齐）。

**加载规则（`get_prompt`）**：扫描 `llm_core/prompts/` 下各子目录中的 `*.yaml`，用文件内的 **`prompt_id` + `version` 字段** 定位模板——**不是**用文件名。`risk_review_v1.yaml` 只是人工命名习惯；即便改名，只要 yaml 里仍是 `version: "1.0.0"`，`get_prompt(..., "1.0.0")` 就能找到。

约定：同一 `(prompt_id, version)` 只对应**一个** yaml 文件，避免重复注册。未来 harness（调用 Harness）会把样例绑定到 `prompt_id@version`；本节在笔记里手动记录即可。

版本管理真正解决的是「可讨论」。如果评审负责人说「上周那版更稳」，你需要能回答：上周是哪个 `prompt_id@version`、用的哪条样例、温度是多少、证据块是否相同、模型有没有变。如果这些变量都不可见，Prompt 调优就会变成凭感觉改句子。

本节只做最小版本管理：YAML 存正文，`version` 标记变化，demo 固定样例做对比。后续调用 Harness 会把它扩展成 harness：把样例、Prompt 版本、模型配置、token、延迟和人工观察一起记录。

[`registry.py`](../../../source/packages/llm_core/prompts/registry.py) 核心查找逻辑：

```python
def get_prompt(prompt_id: str, version: Optional[str] = None) -> PromptTemplate:
    candidates = []
    for path in _iter_prompt_files():
        data = _load_yaml(path)
        if data.get("prompt_id") != prompt_id:
            continue
        candidates.append(_parse_template(data, path))
    ...
    target = _normalize_version(version)
    for tpl in candidates:
        if _normalize_version(tpl.version) == target:
            return tpl
```

[`render_prompt`](../../../source/packages/llm_core/prompts/registry.py) 把 `{{variable}}` 替换后输出 messages。未提供的占位符变为空字符串——**漏传 `evidence_block` 会导致 Evidence 段为空**，这是常见配置错误。

这段代码只展示两个机制：**按逻辑名找模板**，以及**把变量渲染成 messages**。不要把学习重点放在扫描文件的细节上；真正要掌握的是：Prompt 真源从业务代码里移出来以后，调用方仍然可以用稳定的 `prompt_id@version` 得到一组可复现的 `messages`。

### 从 Provider 示例中的硬编码到可维护 Prompt：数据流

```text
prompt_compare.py（实验配置：样例 id、版本列表、temperature）
    │
    ├─ load_sample(S2)  → requirement_text
    ├─ load evidence_s2.json → evidence_block
    │
    ▼
get_prompt("review.risk_review", version="2.0.0")
    │
    ▼
render_prompt(tpl, variables)  → messages
    │
    ▼
LLMClient.chat(messages, tpl.model_config_ref, temperature=0)
    │
    ▼
对比表：v1 / v2 / v3 的 latency、tokens、content 预览
```

Provider 调用层 里写在 `provider_switching.py` 顶部的 `SYSTEM_PROMPT`，在 Prompt 工程 之后应逐步消失——**任务描述进 YAML**，Python 只负责选版本、灌变量、调用客户端。

### 如何判断 Prompt 真的变好了

不要只看「这次输出我更喜欢」。Prompt 对比至少要固定四个变量：

1. 固定样例，例如 S2 售后按钮 PRD。
2. 固定模型配置，例如 `chat.dev_chat`。
3. 固定温度，例如 `temperature=0`。
4. 只改变 Prompt 版本，例如 v1 → v2。

然后观察具体失败是否减少：有没有少编造接口名，是否更贴 Evidence，风险维度是否更稳定，输出是否更接近后续 Schema。若一次改了 Prompt、样例、模型和温度，你就无法知道改进来自哪里。

本节的 Prompt 工程不是追求一次完美答案，而是训练最小可回归方法：**固定变量、只改一处、记录差异、用失败类型指导下一次修改**。

### 最小 Prompt 调试顺序

当输出不好时，不要第一反应就是“再加一句要求”。很多 Prompt 越调越乱，就是因为每次失败都往 system 里追加一句新限制，最后得到一团互相冲突的说明。

本节推荐一个最小调试顺序：

1. **先看任务是否单一**：这轮到底是摘要、风险审查、追问，还是报告生成？如果一个 Prompt 同时做三件事，先拆任务。
2. **再看材料是否足够**：模型是否真的拿到了 PRD 和 Evidence？若材料缺失，补 Prompt 没用。
3. **再看边界是否明确**：是否写明不得编造、证据不足如何处理、风险维度有哪些。
4. **再看输出是否可检查**：是否有稳定段落、字段或结构，方便人工或程序对比。
5. **最后才考虑 Few-shot**：当规则讲不清边界时，用示例对齐风格和粒度。

这套顺序能避免把所有问题都归因于“模型不稳定”。在 AI 应用里，很多所谓模型不稳定，其实是任务接口不稳定：变量来源不清、任务目标混杂、约束冲突、版本不可追踪。

### 坏 Prompt 如何改造成任务协议

先看一个常见坏写法：

```text
你是一个很专业的需求评审助手，请认真分析下面需求，尽量全面，输出风险。
{{requirement_text}}
```

这段 Prompt 看起来礼貌、自然，但工程上有几个问题：

- “专业”没有定义专业视角，是产品、研发、测试还是合规？
- “认真分析”不可验证，后续无法判断它是否遵守。
- “尽量全面”会诱导模型展开很多材料外推。
- “输出风险”没有说明风险类别、依据、证据不足时怎么办。
- 没有版本和变量契约，改完以后无法比较。

把它改造成任务协议，不是简单把文字变长，而是把不可检查的要求换成可检查的约束：

```text
角色：研发团队的需求评审助手。
任务：只基于 PRD 与 Evidence，识别研发侧潜在风险。
材料：{{requirement_text}} 与 {{evidence_block}}。
约束：不得编造接口、状态机、埋点或权限规则；证据不足时说明缺失信息。
输出：按风险类别、等级、理由和依据组织。
```

这版仍然不是最终结构化输出，但它已经具备工程形态：变量边界清楚，任务目标单一，失败更容易归因。若模型仍然编造接口，就优先检查 Evidence 是否为空、constraints 是否被渲染进 messages；若输出字段漂移，就应该进入 Schema 机制，而不是继续在 Prompt 里堆“请严格输出”。

### Prompt 调优与产品判断

Prompt Engineering 不只是技术动作，也包含产品判断。需求评审助手到底要“尽可能多找风险”，还是“只列高置信风险”？要“偏保守拒答”，还是“尽量给出建议并标注不确定”？这些不是模型自动决定的，而是产品策略。

例如同一份 PRD 缺少接口失败兜底说明：

- 如果产品策略偏审慎，Prompt 应要求“证据不足时提出待确认问题”。
- 如果产品策略偏启发式评审，Prompt 可允许“标注为潜在风险，但必须说明依据不足”。

两种策略都可能合理，但不能混在同一版 Prompt 里。否则模型有时拒答、有时猜测，评审负责人会觉得助手性格不稳定。版本化 Prompt 的意义之一，就是让这类产品策略变更可见、可比较、可回滚。

### Prompt 与代码所有权

在 AI Coding 参与下，Prompt YAML 很容易由 Agent 快速生成。但真正掌握不在于“能生成一段看起来不错的 Prompt”，而在于你能解释每一段为什么存在。

你应该能回答：

- 这个 role 限制了模型的哪个视角？
- 这个 constraint 在防哪类失败？
- 这个 example 是否可能过期或污染？
- 这个 output_format 是给人读，还是给 结构化输出 的 Schema 铺路？
- 改这一行后，应该用哪条样例验证？

如果这些问题答不上来，就算 Prompt 现在效果不错，也还没有形成代码所有权。后续进入 RAG 和 Agent 后，Prompt 会更多、更分散，更需要这种解释能力。

---

## 用三版 Prompt 控制一个变量

### 三版 `review.risk_review` 的设计意图

同一任务（风险审查）、同一样例（S2）、同一 `temperature=0`，只变 Prompt 版本：

| 版本 | 文件 | 刻意差异 | 观察重点 |
| --- | --- | --- | --- |
| **v1.0.0** | [`risk_review_v1.yaml`](../../../source/packages/llm_core/prompts/review/risk_review_v1.yaml) | 短 system + 直接把 PRD 当 user | 是否空泛、是否编造接口细节 |
| **v2.0.0** | [`risk_review_v2.yaml`](../../../source/packages/llm_core/prompts/review/risk_review_v2.yaml) | + Task / Evidence / Constraints / 维度 checklist | 是否更贴材料、少幻觉 |
| **v3.0.0** | [`risk_review_v3.yaml`](../../../source/packages/llm_core/prompts/review/risk_review_v3.yaml) | v2 + 1 条 example + **要求 JSON 字段** | 结构是否更稳；JSON 是否可解析（仍可能失败） |

### 核心 API（真实代码）

```python
from llm_core import LLMClient
from llm_core.prompts import get_prompt, render_prompt

tpl = get_prompt("review.risk_review", version="2.0.0")
messages = render_prompt(tpl, {
    "requirement_text": prd_text,
    "evidence_block": evidence_text,
})
resp = client.chat(messages, tpl.model_config_ref, temperature=0)
```

`get_prompt` 在 [`prompts/registry.py`](../../../source/packages/llm_core/prompts/registry.py) 扫描 `prompts/review/*.yaml`；`PromptTemplate` 定义在 [`prompts/template.py`](../../../source/packages/llm_core/prompts/template.py)。`PromptTemplate.ref` 即 `review.risk_review@2.0.0`，应写入实验笔记与后续日志。

这段代码足够说明本节最小闭环：业务不再拼长字符串，而是加载一份命名 Prompt、注入变量、得到 `messages`，再交给 Provider 调用层 的 `LLMClient`。正文不需要展开 registry 的所有文件扫描细节；学习重点是 **Prompt 真源外置以后，业务仍能稳定复现某个任务版本**。

### v1 YAML 片段（极简对照）

```yaml
system: |
  你是研发团队的需求评审助手，负责从研发视角识别 PRD 中的潜在风险。
user: |
  {{requirement_text}}
```

### v2 为何多加 Constraints

v2 的 user 模板显式分出 `## Task`、`## Requirement`、`## Evidence`、`## Constraints`。这是产品里最常见的「质量跃迁」：**不是换更大的模型，而是把禁止编造、维度 checklist 写清楚**。对比实验里重点看 v1→v2 是否减少「接口 v3」「未提及的埋点」类幻觉。

### v3 为何加 Example + JSON 文字

- **Example**：few-shot 只给**风格**，并注明「勿照搬」，降低过时业务规则污染（见失败分析）。
- **JSON output_format**：为后续 Structured Output 做铺垫——本节**不**做 `json.loads` 成功率统计，只在笔记里观察是否多出 Markdown 包裹、字段是否齐全。

v1、v2、v3 的差异刻意保持很少。这样做是为了训练「一次只改一个方向」：v1 观察没有约束时会怎样，v2 观察 Evidence 和 constraints 能否减少幻觉，v3 观察 example 与 JSON 意图是否让输出更接近程序接口。若一口气加入十几个技巧，就很难解释到底是哪一个在起作用。

---

## 模板框架的价值与边界

| 方式 | 做什么 | 与本项目关系 |
| --- | --- | --- |
| **字符串 + `.format` / `{{}}` 替换** | 模板与数据分离 | `llm_core.prompts` 当前实现 |
| **Jinja2** | 条件、循环、包含 | 未引入；任务协议复杂后再考虑 |
| **LangChain `ChatPromptTemplate`** | 把 template 包成 Runnable | RAG 链可读取**同一 YAML 真源**，避免两套 Prompt |
| **厂商 Prompt 管理后台** | 云端版本、A/B | 认知即可；本仓库 YAML + Git 便于学习与 diff |

原则：**配置真源在仓库**（YAML + 变量契约），框架只是消费方。不要在 LangChain 里再写一份与 YAML 不同步的长字符串。

---

## Prompt 失败时先检查什么

### 排查路径（表现 → 原因 → 怎么验证）

**1. 输出空泛、编造接口/系统**

- **表现**：风险里出现 PRD、Evidence 都没有的「支付中台」「埋点 SDK v3」等。
- **原因**：v1 类 Prompt 缺 constraints；或 `evidence_block` 为空仍强答。
- **验证**：`VERBOSE=True` 看渲染后 messages 是否含 Evidence/Constraints；换 v2；`EVIDENCE_FILE` 指向不存在路径看是否收敛。

**2. 约束冲突导致行为飘忽**

- **表现**：同一 version 有时极简有时极长；或摘要与风险任务互相「打架」。
- **原因**：多个任务共用一个 Prompt 或同一 user 段里「尽量简短」与「列全维度」并存。
- **验证**：拆 `prompt_id`；diff 两个 YAML 的 constraints 段。

**3. Few-shot 污染**

- **表现**：模型反复强调示例里的旧业务规则，与当前 PRD 不符。
- **原因**：Example 含具体过期规则且未标注勿照搬。
- **验证**：临时去掉 Example 段升小版本对比；调用 Harness 用 bad case 淘汰。

**4. v3「像 JSON」但程序接不住**

- **表现**：肉眼是 JSON，但有 ` ```json ` 围栏、中文 key、缺字段。
- **原因**：只有 Prompt 软约束，无 Schema（结构化输出 职责）。
- **验证**：用 `json.loads` 初步检查并记录失败形态；Structured Output 机制再用 Pydantic 区分具体失败层级。

**5. 对比实验结论不可信**

- **表现**：换版本同时换了样例或 `temperature`。
- **原因**：未固定实验变量。
- **验证**：只改 `PROMPT_VERSIONS`，保持 `SAMPLE_ID`、`TEMPERATURE=0`。

### Prompt 不能替代什么

检索命中、引用真伪、工具调用、权限审批、统计化 eval——分属 RAG、Agent、业务服务、上下文工程/调用 Harness。Prompt 只定义**任务与边界**。

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| Pydantic、`response_format`、parse 判层 | 结构化输出 | 知 v3 JSON 意图与 Schema 分工 |
| 真实向量检索 | RAG | 会用静态 `evidence_block` 变量 |
| 上下文预算、超长 PRD 裁剪 | 上下文工程 | 知 Prompt 变长即 token 成本 |
| harness 落盘、字段缺失率 | 调用 Harness | 手写对比表 + 观察清单 |
| 六份完整 Prompt YAML | 规划 | 只落地 `review.risk_review` 三版 |
| Prompt 调试八步法、大规模 A/B | 调用 Harness / 上下文工程 | 本节四步受控对比即可 |

### 需求评审助手 Prompt 集（规划表，非本节代码）

| prompt_id | 适用场景 | 主要变量 | 输出（结构化输出 深化） |
| --- | --- | --- | --- |
| `review.requirement_summary` | 评审入口压缩材料 | `requirement_text` | 短摘要 |
| **`review.risk_review`** | **风险识别（本节实现）** | `requirement_text`, `evidence_block` | 风险列表 / JSON |
| `review.technical_impact` | 接口与数据影响 | `requirement_text`, `evidence_block` | impact 列表 |
| `review.test_acceptance` | 测试验收点 | `requirement_text`, `evidence_block` | test_points |
| `review.clarification` | 证据不足追问 | `requirement_text`, `evidence_block` | 追问列表 |
| `review.report_synthesis` | 汇总报告 | 上游结构化字段 | `ReviewReport` |

---

## 运行 Prompt 版本对比

### 目标

**YAML 模板 → 变量渲染 → `LLMClient` 调用** 闭环；在 S2 上对比 v1/v2/v3。

### 涉及文件

关键路径：

- [`source/packages/llm_core/prompts/registry.py`](../../../source/packages/llm_core/prompts/registry.py)：加载与渲染 Prompt。
- [`source/packages/llm_core/prompts/review/`](../../../source/packages/llm_core/prompts/review/)：三版 `review.risk_review`。
- [`source/demos/model_contract_lab/prompt_compare.py`](../../../source/demos/model_contract_lab/prompt_compare.py)：本节观察入口。

完整参数说明、样例列表和命令变体放在 [demo README](../../../source/demos/model_contract_lab/README.md)。

### 实现步骤

1. **阅读三份 YAML**，标出 v1→v2→v3 各多了哪一段语义（constraints / evidence / example / JSON）。
2. **打开 `prompt_compare.py` 顶部实验配置**，确认样例、版本列表和温度。
3. **配置 `.env`**（与 Provider 调用层 相同，`OPENAI_API_KEY`；DeepSeek 用户同步改 `OPENAI_MODEL` 等）。
4. **运行对比**，只观察 Prompt 版本变化带来的输出差异。

### 核心实验变量

入口文件是 [`prompt_compare.py`](../../../source/demos/model_contract_lab/prompt_compare.py)。正文只保留本节必须理解的实验变量：

- `SAMPLE_ID`：默认 S2，表示同一份售后 PRD。
- `PROMPT_VERSIONS`：默认 v1 / v2 / v3，表示只换 Prompt 版本。
- `TEMPERATURE`：默认 0，避免随机性掩盖 Prompt 差异。
- `EVIDENCE_FILE`：默认静态 evidence，用来模拟后续 RAG 检索结果。

若要看完整常量含义、样例列表、文件名关系和命令变体，读 demo README。课程正文里只需要记住：**Prompt 对比要固定样例、模型、温度和证据，只改变版本**。

### 运行方式

```bash
uv sync
cd source/demos/model_contract_lab
uv run python prompt_compare.py
```

### 预期结果

1. 终端先打印样例、prompt id、版本列表。
2. 输出对比表三行（v1 / v2 / v3）：`model`、`latency_ms`、`total_tokens`、`content_preview`。
3. 主观对比（建议记入笔记）：

| 对比项 | v1 | v2 | v3 |
| --- | --- | --- | --- |
| 是否出现未在 PRD/Evidence 出现的接口名 |  |  |  |
| 是否覆盖交互/状态/接口中至少 2 类 |  |  |  |
| 输出是否便于程序解析 |  |  |  |

4. `VERBOSE = True` 时，表后按版本打印 `format_call_log` 详情。

### 推荐实验顺序

1. 默认跑一遍（S2 + 三版 + `evidence_s2.json` + `TEMPERATURE=0`）。
2. 打开 verbose，确认渲染后的 messages 是否真的包含 Evidence / Constraints。
3. 换无材料样例，观察 v1 与 v2 是否都会胡编。
4. 去掉 evidence 文件，观察 v2/v3 是否弱化无依据风险。

### 人工观察清单（代替本节自动化 eval）

- [ ] v2 比 v1 更少「凭空」接口/埋点/权限描述
- [ ] v2 或 v3 会引用 `evidence_s2.json` 中的接口 v2、状态机表述
- [ ] v3 输出更接近 JSON；尝试 `json.loads` 是否一次成功（失败也正常，记原因）
- [ ] 三版 `prompt_tokens` 随 Prompt 变长而增加——体会 **Prompt 长度即成本**

---

## 亲手完成一次 Prompt 变更

以 v2 为基线创建一个新版本，只修改一项产品策略：

> 证据不足时，不再输出低置信风险，改为生成待确认问题。

保持样例、模型、温度、Evidence 和输出观察项不变，然后：

1. 修改 YAML 中对应的 constraint，不在 Python 里增加特殊判断。
2. 确认新旧版本都能被 registry 按 `prompt_id@version` 加载。
3. 在有证据和无证据样例上分别比较。
4. 记录无依据风险、待确认问题、Token 和输出结构变化。
5. 说明为什么这属于 Prompt 产品策略，而不是 Schema 或 Retriever 修改。

## 怎样判断 Prompt 可被项目维护

- **能解释**：六段式协议；Prompt 与 Schema、RAG 的边界；Few-shot 何时有用。  
- **能说明**：硬编码 → YAML → `prompt_id@version` 的递进各解决什么。  
- **能运行**：`prompt_compare.py` 并读懂对比表。  
- **能改造**：复制 v2 改一条 constraint、升 version 再对比。  
- **能判断**：至少 3 种失败模式及验证方式。

### 运行与观察

```bash
cd source/demos/model_contract_lab
uv run python prompt_compare.py
```

详见 [demo README](../../../source/demos/model_contract_lab/README.md)。

### 自检题（不看正文能否答）

1. `requirement_text` 和 `evidence_block` 在真实产品里分别通常由谁提供？  
2. 为什么 v1 往往比 v2 更容易编造？  
3. v3 要求 JSON 字段与 结构化输出 Pydantic Schema 还有什么差别？  
4. 对比 Prompt 版本时为什么要固定 `temperature` 和样例？  
5. 为什么 Prompt 放在 YAML 而不是 `provider_switching.py`？  
6. `PROMPT_VERSIONS` 与 `risk_review_v1.yaml` 文件名是什么关系？  
7. Few-shot 示例写过期业务规则会导致什么现象？怎么验证是示例问题？

---

## 交给项目的 Prompt 真源

- 新增 `llm_core.prompts`（`get_prompt`、`render_prompt`、三份 `review.risk_review` YAML）与 `prompt_compare.py`。  
- 需求评审助手具备：**按任务版本渲染 messages、与 `LLMClient` 衔接**；风险审查可在固定样例上受控对比。  
- Structured Output 会继续消费这里的 Prompt 协议，但它不是由本页自行指定的“下一课”。

完成实验后回到 [标准学习路径](../../learning-path.md)。需要查完整知识关系时再使用 [知识地图](../../knowledge-map.md)。
