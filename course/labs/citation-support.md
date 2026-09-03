# Citation 支持性校验实验

> 这是[引文真的支持这条结论吗](../mechanisms/citation-support.md)的配套实验。第 16 节已经完成结构化生成和来源集合成员检查；本实验冻结 Retriever、Context 和风险生成，不再重新调用它们，只观察一条合法来源声明怎样经过逐字引文定位和真实模型支持判断。

本实验只回答一个问题：保持 Claim 与逐字引文不变，只改变引文周围的来源内容和适用条件时，应用怎样区分“引文不存在”“内容支持”“内容无关”和“来源反驳”？

它能用确定性测试证明定位、跳过、批量身份和失败契约，也能观察当前真实模型怎样判断支持关系。一次真实运行不能证明判断器在所有业务资料上都准确，也不能证明整份评审证据充分。

## 1. 为什么本实验不重新跑 Retriever 和风险生成

第 16 节已经固定了结构化风险和来源成员资格。本节新增的生成版本要求 Citation 必须带逐字 `excerpt`；为了不让风险生成的随机变化干扰支持判断，实验直接固定升级后交给校验器的输入：

```text
一条需要外部资料支持的具体说法
+ 已经通过成员检查的 source_id
+ 模型按新 Schema 声明的逐字 excerpt
```

如果本实验重新改变检索 Query、Top-k、Context 预算或风险生成 Prompt，那么 Claim、来源和引文可能一起变化。最终看到 `supported` 或 `unrelated` 时，无法判断差异来自上游候选，还是来自本节的支持关系。

因此主入口直接读取固定探针：

```text
CitationSupportInput[]
+ 本轮允许的 ContextSource[]
→ 确定性定位
→ 一次真实结构化模型判断
```

这不是用静态结果代替真实模型。静态 fixture 只固定模型要判断的输入；支持关系仍由当前配置的真实 Chat Provider 判断。Mock 只在单元测试中证明确定性状态机和失败契约。

## 2. 运行前准备

本实验不访问 PostgreSQL，不调用 Embedding，也不执行 Retriever。需要：

- 根环境已经通过 `uv sync` 安装。
- `chat.structured_chat` 对应的真实 Chat Provider、模型和 Key 可用。
- Provider 支持当前选择的 Structured Output 模式。
- 当前 Prompt 与 fixture 能从安装后的 package 中读取。

在仓库根目录执行：

```bash
uv sync
set -a && source .env && set +a

uv run python -c 'import openai, pydantic; print(openai.__version__, pydantic.__version__)'
```

当前 `uv.lock` 对应：

```text
openai 2.44.0
pydantic 2.13.4
```

版本号只说明本次实验使用的客户端环境，不保证 endpoint、模型和账户额度可用。运行时仍要读取输出中的 `provider`、`model`、`config` 与 `structured_mode`。

查看探针身份：

```bash
uv run python -c '
import json
from pathlib import Path
p = Path("source/apps/review_assistant/fixtures/rag/generation/citation_support_probes.json")
d = json.loads(p.read_text())
print(d["fixture_kind"], d["version"])
print(d["claim_text"])
print([v["name"] for v in d["variants"]])
'
```

## 3. 唯一主入口、参数和退出状态

唯一主入口是：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py
```

查看实际参数：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py --help
```

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `--variants` | 四组全跑 | 选择支持、无关、反驳或引文不存在探针 |
| `--structured-mode` | `json_schema` | 选择 Provider 侧结构约束方式 |
| `--config-ref` | `chat.structured_chat` | 选择真实 Chat 配置 |
| `--log-format` | `compact` | 可切换 `verbose`、`json` 或 `quiet` |
| `--verbose` | 关闭 | 展开来源身份、引文位置、判断理由和原始响应 |

退出状态区分实验是否完成与 Citation 是否获得支持：

| 状态 | 含义 |
| ---: | --- |
| `0` | 输入完成定位流程，并形成真实模型判断报告；某条结果可以是无关、反驳、无法判断或结构化输出无效 |
| `1` | fixture、配置、鉴权、额度、网络或 Provider 使实验没有形成支持性报告 |

`contradicted` 是成功观察到的一种业务结果，不应让 shell 返回 `1`。相反，额度耗尽发生在真实模型调用之前，即使确定性定位已经成功，实验仍返回 `1`。

## 4. 唯一主要变量：引文周围的来源语境

四组共用同一句 Claim：

```text
现行售后接口 v2 的所有请求都必须提供 source_channel。
```

也共用同一句模型引文：

```text
请求必须提供 source_channel。
```

变化的是这句话在来源中处于什么范围和条件：

| variant | 引文周围的来源内容 | 运行前预测 |
| --- | --- | --- |
| `supported` | 现行 v2、全部入口、全部请求 | 定位成功，预期支持 |
| `unrelated` | 营销曝光规则，明确不适用于售后 | 定位成功，预期无关 |
| `contradicted` | 引文属于废弃 v1，现行 v2 允许省略 | 定位成功，预期反驳 |
| `missing_quote` | 来源中没有这句引文 | 定位失败，不进入模型判断 |

前三组使用不同稳定 `source_id`，只是为了在同一次批量请求中保留来源身份；模型真正需要比较的主要变量是完整来源语境。

运行前先写下两条不变量：

```text
前三组必须先通过确定性定位，才能观察语义判断
missing_quote 必须在真实模型调用前被拦截
```

不要预测模型 `reason` 的具体措辞。真实模型可能使用不同语言解释同一关系。

## 5. 先单独运行引文不存在

先观察不需要模型判断的边界：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py \
  --variants missing_quote \
  --verbose
```

运行前预测：

```text
source_id 属于本轮允许集合
excerpt 不在对应来源中
location = quote_not_found
model calls = 0
verdict = —
VerifiedCitation = 0
```

按顺序观察：

1. `source_id` 是否仍是 `CS-MISSING`；
2. 原始 `excerpt` 是否被完整保留；
3. `location` 是否为 `quote_not_found`；
4. `model calls` 是否为 `0`；
5. 输出是否没有伪造 `indeterminate`。

这一组证明：确定性定位可以挡住不存在的引文，而且没有为了得到一个语义标签去调用模型。它不能证明真实模型的支持判断能力。

## 6. 再运行一条真实支持关系

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py \
  --variants supported \
  --verbose
```

运行前预测：

```text
引文唯一存在
location = located
保留 source locator 与 chars 范围
model calls = 1
真实模型应倾向于 supported
```

输出中先看定位，不要先看模型结论：

```text
source_id
→ excerpt
→ location
→ locator + chars
→ verdict
→ reason
```

若模型给出 `supported`，它只说明当前真实模型在固定 Prompt 和 Schema 下认为该来源支持 Claim。一次绿色结果不能替代后续 Golden Set 或人工校准。

## 7. 最后做三种语义关系的批量对照

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py \
  --variants supported,unrelated,contradicted \
  --verbose
```

运行前预测：

```text
三个 excerpt 都能唯一定位
三个项目合并成一次模型调用
返回的 claim_id 必须与输入顺序完全一致
预期依次为 supported / unrelated / contradicted
只有 supported 进入 verified_citations
```

重点比较：

- 三组是否都显示 `located`。
- `model calls` 是否仍然是 `1`，而不是三次。
- 无关组是否因为关键词相同被误判为支持。
- 反驳组是否读取了“废弃 v1”和“现行 v2”两处条件。
- `reason` 是否只解释输入资料，没有补充外部事实。

再一次运行四组，观察定位和判断怎样在同一份报告中汇合：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py \
  --variants supported,unrelated,contradicted,missing_quote
```

正常情况下应看到：

```text
input = 4
located = 3
quote_not_found = 1
model calls = 1
judged = 3
```

真实模型的三个 verdict 是观察值，不是 shell 成功的硬编码条件。

## 8. 怎样读取 Token、成本和延迟

真实调用完成后，报告显示：

```text
usage
prompt tokens
completion tokens
total tokens

estimated cost
total cost
price label

latency
```

四组中 `missing_quote` 不进入模型请求，因此不会占用支持判断的输入 Token。其余已定位项目合并为一次请求；这能避免声明数量增长时逐条发起调用。

成本可能显示 `unknown`。这表示当前模型没有匹配本地学习价格表，不表示调用免费。真实账单以 Provider 为准，本地值只用于同配置实验比较。

## 9. 真实失败与业务结果要分开

### 鉴权、额度和网络失败

表现：

```text
ERROR auth / rate_limit / timeout / provider
进程退出 1
```

这说明支持判断没有完成。不要改用 Fake 模型继续主实验，也不要把全部项目标成 `indeterminate`。

### 结构化输出失败

Provider 已返回内容，但它不是合法 JSON、Schema 不匹配或 verdict 不在枚举中。报告应显示：

```text
validation status = structured_output_invalid
parse error stage = json 或 schema
verified citations = 0
```

进程可以返回 `0`，因为实验已经成功观察到业务校验结果；但这个结果不能进入后续证据充分性判断。

### 返回身份集合错误

模型少回、多回、重复或改变 `claim_id` 顺序时：

```text
validation status = judgment_set_invalid
verified citations = 0
```

不能只消费“看起来正确”的那几条。批量映射本身就是支持校验的一部分。

### 引文位置不唯一

同一句 `excerpt` 在来源中出现两次时，定位结果是：

```text
ambiguous_quote
match_count > 1
```

当前机制不擅自选择第一次，也不进入模型判断。产品若以后保存更精确的模型 locator，可以在保持这条不变量的前提下增加消歧输入。

## 10. 按表现定位问题

| 表现 | 先检查的层次 | 验证方式 |
| --- | --- | --- |
| 合法来源却是 `source_not_allowed` | Context 允许集合与传入原文不一致 | 对照 `citation_source_ids` 和 `source_id` |
| 明明能看到原文却 `quote_not_found` | excerpt、Unicode、空白或标点 | `--verbose` 对照原始引文和来源全文；运行定位测试 |
| 同一句出现两次却进入模型 | 确定性定位契约 | 运行 ambiguous quote 单元测试 |
| 三组触发三次调用 | 批量组装位置错误 | 查看 `model calls` 和测试中的 client call 数 |
| 模型把营销规则判为支持 | 支持 Prompt 或模型判断能力 | 对照完整 `source_content`，保留 bad case，不改定位规则 |
| 反驳组被判支持 | 版本和适用条件未被正确读取 | 检查 Prompt 中是否包含完整来源，而不只有 excerpt |
| `indeterminate` 出现在 Provider 超时后 | 依赖错误被静默降级 | 检查异常映射，真实错误必须退出 `1` |
| verdict 有结果但映射到错误 Claim | 返回身份集合校验 | 检查输入与输出 `claim_id` 顺序 |

排查时不要回到 Embedding、RRF 或 Top-k。本实验没有运行这些上游步骤。

## 11. 确定性测试证明什么

运行：

```bash
uv run pytest source/packages/rag_core/tests/test_citation_support.py -q
```

测试覆盖：

- 三条已定位声明只触发一次模型边界。
- 引文不存在、为空、来源不允许或位置歧义时不调用模型。
- NFKC、换行与连续空白可以有限归一化。
- 无关、反驳和无法判断不会形成 `VerifiedCitation`。
- 返回身份集合错误、JSON 和 Schema 失败不会变成支持。
- Token usage 和模型调用数量进入报告。

测试中的 Fake 结构化客户端只用于稳定制造模型边界结果。它证明状态、映射和失败契约，不证明真实模型能正确判断自然语言支持关系。后者必须运行主入口观察。

## 12. 读码路径

只追一条 `supported` 输入，不做全仓库源码导览：

```text
fixture
source/apps/review_assistant/fixtures/rag/generation/citation_support_probes.json
        ↓
demo 主入口
source/demos/rag_retrieval_lab/inspect_citation_support.py
        ↓
公共入口
rag_core.validate_citation_support
        ↓
两段机制
rag_core/evidence/service.py
        ↓
Prompt 与 Structured Output
llm_core/prompts/review/citation_support_v1.yaml
llm_core.LLMClient.chat_structured
        ↓
确定性契约
source/packages/rag_core/tests/test_citation_support.py
```

阅读时回答：

1. 哪一行决定引文不存在时不调用模型？
2. 完整来源内容在哪里进入 Prompt？
3. 返回的 `claim_id` 在哪里与输入集合比较？
4. 只有哪种 verdict 会形成 `VerifiedCitation`？
5. 真实 `LLMError` 为什么没有被转换成 `indeterminate`？

## 13. 修改任务：让唯一位置变成歧义

只修改 fixture 中 `supported` 的 `content`，把逐字引文重复一次：

```text
请求必须提供 source_channel。
……
请求必须提供 source_channel。
```

其他字段保持不变。运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py \
  --variants supported \
  --verbose
```

修改前预测：

```text
location = ambiguous_quote
match_count = 2
model calls = 0
verdict = —
verified citations = 0
```

不应变化的契约：

- `source_id` 仍属于允许集合。
- 应用不自动选择第一次出现的位置。
- 没有唯一位置就不进入语义支持判断。
- 真实模型配置不影响这个确定性结果。

完成观察后恢复 fixture，再运行：

```bash
uv run pytest source/packages/rag_core/tests/test_citation_support.py -q
uv run python source/demos/rag_retrieval_lab/inspect_citation_support.py \
  --variants supported,unrelated,contradicted,missing_quote
```

## 14. 完成自检

完成本实验后，应当能够：

- 从一条合法来源声明回到对应原文。
- 解释有限归一化和语义改写的边界。
- 区分引文不存在、内容无关、来源反驳和无法判断。
- 说明为什么前三组进入模型、`missing_quote` 不进入。
- 读懂批量身份、Token、成本、延迟和结构化失败。
- 区分 Fake 测试证明的确定性契约与真实模型观察。
- 不用一条 `supported` 结果宣称整份评审证据充分。
