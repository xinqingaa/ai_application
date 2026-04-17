# 06. 错误处理、成本控制与安全 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/06_reliability_cost_security.md) 一步步完成第六章实践

---

## 核心原则

```text
先识别错误类型 -> 再理解重试边界 -> 再建立成本观测 -> 再加入缓存和配额 -> 最后补上基础安全防护与统一服务层
```

- 在 `source/02_llm/06_reliability_cost_security/` 目录下操作
- 这一章的重点不是“罗列一堆风险名词”，而是把可靠性、成本、安全变成应用侧真正可执行的工程能力
- 没有 API Key 时，绝大多数示例仍然可以运行，因为本章很多内容本来就适合用 mock 和本地模拟方式学习
- 有真实模型时，依然优先推荐百炼 / 通义、DeepSeek、GLM；教学理解继续参考 OpenAI / Claude / Gemini 的主流设计思路
- 这一章默认你已经理解前五章：普通聊天、provider 配置、Prompt、结构化输出、流式接口

---

## 项目结构

```text
06_reliability_cost_security/
├── README.md                 ← 你正在读的这个文件
├── .env.example              ← 第六章环境变量模板
├── reliability_utils.py      ← 公共工具：错误分类、重试、成本、缓存、配额、安全、统一服务
├── 01_error_retry.py         ← 第 1 步：错误分类、指数退避、主备模型降级
├── 02_cost_counter.py        ← 第 2 步：Token 与成本统计
├── 03_cache_quota.py         ← 第 3 步：缓存和用户配额
├── 04_prompt_injection.py    ← 第 4 步：Prompt 注入与敏感信息保护
└── 05_llm_service.py         ← 第 5 步：综合服务封装
```

---

## 前置准备

### 1. 安装依赖

推荐先进入虚拟环境，再安装：

```bash
pip install openai python-dotenv
```

如果你想更准确地统计 token，可以额外安装：

```bash
pip install tiktoken
```

### 2. 配置环境变量

把 `.env.example` 复制为 `.env`，按你当前可用的平台填写。

这一章建议优先完成两类实验：

1. 用 mock 或本地模拟方式理解错误、缓存、配额、安全链路
2. 用真实 provider 观察 usage、成本和错误返回差异

### 3. 运行方式

```bash
cd source/02_llm/06_reliability_cost_security

python 01_error_retry.py
python 02_cost_counter.py
python 03_cache_quota.py
python 04_prompt_injection.py
python 05_llm_service.py
```

---

## 第 1 步：错误分类、重试与降级（文档第 2 章）

**对应文件**：`01_error_retry.py`  
**对应文档**：第 2 章「错误处理不是异常分支，而是主链路的一部分」

### 这一步要解决什么

很多初学者会写：

```python
try:
    call_llm()
except Exception:
    pass
```

这在 AI 应用里几乎等于没有做错误处理。

你需要区分：

- 认证错误能不能重试
- 限流错误什么时候适合退避
- 超时错误要不要缩短上下文
- 主模型失败时要不要切备用模型

### 操作流程

1. 先读文档第 2 章。
2. 打开 `01_error_retry.py`，重点看：
   - `ScenarioTransport`
   - `retry_call()`
   - `fallback_demo()`
3. 运行：

```bash
python 01_error_retry.py
```

### 重点观察

- `auth_error` 为什么不应该重试
- `rate_limit_then_success` 为什么适合指数退避
- `RetryRecord` 里记录了哪些调试关键信息
- 主备模型降级的触发条件是什么

### 建议主动修改

- 把 `max_retries` 改成 1、2、4，对比结果
- 把 `base_delay` 调大，感受等待成本
- 自己增加一个 `request_error` 场景，看是否会被错误地重试

---

## 第 2 步：Token 与成本统计（文档第 3 章）

**对应文件**：`02_cost_counter.py`  
**对应文档**：第 3 章「成本控制不是财务问题，而是产品能力」

### 这一步要解决什么

很多人会说“某模型便宜”，但在工程上真正决定成本的还有：

- 历史消息长度
- 多轮对话次数
- 结构化输出约束
- `max_tokens` 上限
- 是否反复请求同样的问题

### 操作流程

1. 先读文档第 3 章。
2. 打开 `02_cost_counter.py`，重点看：
   - `estimate_messages_tokens()`
   - `compute_cost_breakdown()`
   - `session_cost_report()`
3. 运行：

```bash
python 02_cost_counter.py
```

### 重点观察

- 单条用户消息和整段会话消息的 token 差异
- 为什么没有配置价格时，也应该先把 usage 观测起来
- 教学示例价格对比里，哪一部分成本差异最大

### 建议主动修改

- 增加一轮 assistant / user 历史，再看 token 变化
- 改大 `max_tokens` 的预期输出长度，感受 completion cost 增长
- 把你的真实价格填到 `.env`，对照本地估算输出

---

## 第 3 步：缓存和配额（文档第 4 章）

**对应文件**：`03_cache_quota.py`  
**对应文档**：第 4 章「缓存、预算与配额是成本控制真正落地的地方」

### 这一步要解决什么

知道 token 和价格还不够，你还需要能：

- 避免重复请求重复付费
- 在调用前判断当前用户还能不能继续用
- 在调用后精确扣减配额

### 操作流程

1. 先读文档第 4 章。
2. 打开 `03_cache_quota.py`，重点看：
   - `TTLCache`
   - `DailyQuotaManager`
   - `cache_quota_combined_demo()`
3. 再对照 `reliability_utils.py`，继续看：
   - `TTLCache.get() / set() / size()`
   - `DailyQuotaManager.ensure_available() / consume()`
   - `stable_cache_key()`
4. 运行：

```bash
python 03_cache_quota.py
```

### 重点观察

- 为什么第二次命中缓存不应该再次扣减配额
- `ensure_available()` 和 `consume()` 为什么必须分成两个动作
- TTL 缓存只适合什么类型的问题

### 建议主动修改

- 把 `daily_limit_tokens` 改小，观察更早触发的超限
- 把 `ttl_seconds` 改成很短，模拟缓存过期
- 把缓存 key 设计得更粗或更细，思考命中率与误命中的权衡

---

## 第 4 步：Prompt 注入与敏感信息保护（文档第 5 章）

**对应文件**：`04_prompt_injection.py`  
**对应文档**：第 5 章「安全不是额外模块，而是输入链路的一部分」

### 这一步要解决什么

Prompt 注入的本质不是“模型被黑客控制了”，而是：

- 系统没有把用户数据和系统指令隔离开
- 系统没有在日志和提示词里处理敏感信息
- 系统把业务文本里出现的恶意句子误当成真实指令

### 操作流程

1. 先读文档第 5 章。
2. 打开 `04_prompt_injection.py`，重点看：
   - `detect_prompt_injection()`
   - `build_guarded_messages()`
   - `redact_sensitive()`
3. 再对照 `reliability_utils.py`，确认：
   - 风险分是如何累加的
   - 输入是如何被包裹成“待分析数据”的
   - 日志脱敏主要覆盖哪些模式
4. 运行：

```bash
python 04_prompt_injection.py
```

### 重点观察

- 风险分是怎么被计算出来的
- 为什么“把用户输入包进标签里”会比直接拼接更稳
- 日志脱敏处理了哪些敏感信息

### 建议主动修改

- 把你自己的业务文本放进去测试
- 自己增加新的注入特征词
- 故意输入手机号、邮箱、API Key 格式文本，看脱敏结果

---

## 第 5 步：统一服务封装（文档第 6 章）

**对应文件**：`05_llm_service.py`  
**对应文档**：第 6 章「把可靠性、成本和安全收束成统一服务层」

### 这一步要解决什么

前面四个脚本分别讲单点能力，第五步要把它们收束成更接近真实项目的服务层：

- 调用前先做安全检查
- 再做配额检查
- 再查缓存
- 真正调用时带重试
- 返回 usage、成本、风险信息

### 操作流程

1. 先读文档第 6 章。
2. 打开 `05_llm_service.py`，重点看：
   - `ReliableLLMService`
   - `ServiceResponse`
   - `normal_case / cached_case / risky_case`
3. 再对照 `reliability_utils.py`，重点看：
   - `run_chat()`
   - `call_openai_compatible_chat()`
   - `mock_chat_response()`
   - `ReliableLLMService.chat()`
4. 运行：

```bash
python 05_llm_service.py
```

### 重点观察

- 第二次同样的问题为什么会 `from_cache=True`
- `risky_case` 为什么不会直接抛异常，而是返回结构化风险信息
- 为什么服务层要统一返回 `usage / cost / retries / quota_snapshot`

### 建议主动修改

- 把 `block_on_injection=True` 再跑一次
- 把 `daily_limit_tokens` 调小，观察配额失败结果
- 用真实 `.env` 配置运行，看 `mocked` 是否变成 `False`

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2 章 | 错误分类、重试、退避、降级 | `01_error_retry.py`, `reliability_utils.py` |
| 第 3 章 | Token、usage、成本估算 | `02_cost_counter.py`, `reliability_utils.py` |
| 第 4 章 | 缓存、预算、用户配额 | `03_cache_quota.py`, `reliability_utils.py` |
| 第 5 章 | Prompt 注入、脱敏、输入隔离 | `04_prompt_injection.py`, `reliability_utils.py` |
| 第 6 章 | 综合服务封装 | `05_llm_service.py`, `reliability_utils.py` |

---

## 建议的学习顺序

1. 先跑 `01_error_retry.py`
2. 再跑 `02_cost_counter.py`
3. 接着跑 `03_cache_quota.py`
4. 再跑 `04_prompt_injection.py`
5. 最后跑 `05_llm_service.py`

这个顺序对应的能力递进是：

1. 先理解失败如何被分类和处理
2. 再理解调用为什么会花钱，以及如何被观测
3. 再把成本控制落实到缓存和配额
4. 然后补上基础安全防护
5. 最后把这些横切逻辑收束成一个统一服务层

---

## 你完成本章后应该达到什么程度

如果这一章学完后你已经能做到下面这些事，就说明落地是成功的：

- 看到错误时，不再只会 `except Exception`
- 能区分哪些错误该重试，哪些错误该立即失败
- 能统计 usage 和估算成本，而不是只知道“模型贵不贵”
- 能用缓存和配额控制重复支出
- 能识别基础 Prompt 注入风险，知道最小防护动作是什么
- 能把这些能力封装进一个统一服务，而不是散落在业务代码里
