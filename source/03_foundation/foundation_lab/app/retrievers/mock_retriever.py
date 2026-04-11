"""
Mock retriever used to keep the RAG boundary explicit in phase 1.
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
    def __init__(self, documents: tuple[RetrievedDocument, ...] = DEFAULT_DOCUMENTS) -> None:
        self.documents = documents

    def retrieve(self, query: str, top_k: int = 2) -> list[RetrievedDocument]:
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
