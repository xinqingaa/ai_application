# 07. foundation_lab 任务拆解

> 本节目标：把 `foundation_lab` 从设计方案继续拆成可执行任务，明确实施顺序、文件职责、每个阶段的完成标准和建议节奏，让你可以直接据此开始编码，而不是继续停留在抽象层

---

## 1. 概述

### 学习目标

- 明确 `foundation_lab` 的正确实施顺序
- 明确每个阶段该写哪些文件、写到什么程度
- 明确哪些能力在 `03` 必须做，哪些必须刻意不做
- 明确每个阶段的完成标准
- 把文档理解真正转成可执行项目计划

### 预计学习时间

- 任务顺序理解：0.5 小时
- 文件级拆解：1 小时
- 阶段完成标准梳理：0.5 小时
- 节奏规划与自查：0.5 小时

### 本节在整体路径中的重要性

| 问题 | 本章解决方式 |
|------|-------------|
| 知道结构但不知道先写什么 | 按阶段拆顺序 |
| 文件很多，不知道职责 | 文件级任务清单 |
| 容易过度实现 | 明确边界和完成标准 |
| 学习节奏容易拖散 | 给出建议排期 |

> **这一章解决的核心问题不是“项目结构长什么样”，而是“怎么把这个结构真正写出来”。**

### 本章的学习边界

这一章重点解决：

1. `foundation_lab` 的实施顺序
2. 文件级职责和最小完成标准
3. 每个阶段该停在哪里
4. 一周左右有效学习量下的建议节奏

这一章不展开：

- 具体代码实现细节
- 真正依赖安装与运行问题
- 后续 `04_rag` 的实现方案

这些会在真正进代码时再处理。

### 本章与前后章节的衔接

上一章 [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md) 已经把项目定义清楚了。

这一章继续往下做：

- 把“项目设计”变成“项目任务”

它是 `03` 文档组里最贴近执行的一篇，也是在真正开始写代码前最应该反复看的文档。

### 当前状态与第一入口

当前 `foundation_lab` 仍未开始正式编码，所以这篇文档当前承担的是：

- 实施计划
- 文件清单
- 阶段完成标准

当前第一入口是：

- 本文档本身

未来正式开始编码后，这篇文档应与以下位置对应：

- `source/03_foundation/foundation_lab/README.md`
- `source/03_foundation/foundation_lab/app/`
- `source/03_foundation/foundation_lab/scripts/`
- `source/03_foundation/foundation_lab/tests/`

### 使用顺序

建议这样使用这篇文档：

1. 先对照 [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md) 确认项目边界
2. 再按本篇 `Phase 1 -> Phase 6` 顺序推进
3. 每完成一个 Phase，就回看对应完成标准
4. 全部结束后再用 `10. 最终验收` 做总检查

卡住时优先回看：

1. `2. 总任务顺序为什么这样排`
2. 当前 Phase 的目标、任务和完成标准
3. `10. 最终验收`

### 项目映射

| 文档部分 | 对应代码/文档 | 角色 | 说明 |
|----------|---------------|------|------|
| 本章全文 | 本文档 | 第一执行入口 | 当前还没代码时，先用它固定实施顺序 |
| `3-8` Phase 清单 | 未来 `foundation_lab/app/`、`scripts/`、`tests/` | 分阶段落地清单 | 明确每一步先写什么、后写什么 |
| `8. 接口与工程化收口` | 未来 `main.py`、`logger.py`、项目 README、测试目录 | 收口阶段 | 说明什么时候才补接口和 README |
| `9. 建议时间安排` | 实施节奏 | 节奏建议 | 控制项目不要拖散 |
| `10. 最终验收` | 项目 README / 自查记录 | 总验收标准 | 判断项目是否真正完成 |

---

## 2. 总任务顺序为什么这样排 📌

建议按这个顺序实施：

1. 先搭目录骨架
2. 先做原生 SDK 最小问答
3. 再做 LangChain 等价版本
4. 再补 `mock_retriever`
5. 再补 `mock_tool`
6. 再补 `service`
7. 最后补 FastAPI、日志、README、测试

这个顺序的逻辑非常重要：

- 先验证最底层模型调用
- 再验证抽象层
- 再验证知识入口和动作入口
- 最后再组织成最小项目

如果顺序反了，比如一开始就写 FastAPI 或 service，很容易在底层还没想清楚时就把结构写死。

---

## 3. Phase 1：项目骨架 📌

### 目标

- 先把项目结构搭出来
- 先明确职责，再逐步填实现

### 任务

创建以下文件和目录：

- `app/config.py`
- `app/schemas.py`
- `app/main.py`
- `app/llm/client_native.py`
- `app/llm/client_langchain.py`
- `app/prompts/qa_prompt.py`
- `app/chains/qa_chain.py`
- `app/retrievers/mock_retriever.py`
- `app/tools/mock_tools.py`
- `app/services/qa_service.py`
- `app/observability/logger.py`
- `scripts/demo_native.py`
- `scripts/demo_langchain.py`
- `scripts/compare_native_vs_lc.py`
- `tests/test_prompt_format.py`
- `tests/test_mock_retriever.py`
- `tests/test_mock_tools.py`
- `README.md`

### 为什么这一阶段先不急着实现

因为这一阶段的重点是：

- 强迫自己先想清楚每层职责

这一步做完后，你后面写代码时不会不断在项目结构上摇摆。

### 完成标准

- 目录齐全
- 文件职责明确
- 不要求功能全部实现

---

## 4. Phase 2：原生 SDK 最小能力 📌

### 目标

- 先证明你能用最底层方式跑通问答

### 任务

在 `client_native.py` 中实现：

- 一个最小普通问答调用
- 一个最小结构化输出示例
- 一个最小流式调用示例

在 `demo_native.py` 中验证：

- 输入一个问题
- 返回一段文本结果

### 为什么必须先做这一步

因为如果你连原生 SDK 的最小调用都没有完全想清楚，后面很容易把 LangChain 当成“神秘黑盒”。

这一阶段的学习收益是：

- 明白“不用框架时自己到底要写哪些胶水代码”

### 完成标准

- 模型能稳定返回文本
- 你能清楚说出：
  - 输入怎么组织
  - 输出怎么取值
  - 流式怎么处理

---

## 5. Phase 3：LangChain 等价版本 📌

### 目标

- 用 LangChain 重写同类能力

### 任务

在 `qa_prompt.py` 中定义最小 Prompt  
在 `qa_chain.py` 中实现：

- `prompt -> llm -> parser`

在 `client_langchain.py` 中封装：

- LangChain 模型初始化
- `invoke`
- `stream`

在 `demo_langchain.py` 中验证：

- 能得到和原生 SDK 类似的功能结果

### 这一阶段真正要比较什么

重点不是“谁更短”，而是：

- 原生 SDK 更透明在哪里
- LangChain 更可组合在哪里

### 完成标准

- 最小链能跑通
- 你能明确说明 LangChain 替你抽象了什么

---

## 6. Phase 4：检索与工具边界验证 📌

### 目标

- 明确 `Retriever` 和 `Tool` 的本质区别

### 任务

在 `mock_retriever.py` 中实现：

- 预置几条固定文档
- 按简单关键词或规则返回相关文档

在 `mock_tools.py` 中实现至少一个工具：

- 计算器
- 当前时间
- 模拟规则查询

### 为什么这一阶段很重要

因为这是后面 `04_rag` 和 `05_agent` 分岔的起点。

你在这里必须形成清楚认知：

- `Retriever` 返回的是文档
- `Tool` 返回的是动作结果

### 完成标准

- `mock_retriever` 能返回预期文档
- `mock_tool` 能返回预期结果
- 你能明确说明两者边界

---

## 7. Phase 5：业务编排层 📌

### 目标

- 用 `service` 层统一组织不同路径

### 任务

在 `qa_service.py` 中实现：

- 普通问答入口
- 检索问答入口
- 工具辅助问答入口
- 一个最小路径判断逻辑

建议先使用：

- 手工规则
- 简单关键词判断

不要在 `03` 阶段做：

- 自动多步决策
- 复杂工具选择
- 真正 Agent 循环

### 为什么这一层是关键

因为它是你从“示例代码”走向“项目结构”的真正分界线。

如果没有 service 层，后面 API 会越来越重，结构会很快失控。

### 完成标准

- API 层不直接堆业务判断
- 三条路径都有统一入口
- 你能看出后续扩展点在哪里

### 这一阶段最应该讲清楚的执行流

很多人在这一阶段最大的误区不是“不会写代码”，而是：

- 不清楚问题进入项目后应该先到哪一层

正确的最小执行流应该先固定成：

```plain
question
  -> service.ask()
  -> 路径判断
  -> plain / retrieval / tool
  -> chain.invoke(...)
  -> answer
```

如果当前是 `retrieval` 路径，应进一步展开成：

```plain
question
  -> service.ask()
  -> retriever.retrieve(question)
  -> docs
  -> chain.invoke(question, context_blocks=...)
  -> answer
```

如果当前是 `tool` 路径，应进一步展开成：

```plain
question
  -> service.ask()
  -> select_tool(question)
  -> run_tool(...)
  -> tool result
  -> chain.invoke(question, tool_result=...)
  -> answer
```

这部分如果文档不先写清楚，后面非常容易在 API 层直接开始拼 Prompt、调工具、调 retriever，最后把整个结构写散。

---

## 8. Phase 6：接口与工程化收口 📌

### 目标

- 让项目真正能独立运行和演示

### 任务

在 `main.py` 中提供：

- `POST /ask`
- `POST /ask/stream`

在 `logger.py` 中提供：

- 基础 logger 初始化

在测试中覆盖：

- Prompt 基础格式
- `mock_retriever`
- `mock_tool`

在项目 `README.md` 中写清楚：

- 项目定位
- 目录结构
- 运行方式
- 原生 SDK 与 LangChain 的区别

### 这一阶段最应该讲清楚的 API 流

这一阶段不要只写“有两个接口”，还要把接口怎么流到 service 说清楚。

`POST /ask` 的最小流转应该是：

```plain
HTTP request
  -> main.py route
  -> 提取 question / engine
  -> service.ask(...)
  -> AskResponse
  -> HTTP response
```

`POST /ask/stream` 的最小流转应该是：

```plain
HTTP request
  -> main.py route
  -> 提取 question / engine
  -> service.stream(...)
  -> iterator
  -> StreamingResponse
```

这里最重要的不是接口数量，而是职责边界：

- `main.py` 负责接入和返回
- `qa_service.py` 负责业务组织
- `qa_chain.py` 负责 `prompt -> llm -> parser`

如果你写完接口后还不能用语言把这三层关系解释清楚，说明这一步还没有真正完成。

### 为什么这一步放最后

因为它本质上是收口，不是起点。

如果前面抽象和路径没有跑通，这一步只是把混乱结构包成一个接口而已。

### 完成标准

- 本地可运行
- 结构清晰
- 可独立讲解

卡住时先回看：

1. `Phase 2-5` 是否已经真正跑通主线能力
2. 项目 README 是否已经写清运行方式和目录职责
3. `10. 最终验收` 的五项要求是否已经全部具备

---

## 9. 建议时间安排 📌

建议控制在 `5-7` 天有效学习量。

### 第 1 天

- 搭目录
- 写原理判断笔记

### 第 2 天

- 原生 SDK 最小问答

### 第 3 天

- LangChain 重写
- 跑通 LCEL

### 第 4 天

- `mock_retriever`
- `mock_tool`

### 第 5 天

- `qa_service`
- FastAPI 接口

### 第 6 天

- 日志
- 测试
- README

### 第 7 天

- 复盘
- 整理问题
- 准备进入 `04_rag`

### 如果进度慢怎么办

优先级建议是：

1. 先保留骨架
2. 再保留原生 SDK 与 LangChain 对照
3. 再保留 `mock_retriever` / `mock_tool`
4. 最后再补 API 和测试

不要因为想一步到位，导致整个阶段拖得过长。

---

## 10. 最终验收 📌

到这一阶段结束时，你应该能做到：

1. 清楚解释 `Model / Prompt / Parser / Runnable / Retriever / Tool / Service`
2. 清楚解释原生 SDK 和 LangChain 的差别
3. 有一个最小但独立的 `foundation_lab`
4. 能把这个骨架迁移到 `04_rag`，而不是从零重新组织工程结构
5. 能明确说出当前阶段故意没有做什么，以及为什么没有做

这才说明 `03_foundation` 真正完成了“过渡阶段”的价值。

## 11. 文档完成标准

### 理解层

- 能解释为什么任务顺序必须是“骨架 -> 原生 SDK -> LangChain -> mock -> service -> 收口”
- 能解释每个 Phase 负责验证什么能力

### 操作层

- 能按本篇 Phase 顺序组织后续编码
- 能在每个阶段结束时用完成标准做自查
- 卡住时知道该回看设计文档还是当前 Phase

### 代码准备层

- 能明确未来要创建哪些核心文件
- 能明确哪些能力属于当前阶段必须做，哪些必须刻意不做
- 能明确 README、API、日志、测试应该在什么时候补

### 映射层

- 能说清本篇与 `06_foundation_lab_design.md` 的关系
- 能说清每个 Phase 会落到未来哪个目录和文件集合
- 能说清本篇是未来 `foundation_lab` 开发时的主要执行文档
