"""
最小 mock retriever 实现。

它的用途不是验证检索效果，而是先把“Retriever 返回文档”这条边界固定下来，
避免在 `03` 阶段过早进入真实 RAG 复杂度。
"""

from __future__ import annotations

from app.schemas import RetrievedDocument


DEFAULT_DOCUMENTS = (
    RetrievedDocument(
        doc_id="doc-1",
        title="LangChain Components",
        content="Model, prompt, parser, retriever and tool should stay as separate responsibilities.",
        tags=("langchain", "abstractions", "components"),
    ),
    RetrievedDocument(
        doc_id="doc-2",
        title="foundation_lab Goal",
        content="foundation_lab validates the minimal structure before real RAG or Agent complexity is introduced.",
        tags=("foundation_lab", "goal", "structure"),
    ),
    RetrievedDocument(
        doc_id="doc-3",
        title="Service Layer Boundary",
        content="The service layer centralizes path routing instead of pushing business decisions into the API layer.",
        tags=("service", "boundary", "engineering"),
    ),
)


class MockRetriever:
    """根据简单关键词规则返回预置文档。"""

    def __init__(self, documents: tuple[RetrievedDocument, ...] = DEFAULT_DOCUMENTS) -> None:
        """允许在测试或后续实验中注入自定义文档集合。"""

        self.documents = documents

    def retrieve(self, query: str, top_k: int = 2) -> list[RetrievedDocument]:
        """按关键词命中次数做最简单的相关性排序。"""

        normalized_query = query.lower()
        scored: list[tuple[int, RetrievedDocument]] = []
        for document in self.documents:
            haystack = " ".join((document.title, document.content, " ".join(document.tags))).lower()
            score = sum(1 for word in normalized_query.split() if word and word in haystack)
            if score > 0:
                scored.append((score, document))

        if not scored:
            return [self.documents[0]]

        scored.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored[:top_k]]
