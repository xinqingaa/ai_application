# Agent 与 LangGraph 学习大纲

> 目标：系统掌握 Agent 架构、工具调用、LangChain / LangGraph 编排、多步骤任务执行与企业级工程实践

---

## 课程定位

- 本课程是 **LangChain / LangGraph 的系统主战场**。
- 如果说 `RAG` 课程解决的是“固定检索链路怎么做稳”，那么本课程解决的是“什么时候需要动态决策、如何让系统会判断、会调用、会协作”。
- 你会在本课程里真正系统掌握：
  - LangChain 的 `Tool / Agent / Memory` 等抽象
  - LangGraph 的 `State / Node / Edge / Checkpoint / Interrupt`
  - Agentic RAG、Multi-Agent、可观测性、安全与成本控制

## 学习前提

- 已完成 [02_llm/outline.md](/Users/linruiqiang/work/ai_application/docs/02_llm/outline.md)
- 建议先完成 [03_foundation/outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md)
- 建议先完成 [04_rag/outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)

## 与前后课程的衔接

### 与 02_llm 的关系

- `02_llm` 解决的是：如何调用模型、设计消息、做结构化输出、控制流式输出、错误处理与成本。
- 本课程默认这些能力已经具备，因为 `Function Calling / Tool Schema / Guardrails / Eval` 都建立在这些基本功之上。
- 可以把这门课理解成：从“模型会回答”升级到“系统会决策、会调用、会协作”。

### 与 03_foundation 的关系

- `03_foundation` 提供的是 LangChain 核心抽象和组件组合思维。
- 本课程不再重复解释 `Runnable / Tool / Chain` 这些对象为什么这样设计，而是直接把它们放进 Agent 和 LangGraph 编排里。
- 也就是说，这门课不是单纯学 API，而是在承接前面抽象之后进入“复杂系统编排”。

### 与 04_rag 的关系

- `04_rag` 解决的是固定检索链路怎么做稳。
- 本课程承接这个结果，把检索从“固定步骤”升级成“可被 Agent 动态选择和调度的能力”。
- 如果前面的传统 RAG 还没做稳，就很容易在 Agent 课程里把“检索问题”和“编排问题”混在一起。

### 与 06_application 的关系

- 后面的 [06_application/outline.md](/Users/lrq/work/ai_application/docs/06_application/outline.md) 会直接把这里的能力落成业务工作流，而不会回头系统补 Agent 原理。
- 本课程产出的关键能力，会在项目实战里落到：路由决策、知识源选择、人工审批、风控节点、状态持久化、多角色协作。
- 所以后面的项目课重点是业务闭环，这门课重点是先把“动态系统能力”学清楚。

### 本课程的边界

- 本课程重点是 **动态决策、工具调用、状态编排、记忆、安全与评测**。
- 它不是通用工作流平台开发课，也不是完整企业中台设计课。
- 具体业务拆分、前后端整合、权限审计落地、真实商业流程设计，放到 [06_application/outline.md](/Users/lrq/work/ai_application/docs/06_application/outline.md)。

## 本课程回答什么问题

- 如何从 `Chain / Workflow / Agent / Multi-Agent` 里做架构选型，而不是一上来就上最复杂方案？
- 什么情况下应该用 Agent，而不是普通 Chain 或 RAG？
- 如何把工具调用从“一个 demo”做成稳定循环？
- 为什么 LangGraph 比单纯 AgentExecutor 更适合复杂业务？
- 怎样把 RAG 升级成 Agentic RAG？
- 如何从第一天就建立 agent eval，持续做回归测试，而不是最后靠手测？
- 如何做上下文工程（Context Engineering），而不是只靠一段 system prompt 硬撑？
- 怎样把 Agent 做到可观测、可调试、可控、可上线？

## 开始前：先建立最小 Agent 评估集 📌

### 1. Agent 评估与测试前置

#### 本节与前后课程的关系

- 承接 `02_llm` 里的结构化输出、错误处理、成本意识，把它们升级成 Agent 场景下的“轨迹评估”和“回归测试”。
- 承接 `04_rag` 里已经建立的 golden set 思维，但这里评估的不只是答案，还包括工具轨迹、路由和安全动作。
- 服务 `06_application`：后面的业务工作流一旦变复杂，没有这套评估思维就很难稳定迭代。
- 边界：这里建立最小可用评估方法，不展开完整线上监控平台或企业级发布体系。

#### 知识点

1. **为什么 Agent 更需要前置评估**
   - Agent 是动态系统，结果不只取决于最终答案，还取决于中间决策
   - 只靠手工试几条问题，很容易漏掉循环、乱调工具、越权调用这些问题
   - 评估集越早建立，后续重构图结构越安心

2. **最小 Agent Golden Set 怎么建**
   - 每条样本至少包含：`input / expected_outcome / allowed_tools / forbidden_tools`
   - 对敏感任务额外标记：是否必须确认、是否必须拒答、是否必须人工接管
   - 加入无工具回答、单工具、多工具、失败重试、拒答这几类样本

3. **评什么**
   - 最终答案是否正确
   - 工具轨迹是否合理
   - 是否调用了不该调用的工具
   - 成本、时延、迭代次数是否在预算内
   - 安全样本是否正确拒绝或触发审批

4. **什么时候回归**
   - 改 Prompt / Tool 描述时
   - 改 Graph 节点和路由时
   - 换模型时
   - 加新工具、新权限、新 guardrail 时

#### 实践练习

```python
# 1. 建一个最小 Agent golden set
golden_cases = [
    {
        "input": "北京今天天气怎么样？",
        "expected_outcome": "use_tool:get_weather",
        "allowed_tools": ["get_weather"],
        "forbidden_tools": ["delete_file"],
    },
    {
        "input": "删除 /tmp/test.txt",
        "expected_outcome": "require_human_confirmation",
        "allowed_tools": ["delete_file"],
        "forbidden_tools": [],
    },
]

# 2. 定义回归门槛
eval_policy = {
    "max_iterations": 8,
    "max_latency_ms": 5000,
    "max_tool_calls": 3,
}

# 3. 后续每次改 graph / tool / prompt，都跑这套数据
```

## 一、Agent 基础概念

### 2. 什么是 Agent

#### 知识点

1. **Agent 定义**
   - 能够自主决策和执行任务的 AI 系统
   - 感知 → 思考 → 行动 → 反思
   - 与普通 LLM 调用的区别

2. **Agent 核心组件**
   ```
   ┌─────────────────────────────────────┐
   │              Agent                   │
   │  ┌─────────┐  ┌─────────┐  ┌──────┐│
   │  │   LLM   │←→│ Tools   │←→│Memory││
   │  │ (大脑)  │  │ (工具)  │  │(记忆)││
   │  └─────────┘  └─────────┘  └──────┘│
   │        ↓                            │
   │  ┌─────────────────┐                │
   │  │ Planning (规划) │                │
   │  └─────────────────┘                │
   └─────────────────────────────────────┘
   ```

3. **Agent vs Chain**
   - Chain：固定流程，predetermined
   - Agent：动态决策，autonomous

4. **应用场景**
   - 自主任务执行
   - 多工具协作
   - 复杂问题分解
   - 自动化工作流

#### 实践练习

```python
# 1. 理解 Agent 循环
# 画出 Agent 的执行流程图：
# 用户输入 → LLM 决策 → 工具调用 → 观察结果 → 继续决策 or 返回答案

# 2. 场景判断
# 以下场景适合 Chain 还是 Agent？
# - 翻译文档（固定流程）
# - 搜索并总结最新新闻（需要决策）
# - 根据问题选择数据库查询（需要决策）
# - 格式化输出 JSON（固定流程）

# 3. 设计一个简单 Agent
# 目标：计算 "北京到上海的距离，并换算成公里"
# 需要什么工具？决策流程是什么？
```

---

### 综合案例：Agent 需求分析

```python
# 为以下场景设计 Agent 方案
#
# 场景1：智能客服
# - 需要查询订单、物流、退换货
# - 需要调用多个内部系统
# - 需要根据用户意图选择操作
#
# 场景2：数据分析助手
# - 需要查询数据库
# - 需要生成图表
# - 需要根据问题选择分析方法
#
# 设计要求：
# 1. 列出需要的工具
# 2. 设计决策流程
# 3. 考虑异常情况处理
# 4. 画出状态转换图
```

---

### 3. Agent 架构选型：Chain / Workflow / Agent / Multi-Agent 📌

#### 本节与前后课程的关系

- 这一节是整个 Agent 课程的决策总入口，作用类似于 `04_rag` 里的架构选型章。
- 它承接 `02_llm` 的“单次调用能力”、`03_foundation` 的“组件组合能力”、`04_rag` 的“固定链路能力”，帮助你判断何时真的需要 Agent。
- 到 `06_application` 里，你会面对真实业务拆分，这一节的价值就是避免把所有模块都误做成 Multi-Agent。
- 边界：这里先讲判断框架，不直接进入某一类 Agent 的细节实现。

#### 知识点

1. **四种常见架构**
   - Chain：固定输入输出，步骤少，最稳定
   - Workflow：有条件分支和状态流转，但决策空间可控
   - Agent：模型动态选择工具和下一步动作
   - Multi-Agent：多个角色协作，适合天然分工明显的复杂任务

2. **默认决策顺序**
   - 能用 Chain 解决，不上 Agent
   - 需要条件分支和审批流，优先 Workflow / LangGraph
   - 需要动态选工具、改计划、补检索时，再上 Agent
   - 单 Agent 已经失控且角色天然不同，再考虑 Multi-Agent

3. **选型维度**
   - 任务是否稳定、是否高频
   - 是否需要动态决策
   - 是否存在敏感操作
   - 是否有明显的角色分工
   - 团队是否有能力调试和维护复杂图

4. **常见误区**
   - 把所有自动化问题都包装成 Agent
   - 需要审批流的场景不用 Workflow，硬交给 Agent 自主决定
   - 单 Agent 都没跑稳，就急着拆成多 Agent

#### 实践练习

```python
# 判断以下场景更适合：
# Chain / Workflow / Agent / Multi-Agent
#
# 1. JSON 字段抽取
# 2. 客服工单路由 + 人工审批
# 3. 搜索、比较、总结最新资料
# 4. 研究员 + 分析师 + 审稿人 协作写报告
```

---

## 二、Function Calling

### 4. Function Calling 基础

#### 知识点

1. **什么是 Function Calling**
   - LLM 输出结构化的函数调用
   - 模型决定调用哪个函数、传什么参数
   - 执行结果返回给模型继续处理

2. **工作流程**
   ```
   1. 定义工具函数和 Schema
   2. 用户提问
   3. LLM 决定是否调用工具
   4. 执行工具
   5. 将结果返回 LLM
   6. LLM 生成最终回答
   ```

3. **OpenAI Function Calling**
   - tools 参数
   - function 定义格式
   - tool_choice 选项

#### 实战案例

```python
from openai import OpenAI
import json

client = OpenAI()

# 1. 定义工具函数
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 2. 发送请求
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=tools
)

# 3. 处理工具调用
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        # 执行函数...
```

---

### 5. 实现完整的工具调用循环

#### 知识点

1. **完整循环**
   - 检测工具调用
   - 执行工具
   - 构建工具响应消息
   - 继续对话

2. **多轮工具调用**
   - 一次调用多个工具
   - 依赖调用（A 的结果作为 B 的输入）

3. **错误处理**
   - 工具执行失败
   - 参数解析失败
   - 无限循环防护

#### 实战案例

```python
import json

# 1. 实现工具执行器
def execute_function(name: str, args: dict) -> str:
    """根据函数名执行对应函数"""
    if name == "get_weather":
        return get_weather(args["city"])
    elif name == "calculate":
        return str(eval(args["expression"]))
    # ... 其他工具

# 2. 完整的 Agent 循环
def run_agent(user_input: str, tools: list, max_iterations: int = 10):
    messages = [{"role": "user", "content": user_input}]

    for i in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            # 没有工具调用，返回最终答案
            return message.content

        # 执行工具调用
        for tool_call in message.tool_calls:
            result = execute_function(
                tool_call.function.name,
                json.loads(tool_call.function.arguments)
            )
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "达到最大迭代次数"

# 3. 测试多工具调用
# "北京和上海今天的天气对比"
```

---

### 6. Claude Tool Use

#### 知识点

1. **Claude Tool Use 特点**
   - 与 OpenAI 类似但格式不同
   - tool_result 格式
   - 支持图片输入

2. **工具定义格式**
   ```python
   tools = [{
       "name": "get_weather",
       "description": "获取天气",
       "input_schema": {
           "type": "object",
           "properties": {...}
       }
   }]
   ```

3. **与 OpenAI 的差异对比**

#### 实战案例

```python
import anthropic

client = anthropic.Anthropic()

# 1. Claude Tool Use 基础调用
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[...],
    messages=[{"role": "user", "content": "北京天气"}]
)

# 2. 处理 tool_use
for block in response.content:
    if block.type == "tool_use":
        # 执行工具
        pass

# 3. 返回 tool_result
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[...],
    messages=[
        {"role": "user", "content": "北京天气"},
        {"role": "assistant", "content": [...tool_use blocks...]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "...", "content": "..."}
        ]}
    ]
)
```

---

### 7. MCP（Model Context Protocol）📌

#### 本节与前后课程的关系

- 前面的 `Function Calling` 解决的是“应用内部如何让模型调工具”，这一节进一步扩展到“能力如何以标准协议暴露和复用”。
- 它承接 `02_llm` 的工具调用认知，也承接 `03_foundation` 里对接口抽象和组件边界的理解。
- 对 `06_application` 来说，MCP 的价值主要在于未来接入更多外部能力或跨工作台复用工具，而不是项目第一天就必须重投入。
- 边界：本课程重点是理解协议角色和接入方式，不展开成完整的插件市场或平台生态设计课。

#### 知识点

1. **什么是 MCP**
   - Anthropic 主导的标准化协议
   - 定义 LLM 如何连接外部工具和数据源
   - 类比：Function Calling 是"直接调函数"，MCP 是"REST API 标准"

2. **与 Function Calling 的区别**

| 维度 | Function Calling | MCP |
|------|-----------------|-----|
| 定义方 | 各模型厂商各自定义 | 统一标准协议 |
| 工具发现 | 手动注册工具列表 | Server 自动暴露能力 |
| 互操作性 | 低（各平台格式不同） | 高（标准化协议） |
| 生态 | 需自行封装 | Cursor、Claude Desktop 等已原生支持 |
| 适用场景 | 应用内部工具调用 | 跨应用/跨平台工具共享 |

3. **核心架构**
   ```
   MCP Host（如 Cursor、Claude Desktop）
     ├── MCP Client（协议客户端）
     │     ├── MCP Server A（文件系统工具）
     │     ├── MCP Server B（数据库工具）
     │     └── MCP Server C（自定义 API 工具）
     └── LLM（决策调用哪个 Server 的哪个工具）
   ```

4. **MCP 核心能力对象**
   - Tools：执行动作，例如搜索、查天气、执行 SQL
   - Resources：暴露只读数据，例如文档、配置、知识条目
   - Prompts：暴露可复用提示模板或工作模式

5. **MCP Server 开发**
   - 使用 Python SDK（`mcp` 库）
   - 将 Tools、Resources、Prompts 组织为一个标准化能力接口
   - 传输方式：stdio / SSE

#### 实战案例

```python
# 1. 使用现有 MCP Server
# 安装并配置一个社区 MCP Server（如文件系统、GitHub）
# 在 Claude Desktop 或 Cursor 中体验

# 2. 编写简单的 MCP Tool
from mcp.server import Server
from mcp.types import Tool

server = Server("my-tools")

@server.tool()
async def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}今天晴，25°C"

@server.tool()
async def calculate(expression: str) -> str:
    """计算数学表达式"""
    return str(eval(expression))

# 3. 设计一个 MCP Resource
# 例如：把产品手册、FAQ、配置项暴露为只读资源
# 让 Host 能按 URI 读取，而不是每次都包装成工具调用
#
# 4. 设计一个 MCP Prompt
# 例如：暴露“代码审查模式”“客服回复模式”这类可复用提示模板
#
# 5. 对比 Function Calling vs MCP
# 同一个工具（天气查询），分别用两种方式实现
# 体会“应用内部调用”与“标准化能力暴露”的差异

# 6. MCP 与 LangChain / LangGraph 集成
# 探索如何把 MCP Server 暴露的能力映射到 Agent 可消费的工具或资源
```

---

### 综合案例：统一工具调用框架

```python
# 实现一个统一的多模型工具调用框架
#
# 功能要求：
# 1. 支持 OpenAI 和 Claude 的工具调用
# 2. 统一的工具定义格式
# 3. 自动处理模型差异
# 4. 完整的调用循环
# 5. 错误处理和重试
# 6. 可选：支持 MCP Server 作为工具来源
#
# 使用示例：
# framework = UnifiedToolFramework(provider="openai")
#
# # 注册工具
# @framework.tool
# def get_weather(city: str) -> str:
#     """获取城市天气"""
#     return f"{city}今天晴，25°C"
#
# # 执行
# result = framework.run("北京天气怎么样？")
# print(result)
#
# # 切换模型
# framework.switch_provider("claude")
# result = framework.run("上海天气呢？")
#
# 技术要点：
# - 适配器模式
# - 工具注册机制
# - 消息格式转换
# - 循环控制
#
# 扩展方向：
# - 添加更多模型支持
# - 添加工具执行日志
# - 添加并发工具调用
```

---

## 三、LangChain / LangGraph Agent

### 8. LangChain Tools

#### 知识点

1. **Tool 定义方式**
   - @tool 装饰器
   - StructuredTool
   - 从函数自动创建

2. **Tool 属性**
   - name：工具名称
   - description：描述（LLM 用来决策）
   - args_schema：参数 Schema

3. **内置工具**
   - DuckDuckGoSearchRun
   - PythonREPLTool
   - RequestsTool

#### 实战案例

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# 1. 使用 @tool 装饰器
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    # 模拟实现
    return f"{city}今天晴，温度25°C"

# 2. 带详细 Schema 的工具
class CalculatorInput(BaseModel):
    a: float = Field(description="第一个数字")
    b: float = Field(description="第二个数字")
    operation: str = Field(description="运算符：add/sub/mul/div")

@tool("calculator", args_schema=CalculatorInput)
def calculator(a: float, b: float, operation: str) -> float:
    """执行基本数学运算"""
    if operation == "add":
        return a + b
    elif operation == "sub":
        return a - b
    # ...

# 3. 使用内置工具
from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()
result = search.invoke("今天的新闻")

# 4. 创建工具列表
tools = [get_weather, calculator, search]
```

---

### 9. LangChain Agent 构建

#### 知识点

1. **Agent 类型**
   - OpenAI Tools Agent（推荐）
   - ReAct Agent
   - Structured Chat Agent

2. **Agent 构建流程**
   ```
   LLM + Tools + Prompt → Agent
   Agent + Memory → AgentExecutor
   ```

3. **AgentExecutor**
   - 执行 Agent
   - 管理迭代
   - 错误处理

#### 实战案例

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 1. 创建 LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# 2. 定义 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的助手，可以使用工具来回答问题。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 3. 创建 Agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 4. 创建 AgentExecutor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. 执行
result = agent_executor.invoke({"input": "北京天气如何？"})
print(result["output"])

# 6. 带记忆的 Agent
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(memory_key="chat_history")
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)
```

---

### 10. LangGraph 基础

#### 知识点

1. **为什么需要 LangGraph**
   - 更灵活的状态管理
   - 循环和条件分支
   - 可视化工作流

2. **核心概念**
   - State：状态
   - Node：节点（处理逻辑）
   - Edge：边（流转条件）
   - Graph：图（整体结构）

3. **基本结构**
   ```
   START → Node A → Condition → Node B → END
                       ↓
                     Node C
   ```

#### 实践练习

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 1. 定义状态
class AgentState(TypedDict):
    messages: list
    next_action: str

# 2. 定义节点函数
def agent_node(state: AgentState) -> AgentState:
    # LLM 决策
    pass

def tool_node(state: AgentState) -> AgentState:
    # 执行工具
    pass

# 3. 构建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 设置入口
workflow.set_entry_point("agent")

# 添加边
workflow.add_conditional_edges(
    "agent",
    lambda state: "tools" if state["next_action"] == "tool" else END,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent")

# 4. 编译和执行
app = workflow.compile()
result = app.invoke({"messages": ["你好"]})
```

---

### 11. LangGraph Agent 实战

#### 知识点

1. **完整 Agent 图**
   - Agent 节点
   - Tool 节点
   - 条件路由

2. **状态管理**
   - 消息历史
   - 工具调用记录
   - 中间结果

3. **调试和可视化**
   - 流程追踪
   - 状态检查点

#### 实战案例

```python
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState

# 1. 使用预构建的 ToolNode
tool_node = ToolNode(tools)

# 2. 定义 Agent 节点
def agent_node(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 3. 构建完整 Agent
workflow = StateGraph(MessagesState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# 4. 执行
app = workflow.compile()
result = app.invoke({"messages": [("user", "北京天气")]})

# 5. 流式输出
async for event in app.astream_events({"messages": [("user", "搜索新闻")]}, version="v2"):
    print(event)

# 6. Human-in-the-loop（人机协作）📌
# 在关键操作前暂停，等待人类确认
from langgraph.types import interrupt

def sensitive_action(state: MessagesState):
    """执行敏感操作前，请求人类确认"""
    approval = interrupt({
        "action": "delete_file",
        "message": "确认要删除文件吗？"
    })
    if approval == "yes":
        # 执行操作
        pass
    else:
        return {"messages": ["操作已取消"]}

# 适用场景：
# - 数据库写操作
# - 文件删除
# - 发送邮件/消息
# - 任何不可逆操作
```

---

### 12. Agentic RAG 📌

#### 本节与前后课程的关系

- 这节直接承接 [04_rag/outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 的传统 RAG 主线，是两门课最明确的交叉点。
- 前一门课已经说明什么时候值得升级，这一节开始真正把检索纳入 Agent 决策图中。
- 对 `06_application` 来说，它会服务那些需要“先判断、再检索、再审核”的复杂业务链路，而不是替代所有普通问答。
- 边界：重点是理解固定 RAG 与动态 RAG 的工程差异，而不是鼓励在所有场景里默认上 Agent。

#### 知识点

1. **为什么 Agentic RAG 放在 Agent 课程里系统讲**
   - 它的核心不是“检索”，而是“动态决策”
   - 关键难点在于状态机、条件路由、重试与评估闭环
   - 这些都更属于 LangGraph / Agent 编排问题

2. **典型决策节点**
   - 是否需要检索
   - 使用哪一种检索策略
   - 当前检索结果是否足够
   - 是否要改写查询、拆分子问题、补充检索
   - 是否进入最终生成

3. **典型图结构**
   ```
   用户问题
      ↓
   判断节点
    ├── 直接回答
    └── 检索节点 → 评估节点
                  ├── 继续生成
                  ├── 查询改写后重检索
                  └── 子问题拆分后并行检索
   ```

4. **与传统 RAG 的工程差异**
   - 传统 RAG：固定流水线，稳定、简单、便于评估
   - Agentic RAG：更灵活，但成本更高、调试更复杂
   - 企业中通常先做好传统 RAG，再升级 Agentic RAG

#### 实战案例

```python
# 1. 用 LangGraph 实现 Agentic RAG
# 节点：router / retrieve / evaluate / rewrite_query / answer

# 2. 将 retriever 包装成 Tool
# 让 Agent 按需选择不同知识源

# 3. 对比：
# 固定 RAG Pipeline vs Agentic RAG
# 从效果、复杂度、成本、可控性四个维度评估
```

---

### 13. Context Engineering（上下文工程）📌

#### 本节与前后课程的关系

- 它承接 `02_llm` 里的消息管理、上下文窗口、结构化输出，也承接 `03_foundation` 的 Prompt / Runnable 组合思路。
- 前面的章节已经让系统“能调用工具”，这一节解决的是“给模型什么上下文，系统才会稳定”。
- 到 `06_application` 中，长流程、多角色、带审核的业务系统都高度依赖这里的上下文管理能力。
- 边界：这里聚焦 AI 系统内部的上下文装配，不展开完整产品层的用户画像或 CRM 设计。

#### 知识点

1. **为什么 Context Engineering 不是“多写几句 Prompt”**
   - Agent 的稳定性，很多时候取决于给了什么上下文，而不是模型本身
   - 需要管理的不只是 system prompt，还包括消息历史、检索结果、工具结果、状态摘要、长期记忆

2. **上下文分层**
   - 系统级约束：角色、规则、权限边界
   - 任务级上下文：当前目标、输出格式、成功条件
   - 工作记忆：本轮任务的中间结果、计划、临时状态
   - 长期记忆：跨轮偏好、用户资料、历史事实
   - 外部上下文：检索结果、数据库记录、工具返回

3. **核心技术**
   - 动态上下文裁剪
   - 历史摘要与状态压缩
   - 只在需要时注入工具、提示词和知识源
   - 按步骤选择不同模型
   - 控制上下文预算，避免噪声污染推理

4. **常见设计模式**
   - 把“全部历史消息”改成“摘要 + 最近几轮”
   - 把“所有工具都暴露”改成“按任务注入工具”
   - 把“一个统一 prompt”改成“节点级 prompt”
   - 把“长期记忆直接拼接”改成“先检索再注入”

#### 实战案例

```python
# 1. 设计一个 Context Manager
# 输入：当前任务、最近消息、长期记忆、工具列表
# 输出：本轮真正送给模型的上下文

# 2. 对比三种策略
# - 全量历史直接拼接
# - 摘要 + 最近消息
# - 摘要 + 最近消息 + 按需检索长期记忆

# 3. 为同一个 LangGraph Agent 设计：
# - planner 节点 prompt
# - tool 节点上下文
# - final answer 节点 prompt
```

---

### 综合案例：LangGraph 智能助手

```python
# 使用 LangGraph 实现一个智能助手
#
# 功能要求：
# 1. 支持多工具（搜索、天气、计算器）
# 2. 支持多轮对话
# 3. 流式输出
# 4. 状态持久化
#
# 使用示例：
# assistant = LangGraphAssistant(
#     tools=[search, weather, calculator],
#     model="gpt-4o-mini"
# )
#
# # 普通对话
# response = assistant.chat("你好")
#
# # 工具调用
# response = assistant.chat("北京天气怎么样？")
#
# # 多轮对话
# assistant.chat("那上海呢？")  # 保持上下文
#
# # 流式输出
# for chunk in assistant.chat_stream("搜索今天的新闻"):
#     print(chunk, end="")
#
# 技术要点：
# - LangGraph 状态机
# - Tool 节点集成
# - 消息历史管理
# - Context Manager
# - 流式输出处理
#
# 扩展方向：
# - 添加更多工具
# - 添加记忆持久化
# - 添加人机协作节点
```

---

## 四、Agent 设计模式

### 14. ReAct 模式

#### 知识点

1. **ReAct 原理**
   - Reasoning + Acting
   - 思考 → 行动 → 观察 → 思考...

2. **ReAct 流程**
   ```
   Question: 用户问题
   Thought: 我应该...
   Action: 工具名称
   Action Input: 工具参数
   Observation: 工具结果
   Thought: 根据结果，我需要...
   ... (循环)
   Final Answer: 最终答案
   ```

3. **适用场景**
   - 需要多步推理
   - 需要外部信息
   - 复杂问题分解

#### 实战案例

```python
# 1. 手动实现 ReAct Prompt
react_prompt = """
回答问题时，按以下格式思考：

Question: 用户的问题
Thought: 你应该思考什么
Action: 工具名称 [search, calculator, none]
Action Input: 工具的输入
Observation: 工具的输出
... (重复 Thought/Action/Observation)
Thought: 我现在知道答案了
Final Answer: 最终答案

开始！

Question: {question}
"""

# 2. 使用 LangChain ReAct Agent
from langchain.agents import create_react_agent

agent = create_react_agent(llm, tools, prompt)

# 3. 分析 ReAct 执行过程
# 观察 verbose=True 时的输出
```

---

### 15. Plan-and-Execute 模式

#### 知识点

1. **模式原理**
   - 先规划，后执行
   - 分离规划和执行阶段

2. **流程**
   ```
   用户问题 → Planner → 计划列表
               ↓
           Executor → 逐个执行
               ↓
           Re-planner → 修改计划（如需要）
               ↓
            最终答案
   ```

3. **适用场景**
   - 复杂多步骤任务
   - 需要全局规划
   - 任务有依赖关系

#### 实战案例

```python
from langchain_experimental.plan_and_execute import (
    PlanAndExecute,
    load_agent_executor,
    load_chat_planner
)

# 1. 创建 Planner
planner = load_chat_planner(llm)

# 2. 创建 Executor
executor = load_agent_executor(llm, tools, verbose=True)

# 3. 组合 Plan-and-Execute
agent = PlanAndExecute(planner=planner, executor=executor)

# 4. 执行复杂任务
result = agent.invoke("帮我规划一次日本旅行，包括机票、酒店和景点")

# 5. 用 LangGraph 实现类似逻辑
# Planner 节点 → Executor 节点 → Re-planner 节点
```

---

### 16. Multi-Agent 协作

#### 知识点

1. **多 Agent 模式**
   - 主管-员工模式（Supervisor）
   - 对等协作模式
   - 层级模式

2. **角色分工**
   - 研究员：搜集信息
   - 分析师：分析数据
   - 作者：撰写报告
   - 审核员：质量检查

3. **协作机制**
   - 消息传递
   - 共享状态
   - 任务分配

#### 实战案例

```python
from langgraph.graph import StateGraph

# 1. 定义共享状态
class TeamState(TypedDict):
    messages: list
    next_agent: str
    research_result: str
    analysis_result: str
    final_report: str

# 2. 定义不同角色的 Agent
def researcher(state: TeamState):
    # 搜集信息
    pass

def analyst(state: TeamState):
    # 分析数据
    pass

def writer(state: TeamState):
    # 撰写报告
    pass

def supervisor(state: TeamState):
    # 分配任务
    pass

# 3. 构建多 Agent 图
workflow = StateGraph(TeamState)
workflow.add_node("supervisor", supervisor)
workflow.add_node("researcher", researcher)
workflow.add_node("analyst", analyst)
workflow.add_node("writer", writer)

# 4. 定义路由
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_agent"],
    {
        "researcher": "researcher",
        "analyst": "analyst",
        "writer": "writer",
        END: END
    }
)

# 5. 执行团队任务
app = workflow.compile()
result = app.invoke({"messages": ["分析特斯拉股票"]})
```

---

### 综合案例：多 Agent 协作系统

```python
# 实现一个报告生成的多 Agent 协作系统
#
# Agent 角色：
# 1. Supervisor：任务分配和协调
# 2. Researcher：信息搜集（使用搜索工具）
# 3. Analyst：数据分析（使用计算工具）
# 4. Writer：报告撰写
# 5. Reviewer：质量审核
#
# 工作流程：
# 用户请求 → Supervisor 分解任务
#          → Researcher 搜集信息
#          → Analyst 分析数据
#          → Writer 撰写报告
#          → Reviewer 审核质量
#          → 返回最终报告
#
# 使用示例：
# team = ReportTeam()
# result = team.generate_report("分析苹果公司 2024 年度财报")
# print(result.report)
# print(f"参与 Agent: {result.agents_involved}")
#
# 技术要点：
# - LangGraph 状态机
# - 多 Agent 协作
# - 任务队列管理
# - 结果汇总
#
# 扩展方向：
# - 动态 Agent 创建
# - 并行任务执行
# - 人机协作节点
```

---

## 五、Agent 记忆

### 17. 会话记忆

#### 本节与前后课程的关系

- 这节承接 `02_llm` 对多轮对话本质的理解，也承接 `03_foundation` 对状态和组件边界的认知。
- 和 `04_rag` 不同，这里关注的不是知识检索，而是 Agent 在连续任务中的状态延续、摘要和恢复。
- 到 `06_application` 中，它会直接落到用户会话连续性、客服工作台上下文延续、人工接续等真实需求。
- 边界：这里讲的是 AI 系统里的记忆机制，不等于完整用户档案系统或业务主数据系统。

#### 知识点

1. **记忆类型**
   - 短期记忆：当前对话
   - 长期记忆：跨会话持久化
   - 工作记忆：任务相关上下文

2. **主线方案：LangGraph 状态 + Checkpointer**
   - 短期记忆优先放在 graph state 中管理
   - 用 `thread_id` 区分会话
   - 用 checkpointer 负责暂停、恢复和持久化

3. **兼容认知：LangChain Memory（了解即可）**
   - ConversationBufferMemory
   - ConversationSummaryMemory
   - VectorStoreMemory
   - 适合理解历史方案，但新项目优先考虑 LangGraph 状态模型

4. **记忆管理**
   - 容量限制
   - 淘汰策略
   - 重要性筛选

#### 实战案例

```python
from langgraph.checkpoint.memory import MemorySaver

# 1. 主线：用 checkpointer 保留会话状态
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user_123"}}
app.invoke({"messages": [("user", "你好")]}, config=config)
app.invoke({"messages": [("user", "继续刚才的话题")]}, config=config)

# 2. 长对话时，不直接塞全部历史
# 而是把历史压缩成摘要，再和最近几轮消息一起注入

# 3. 兼容了解：LangChain Memory 的旧式写法
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
```

---

### 18. LangGraph 记忆

#### 知识点

1. **Checkpointer 与 Store 的分工**
   - Checkpointer：保存执行中的线程状态
   - Store：保存可跨线程复用的长期记忆或知识
   - 不要把所有记忆都塞进一份对话历史

2. **Checkpointer 机制**
   - 保存执行状态
   - 支持暂停/恢复
   - 时间旅行调试

3. **MemorySaver**
   - 内存存储
   - 适合开发测试

4. **持久化存储**
   - SqliteSaver
   - RedisSaver

#### 实战案例

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 1. 添加 Checkpointer
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# 2. 带 thread_id 的执行
config = {"configurable": {"thread_id": "conversation_123"}}
result = app.invoke({"messages": ["你好"]}, config=config)

# 3. 恢复对话
result = app.invoke({"messages": ["继续"]}, config=config)

# 4. 查看历史状态
states = app.get_state_history(config)
for state in states:
    print(state)

# 5. 回到之前的状态
app.update_state(config, previous_state)
```

---

### 综合案例：带记忆的智能助手

```python
# 实现一个带持久化记忆的智能助手
#
# 功能要求：
# 1. 短期记忆（当前会话）
# 2. 长期记忆（跨会话持久化）
# 3. 记忆摘要（长对话压缩）
# 4. 多用户支持
# 5. 记忆搜索
#
# 使用示例：
# assistant = MemoryAssistant(
#     persist_dir="./memory",
#     summary_threshold=20  # 超过20轮对话时摘要
# )
#
# # 会话1
# assistant.chat("user_1", "我喜欢吃苹果")
# assistant.chat("user_1", "我还喜欢什么水果？")  # 能记住
#
# # 会话2（新会话）
# assistant.chat("user_1", "我之前说我喜欢什么？")  # 能回忆
#
# # 记忆管理
# assistant.clear_memory("user_1")
# assistant.export_memory("user_1", "memory.json")
#
# 技术要点：
# - LangGraph Checkpointer
# - 摘要生成
# - 多用户隔离
# - 持久化存储
#
# 扩展方向：
# - 向量化记忆（语义搜索）
# - 记忆重要性排序
# - 遗忘机制
```

---

## 六、Agent 工具开发与安全

### 19. 自定义工具

#### 知识点

1. **工具设计原则**
   - 单一职责
   - 清晰的描述
   - 合理的参数

2. **工具类型**
   - API 调用工具
   - 数据库查询工具
   - 文件操作工具
   - 计算工具

3. **错误处理**
   - 参数验证
   - 执行异常
   - 超时处理

#### 实战案例

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests

# 1. API 调用工具
class WeatherInput(BaseModel):
    city: str = Field(description="城市名称")
    unit: str = Field(default="celsius", description="温度单位")

@tool(args_schema=WeatherInput)
def get_weather(city: str, unit: str = "celsius") -> str:
    """获取指定城市的实时天气信息"""
    try:
        # 调用天气 API
        response = requests.get(f"https://api.weather.com/{city}")
        data = response.json()
        return f"{city}当前温度：{data['temp']}°{unit[0].upper()}"
    except Exception as e:
        return f"获取天气失败：{str(e)}"

# 2. 数据库查询工具
@tool
def query_database(sql: str) -> str:
    """执行 SQL 查询，返回结果"""
    # 注意：生产环境需要 SQL 注入防护
    pass

# 3. 文件操作工具
@tool
def read_file(file_path: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"读取失败：{str(e)}"

# 4. 组合工具
class Toolkit:
    def __init__(self):
        self.tools = [get_weather, query_database, read_file]
```

---

### 20. 工具安全

#### 知识点

1. **安全风险**
   - SQL 注入
   - 命令注入
   - 敏感数据泄露
   - 权限滥用

2. **防护措施**
   - 参数白名单
   - 权限控制
   - 执行沙箱
   - 日志审计

3. **最佳实践**
   - 最小权限原则
   - 输入验证
   - 输出过滤
   - 用户确认

#### 实战案例

```python
# 1. 参数白名单
ALLOWED_TABLES = ["users", "products", "orders"]

@tool
def safe_query(table: str, conditions: dict) -> str:
    """安全的数据库查询"""
    if table not in ALLOWED_TABLES:
        return "错误：不允许查询此表"
    # 执行查询...

# 2. 用户确认机制
class ConfirmTool:
    def __init__(self, tool, requires_confirmation=True):
        self.tool = tool
        self.requires_confirmation = requires_confirmation

    def invoke(self, *args, **kwargs):
        if self.requires_confirmation:
            # 等待用户确认
            pass
        return self.tool.invoke(*args, **kwargs)

# 3. 执行沙箱
import subprocess

@tool
def run_python_safely(code: str) -> str:
    """在沙箱中执行 Python 代码"""
    # 使用 RestrictedPython 或容器隔离
    pass

# 4. 日志审计
import logging

def audited_tool(tool):
    def wrapper(*args, **kwargs):
        logging.info(f"Tool {tool.name} called with {args}, {kwargs}")
        result = tool.invoke(*args, **kwargs)
        logging.info(f"Tool {tool.name} returned: {result[:100]}...")
        return result
    return wrapper
```

---

### 21. Guardrails 与安全边界 📌

#### 本节与前后课程的关系

- 它承接 `02_llm` 里的可靠性、安全、成本意识，但把问题从“单次调用风险”升级成“动态系统风险”。
- 前面的工具安全主要关注单个工具，这一节开始从输入、决策、输出三个层次看 Agent 的整体安全边界。
- 对 `06_application` 来说，这一节是后续合规审核、权限审批、人工接管、失败降级的直接前置。
- 边界：这里建立的是 Agent Guardrails 设计方法，不替代完整企业安全体系、审计系统或合规制度建设。

#### 知识点

1. **常见风险不只来自工具**
   - Prompt Injection / Indirect Prompt Injection
   - 数据外泄
   - PII 暴露
   - 越权访问
   - 敏感操作未审批
   - 模型在失败时“假装成功”

2. **Guardrails 的层次**
   - 输入前：敏感意图检测、PII 检测、权限校验
   - 决策中：限制可用工具、限制可访问资源、强制审批节点
   - 输出后：脱敏、格式校验、事实约束、拒答策略

3. **关键策略**
   - 最小权限原则
   - 用户身份和资源权限绑定
   - 对写操作、外发操作、删除操作加审批
   - 失败时降级到只读、拒答或人工接管

4. **工程实践**
   - 把 guardrail 当成独立节点，而不是一句 Prompt
   - 给高风险样本单独建安全评估集
   - 审批、拒答、降级都要可追踪

#### 实战案例

```python
# 1. 在 Agent 前增加输入风控节点
def guardrail_input(state):
    # 检测越权、敏感词、PII、注入攻击
    pass

# 2. 对敏感工具强制审批
def require_approval(action):
    if action in {"delete_file", "send_email", "transfer_money"}:
        return "human_review"
    return "allowed"

# 3. 输出前做脱敏和策略校验
def guardrail_output(answer: str) -> str:
    # 脱敏 / 格式校验 / 安全兜底
    return answer

# 4. 失败降级
# 工具不可用、权限不满足、风险过高时：
# - 拒答
# - 返回只读结果
# - 转人工处理
```

---

### 综合案例：安全工具集

```python
# 实现一个安全的 Agent 工具集
#
# 功能要求：
# 1. 工具注册和分类
# 2. 权限控制（只读/读写）
# 3. 参数验证
# 4. 执行日志
# 5. 敏感操作确认
#
# 使用示例：
# toolkit = SecureToolkit()
#
# # 注册工具
# toolkit.register(read_file, permission="read")
# toolkit.register(write_file, permission="write", require_confirm=True)
# toolkit.register(execute_sql, permission="admin", require_confirm=True)
#
# # 获取工具列表（根据权限过滤）
# tools = toolkit.get_tools(user_permission="read")
#
# # 执行工具（自动记录日志）
# result = toolkit.execute("read_file", {"path": "test.txt"}, user="user_1")
#
# # 查看日志
# toolkit.get_logs(user="user_1")
#
# 技术要点：
# - 权限模型设计
# - 参数验证框架
# - 日志系统
# - 确认机制
#
# 扩展方向：
# - 审计报告生成
# - 异常行为检测
# - 工具使用统计
```

---

## 七、Agent 调试、评测与观测

### 22. Agent 调试

#### 知识点

1. **调试方法**
   - verbose 模式
   - 回调函数
   - 中间状态检查

2. **常见问题**
   - 无限循环
   - 工具调用失败
   - 参数解析错误
   - 推理错误

3. **调试工具**
   - LangSmith
   - 打印中间结果
   - 状态可视化

#### 实战案例

```python
# 1. verbose 模式
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 打印详细执行过程
    max_iterations=10,  # 防止无限循环
    handle_parsing_errors=True  # 处理解析错误
)

# 2. 自定义回调
from langchain.callbacks.base import BaseCallbackHandler

class DebugCallback(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"开始调用工具: {serialized['name']}")
        print(f"输入: {input_str}")

    def on_tool_end(self, output, **kwargs):
        print(f"工具输出: {output}")

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[DebugCallback()]
)

# 3. LangSmith 追踪
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"

# 所有执行会自动追踪到 LangSmith

# 4. LangGraph 状态检查
for state in app.get_state_history(config):
    print(f"步骤: {state.metadata['step']}")
    print(f"下一个节点: {state.next}")
    print(f"状态: {state.values}")
```

---

### 23. Agent 可观测性与成本控制

#### 知识点

1. **可观测性三支柱**
   - Logs：日志
   - Metrics：指标
   - Traces：追踪

2. **关键指标**
   - Token 消耗
   - 响应时间
   - 工具调用次数
   - 成功率

3. **观测平台**
   - LangSmith
   - Arize Phoenix
   - 自建监控

4. **Agent 成本控制** 📌
   - 迭代次数限制（max_iterations 防止无限循环）
   - 模型降级策略（复杂推理用大模型，简单工具调用用小模型）
   - 工具调用缓存（相同参数的工具调用缓存结果）
   - Token 预算控制（设置单次执行的 Token 上限）
   - 成本预警（超过阈值时中断或降级）

#### 实战案例

```python
# 1. 添加指标收集
import time
from dataclasses import dataclass

@dataclass
class AgentMetrics:
    start_time: float
    end_time: float = 0
    tool_calls: int = 0
    tokens_used: int = 0
    success: bool = False

    @property
    def duration(self):
        return self.end_time - self.start_time

# 2. 带监控的 Agent 执行器
class MonitoredAgentExecutor:
    def __init__(self, agent_executor):
        self.agent_executor = agent_executor
        self.metrics_history = []

    def invoke(self, input_dict):
        metrics = AgentMetrics(start_time=time.time())
        try:
            result = self.agent_executor.invoke(input_dict)
            metrics.success = True
            return result
        finally:
            metrics.end_time = time.time()
            self.metrics_history.append(metrics)

# 3. 导出指标
def export_metrics(metrics_list):
    total_calls = len(metrics_list)
    success_rate = sum(1 for m in metrics_list if m.success) / total_calls
    avg_duration = sum(m.duration for m in metrics_list) / total_calls

    return {
        "total_calls": total_calls,
        "success_rate": success_rate,
        "avg_duration": avg_duration
    }

# 4. 集成 LangSmith
# 查看追踪、Token 消耗、执行时间等

# 5. Agent 成本控制实战
class CostControlledAgent:
    def __init__(self, max_iterations=10, token_budget=10000):
        self.max_iterations = max_iterations
        self.token_budget = token_budget
        self.total_tokens = 0

    def should_continue(self, state) -> bool:
        """判断是否继续执行"""
        if self.total_tokens >= self.token_budget:
            return False  # 超预算，停止
        return True

    def select_model(self, task_type: str) -> str:
        """根据任务类型选择模型（降级策略）"""
        if task_type == "reasoning":
            return "gpt-4o"
        return "gpt-4o-mini"  # 简单任务用便宜模型

# 6. 工具调用缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_tool_call(tool_name: str, args_hash: str) -> str:
    # 相同参数的工具调用直接返回缓存结果
    pass
```

---

### 24. Agent 评估与回归测试 📌

#### 本节与前后课程的关系

- 这一节和开头的“评估前置”形成呼应：前面建立最小评估集，这里把它发展成更完整的回归方法。
- 它承接 `04_rag` 的效果回归思路，但在 Agent 场景下新增了轨迹、安全、成本、路由正确性这些维度。
- 到 `06_application` 里，这会直接变成业务工作流发布前检查、坏案例回流和版本对比的基础能力。
- 边界：这里解决的是 Agent 应用的评测方法，不展开完整 DevOps / LLMOps 平台建设。

#### 知识点

1. **评估维度**
   - 最终答案质量
   - 工具调用轨迹
   - 路由是否正确
   - 审批 / 拒答是否触发
   - 成本和时延是否超预算

2. **常见评估类型**
   - Final-answer eval
   - Trajectory eval
   - Safety eval
   - Cost / latency regression

3. **回归测试流程**
   - 固定 golden set
   - 每次改 Prompt / Tool / Graph / Model 都回归
   - 设置发布门槛：成功率、拒答率、成本预算、超时比例

4. **工程落地**
   - 评估结果进 CI 或发布前检查
   - 坏案例单独沉淀为 regression set
   - 线上失败样本回流到评估集

#### 实战案例

```python
golden_cases = [
    {
        "input": "查询北京天气",
        "expected_tool": "get_weather",
        "expected_answer_contains": "北京",
    },
    {
        "input": "删除生产数据库",
        "expected_outcome": "require_human_confirmation",
    },
]

def run_agent_eval(agent, cases):
    # 记录：
    # 1. 最终答案
    # 2. 工具调用轨迹
    # 3. 是否命中 guardrail
    # 4. Token / latency / success rate
    pass
```

---

### 综合案例：Agent 监控与评测系统

```python
# 实现一个 Agent 监控、评测和调试系统
#
# 功能要求：
# 1. 执行日志记录
# 2. 性能指标收集
# 3. 错误追踪
# 4. 执行回放
# 5. 实时监控面板
# 6. golden set 回归测试
# 7. 安全样本评估
#
# 使用示例：
# monitor = AgentMonitor()
#
# # 包装 Agent
# monitored_agent = monitor.wrap(agent_executor)
#
# # 正常执行
# result = monitored_agent.invoke({"input": "你好"})
#
# # 查看指标
# print(monitor.get_metrics())
#
# # 回放执行过程
# monitor.replay(session_id="xxx")
# #
# # 跑回归测试
# # monitor.run_eval_suite("evals/agent_golden_set.jsonl")
#
# # 导出报告
# monitor.export_report("report.html")
#
# 技术要点：
# - 回调机制
# - 指标收集
# - 日志存储
# - 可视化展示
#
# 扩展方向：
# - 实时告警
# - 异常检测
# - 性能优化建议
```

---

## 八、综合项目

### 25. 智能助手 Agent

```python
# 实现一个功能丰富的智能助手
#
# 功能要求：
# 1. 多工具支持
#    - 网络搜索
#    - 天气查询
#    - 计算器
#    - 代码执行
#    - 文件操作
#
# 2. 对话能力
#    - 多轮对话
#    - 上下文记忆
#    - 流式输出
#
# 3. 安全控制
#    - 敏感操作确认
#    - 权限控制
#    - 错误处理
#    - Prompt Injection / PII Guardrails
#
# 4. 可观测性
#    - 执行日志
#    - Token 统计
#    - 性能监控
#    - 回归评估
#
# 技术要求：
# - LangGraph 实现状态机
# - FastAPI 提供 API
# - SQLite 持久化记忆
# - Context Manager
```

---

### 26. 多 Agent 协作系统

```python
# 实现一个多 Agent 协作的报告生成系统（可扩展框架）
#
# Agent 角色：
# 1. Supervisor：任务分配和协调
# 2. Researcher：信息搜集
# 3. Analyst：数据分析
# 4. Writer：报告撰写
# 5. Reviewer：质量审核
#
# 工作流程：
# 用户请求 → Supervisor 分解任务
#          → Researcher 搜集信息
#          → Analyst 分析数据
#          → Writer 撰写报告
#          → Reviewer 审核质量
#          → 返回最终报告
#
# 功能要求：
# - 动态任务分配
# - 中间结果共享
# - 质量迭代优化
# - 执行状态追踪
# - 角色权限边界
# - 回归评估集
#
# 技术要求：
# - LangGraph 状态机
# - 多 Agent 协作
# - Checkpoint 持久化
# - 流式输出进度
#
# 扩展方向：
# - 添加人机协作
# - 添加并行执行
# - 添加动态 Agent 创建
```

---

## 学习资源

### 官方文档
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### 教程
- [Build an Agent](https://python.langchain.com/docs/tutorials/agents/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)

### 工具
- [LangSmith](https://www.langchain.com/langsmith) - 调试和监控
- [AgentBench](https://github.com/THUDM/AgentBench) - Agent 评测
- [OpenAI Evals](https://platform.openai.com/docs/guides/evals) - 评测参考

### 论文
- [ReAct](https://arxiv.org/abs/2210.03629)
- [Toolformer](https://arxiv.org/abs/2302.04004)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

---

## 验收标准

完成本阶段学习后，你应该能够：

1. **解释** Agent 的工作原理和适用场景
2. **判断** `Chain / Workflow / Agent / Multi-Agent` 的适用边界
3. **实现** 基于 Function Calling 的工具调用
4. **构建** 使用 LangChain/LangGraph 的 Agent
5. **设计** 多 Agent 协作系统
6. **实现** Agent 记忆、状态管理与 Context Engineering
7. **调试** Agent 执行过程，并建立最小回归评估集
8. **开发** 带 guardrails 的安全 Agent 工具与流程
