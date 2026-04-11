"""
定义 foundation_lab 的 service 层。

service 层是这个项目骨架里最重要的编排位置：它负责决定走 plain、
retrieval 还是 tool 路径，而不是把判断逻辑塞进脚本或 API。
"""

from __future__ import annotations

from collections.abc import Iterator

from app.chains.qa_chain import SimpleQAChain
from app.config import Settings, get_settings
from app.llm.client_langchain import LangChainLLMClient
from app.llm.client_native import NativeLLMClient
from app.retrievers.mock_retriever import MockRetriever
from app.schemas import AskResponse
from app.tools.mock_tools import run_tool


class QAService:
    """统一组织问答主流程的服务对象。

    如果你想理解整个项目“问题是怎么被处理的”，优先读这个类。

    推荐阅读顺序：
    1. `ask()`：总入口，决定走哪条路径
    2. `select_path()`：解释为什么会被分到 plain / retrieval / tool
    3. `ask_plain()`、`ask_with_retrieval()`、`ask_with_tool()`：分别看三条路径
    4. `_select_chain()`：看 native 和 langchain 是如何切换的
    """

    def __init__(
        self,
        settings: Settings | None = None,
        retriever: MockRetriever | None = None,
    ) -> None:
        """初始化配置、retriever 和两套客户端实现。"""

        self.settings = settings or get_settings()
        self.retriever = retriever or MockRetriever()
        self.native_client = NativeLLMClient(self.settings)
        self.langchain_client = LangChainLLMClient(self.settings)

    def ask(self, question: str, engine: str = "langchain") -> AskResponse:
        """根据问题内容选择最合适的最小路径。

        这是整个 service 层的总入口。

        一次请求进入后，会先做一件很重要的事：
        不是立刻调用模型，而是先判断这次问题属于哪一类。

        当前阶段只保留三条最小路径：
        - `plain`：普通问答，不需要额外上下文
        - `retrieval`：需要先拿文档，再回答
        - `tool`：需要先执行工具，再回答
        """

        # 先做路径判断，再分发到具体处理函数。
        path = self.select_path(question)
        if path == "retrieval":
            return self.ask_with_retrieval(question, engine=engine)
        if path == "tool":
            return self.ask_with_tool(question, engine=engine)
        return self.ask_plain(question, engine=engine)

    def stream(self, question: str, engine: str = "langchain") -> Iterator[str]:
        """复用普通问答结果，提供最小流式输出接口。

        当前版本为了保持骨架简单，没有单独实现真正的流式编排，
        而是先复用 `ask()` 的完整结果，再拆成 token 逐段输出。
        """

        # 先走完整问答流程，保证流式接口和普通接口的业务判断保持一致。
        response = self.ask(question, engine=engine)
        # 再把完整答案拆成若干片段，模拟流式输出。
        for token in response.answer.split():
            yield f"{token} "

    def ask_plain(self, question: str, engine: str = "langchain") -> AskResponse:
        """执行不依赖额外上下文的普通问答。

        这条路径最简单：
        1. 选定要用哪种客户端
        2. 直接把原始问题交给 chain
        3. 返回统一的 `AskResponse`
        """

        # 这里先决定底层使用 native 还是 langchain 风格客户端。
        chain = self._select_chain(engine)
        # plain 路径没有额外上下文，直接把问题送进 chain。
        answer = chain.invoke(question)
        return AskResponse(
            question=question,
            answer=answer,
            path="plain",
            engine=engine,
            mocked=True,
        )

    def ask_with_retrieval(self, question: str, engine: str = "langchain") -> AskResponse:
        """先取回文档，再把文档内容并入 Prompt。

        这条路径体现的是 Retriever 的角色：
        它不直接给最终答案，而是先返回“可以放进 Prompt 的文档上下文”。

        执行顺序是：
        1. retriever 根据问题找相关文档
        2. 把文档整理成 Prompt 可用的 context_blocks
        3. 把原始问题和文档上下文一起交给 chain
        """

        # 第一步：Retriever 返回相关文档，而不是直接产出答案。
        documents = self.retriever.retrieve(question)
        # 第二步：把文档对象转成 Prompt 更容易消费的字符串列表。
        context_blocks = [f"{item.title}: {item.content}" for item in documents]
        chain = self._select_chain(engine)
        # 第三步：把“问题 + 文档上下文”一起送入 chain。
        answer = chain.invoke(question, context_blocks=context_blocks)
        return AskResponse(
            question=question,
            answer=answer,
            path="retrieval",
            engine=engine,
            mocked=True,
            used_documents=documents,
        )

    def ask_with_tool(self, question: str, engine: str = "langchain") -> AskResponse:
        """先执行工具，再把工具结果并入 Prompt。

        这条路径体现的是 Tool 的角色：
        它不是返回知识文档，而是先执行一个动作，再把动作结果交还给模型。

        执行顺序是：
        1. 从问题中推断要调用哪个工具
        2. 执行该工具，得到结构化结果
        3. 把工具结果作为额外输入交给 chain
        """

        # 第一步：根据问题特征选择工具及其输入。
        tool_name, tool_input = self._select_tool(question)
        # 第二步：真正执行工具，拿到标准化的 ToolResult。
        tool_result = run_tool(tool_name, tool_input)
        chain = self._select_chain(engine)
        # 第三步：把工具结果并入 Prompt，再生成最终答案。
        answer = chain.invoke(question, tool_result=tool_result.output)
        return AskResponse(
            question=question,
            answer=answer,
            path="tool",
            engine=engine,
            mocked=True,
            used_tool=tool_result,
        )

    def select_path(self, question: str) -> str:
        """用简单关键词规则判断当前问题应走哪条路径。

        这个方法是当前阶段最重要的“最小编排逻辑”。

        它故意写得很简单，因为 `03` 阶段的重点不是做复杂智能路由，
        而是先把“不同问题可能进入不同处理路径”这个结构建立起来。
        """

        normalized = question.lower()
        # 含有时间、计算或规则查询特征时，优先走工具路径。
        if any(token in normalized for token in ("time", "calculate", "rule", "+", "-", "*", "/")):
            return "tool"
        # 含有文档、LangChain、service 等主题词时，优先走检索路径。
        if any(token in normalized for token in ("document", "retriever", "langchain", "foundation_lab", "service")):
            return "retrieval"
        # 其余情况默认回退到普通问答路径。
        return "plain"

    def _select_tool(self, question: str) -> tuple[str, str]:
        """从问题中推断应该调用哪个 mock 工具。

        这个方法和 `select_path()` 的区别是：
        - `select_path()` 负责决定“走不走 tool 路径”
        - `_select_tool()` 负责决定“具体走哪个工具”
        """

        normalized = question.lower()
        # 如果像数学表达式，或者显式出现 calculate，就走计算器。
        if any(symbol in question for symbol in ("+", "-", "*", "/")) or "calculate" in normalized:
            expression = question.replace("calculate", "").strip() or "0"
            return "calculator", expression
        # 如果问题关注当前时间，就走时间工具。
        if "time" in normalized:
            return "current_time", ""
        # 其余 tool 路径问题先回退到规则查询。
        return "rule_lookup", "quality"

    def _select_chain(self, engine: str) -> SimpleQAChain:
        """根据引擎类型返回对应的最小 chain。

        这里体现的是“同一条业务流程，可以切换不同底层客户端”。
        service 层不直接关心客户端细节，只关心拿到一个可调用的 chain。
        """

        if engine == "native":
            # native 路径更贴近底层 SDK 调用。
            return SimpleQAChain(self.native_client)
        # 默认走 langchain 风格客户端，强调组件化调用方式。
        return SimpleQAChain(self.langchain_client)


def build_default_service() -> QAService:
    """创建一份带默认依赖的 service 实例。"""

    return QAService()
