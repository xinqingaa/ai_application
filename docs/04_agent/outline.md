# Agent 学习大纲

> 目标：掌握 Agent 架构、工具调用、多步骤任务执行

---

## 一、Agent 基础概念

### 1. 什么是 Agent

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

## 二、Function Calling

### 2. Function Calling 基础

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

### 3. 实现完整的工具调用循环

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

### 4. Claude Tool Use

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

## 三、LangChain Agent

### 5. LangChain Tools

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

### 6. LangChain Agent 构建

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

### 7. LangGraph 基础

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

### 8. LangGraph Agent 实战

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
# - 流式输出处理
#
# 扩展方向：
# - 添加更多工具
# - 添加记忆持久化
# - 添加人机协作节点
```

---

## 四、Agent 设计模式

### 9. ReAct 模式

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

### 10. Plan-and-Execute 模式

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

### 11. Multi-Agent 协作

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

### 12. 会话记忆

#### 知识点

1. **记忆类型**
   - 短期记忆：当前对话
   - 长期记忆：跨会话持久化
   - 工作记忆：任务相关上下文

2. **LangChain Memory**
   - ConversationBufferMemory
   - ConversationSummaryMemory
   - VectorStoreMemory

3. **记忆管理**
   - 容量限制
   - 淘汰策略
   - 重要性筛选

#### 实战案例

```python
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_community.chat_message_histories import ChatMessageHistory

# 1. 基础记忆
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 2. 带记忆的 Agent
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)

# 3. 摘要记忆（长对话）
summary_memory = ConversationSummaryMemory(
    llm=llm,
    memory_key="chat_history"
)

# 4. 持久化记忆
from langchain_community.chat_message_histories import RedisChatMessageHistory

history = RedisChatMessageHistory(
    session_id="user_123",
    url="redis://localhost:6379"
)
```

---

### 13. LangGraph 记忆

#### 知识点

1. **Checkpointer 机制**
   - 保存执行状态
   - 支持暂停/恢复
   - 时间旅行调试

2. **MemorySaver**
   - 内存存储
   - 适合开发测试

3. **持久化存储**
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

## 六、Agent 工具开发

### 14. 自定义工具

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

### 15. 工具安全

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

## 七、Agent 调试与观测

### 16. Agent 调试

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

### 17. Agent 可观测性

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
```

---

### 综合案例：Agent 监控系统

```python
# 实现一个 Agent 监控和调试系统
#
# 功能要求：
# 1. 执行日志记录
# 2. 性能指标收集
# 3. 错误追踪
# 4. 执行回放
# 5. 实时监控面板
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

### 18. 智能助手 Agent

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
#
# 4. 可观测性
#    - 执行日志
#    - Token 统计
#    - 性能监控
#
# 技术要求：
# - LangGraph 实现状态机
# - FastAPI 提供 API
# - SQLite 持久化记忆
```

---

### 19. 多 Agent 协作系统

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

### 教程
- [Build an Agent](https://python.langchain.com/docs/tutorials/agents/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)

### 工具
- [LangSmith](https://www.langchain.com/langsmith) - 调试和监控
- [AgentBench](https://github.com/THUDM/AgentBench) - Agent 评测

### 论文
- [ReAct](https://arxiv.org/abs/2210.03629)
- [Toolformer](https://arxiv.org/abs/2302.04004)

---

## 验收标准

完成本阶段学习后，你应该能够：

1. **解释** Agent 的工作原理和适用场景
2. **实现** 基于 Function Calling 的工具调用
3. **构建** 使用 LangChain/LangGraph 的 Agent
4. **设计** 多 Agent 协作系统
5. **实现** Agent 记忆和状态管理
6. **调试** Agent 执行过程
7. **开发** 安全可靠的 Agent 工具
