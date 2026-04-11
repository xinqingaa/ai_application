"""
Service layer for the minimal QA routes.
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
    def __init__(
        self,
        settings: Settings | None = None,
        retriever: MockRetriever | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.retriever = retriever or MockRetriever()
        self.native_client = NativeLLMClient(self.settings)
        self.langchain_client = LangChainLLMClient(self.settings)

    def ask(self, question: str, engine: str = "langchain") -> AskResponse:
        path = self.select_path(question)
        if path == "retrieval":
            return self.ask_with_retrieval(question, engine=engine)
        if path == "tool":
            return self.ask_with_tool(question, engine=engine)
        return self.ask_plain(question, engine=engine)

    def stream(self, question: str, engine: str = "langchain") -> Iterator[str]:
        response = self.ask(question, engine=engine)
        for token in response.answer.split():
            yield f"{token} "

    def ask_plain(self, question: str, engine: str = "langchain") -> AskResponse:
        chain = self._select_chain(engine)
        answer = chain.invoke(question)
        return AskResponse(
            question=question,
            answer=answer,
            path="plain",
            engine=engine,
            mocked=True,
        )

    def ask_with_retrieval(self, question: str, engine: str = "langchain") -> AskResponse:
        documents = self.retriever.retrieve(question)
        context_blocks = [f"{item.title}: {item.content}" for item in documents]
        chain = self._select_chain(engine)
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
        tool_name, tool_input = self._select_tool(question)
        tool_result = run_tool(tool_name, tool_input)
        chain = self._select_chain(engine)
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
        normalized = question.lower()
        if any(token in normalized for token in ("time", "calculate", "rule", "+", "-", "*", "/")):
            return "tool"
        if any(token in normalized for token in ("document", "retriever", "langchain", "foundation_lab", "service")):
            return "retrieval"
        return "plain"

    def _select_tool(self, question: str) -> tuple[str, str]:
        normalized = question.lower()
        if any(symbol in question for symbol in ("+", "-", "*", "/")) or "calculate" in normalized:
            expression = question.replace("calculate", "").strip() or "0"
            return "calculator", expression
        if "time" in normalized:
            return "current_time", ""
        return "rule_lookup", "quality"

    def _select_chain(self, engine: str) -> SimpleQAChain:
        if engine == "native":
            return SimpleQAChain(self.native_client)
        return SimpleQAChain(self.langchain_client)


def build_default_service() -> QAService:
    return QAService()
