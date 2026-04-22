import argparse
from dataclasses import dataclass
from typing import Literal

from chroma_store import ChromaVectorStore, ChromaVectorStoreConfig
from langchain_adapter import (
    LangChainChromaConfig,
    build_documents,
    create_langchain_chroma,
    retrieval_results_from_scored_documents,
    reset_langchain_chroma,
)
from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    RetrievalResult,
    SourceChunk,
    VectorStoreConfig,
    demo_embedded_chunks,
)

BackendName = Literal["json", "chroma", "langchain"]


@dataclass
class VectorStoreManager:
    backend: BackendName
    provider: LocalKeywordEmbeddingProvider

    def reset(self) -> None:
        if self.backend == "json":
            PersistentVectorStore(VectorStoreConfig()).reset()
            return
        if self.backend == "chroma":
            ChromaVectorStore(ChromaVectorStoreConfig()).reset()
            return
        reset_langchain_chroma(LangChainChromaConfig())

    def ensure_index(self) -> None:
        if self.backend == "json":
            store = PersistentVectorStore(VectorStoreConfig())
            if store.count() == 0:
                store.replace_document(demo_embedded_chunks(self.provider))
            return

        if self.backend == "chroma":
            store = ChromaVectorStore(ChromaVectorStoreConfig())
            if store.count() == 0:
                store.replace_document(demo_embedded_chunks(self.provider))
            return

        vectorstore = create_langchain_chroma(self.provider, LangChainChromaConfig())
        if vectorstore._collection.count() == 0:
            documents = build_documents()
            ids = [str(document.metadata["chunk_id"]) for document in documents]
            vectorstore.add_documents(documents=documents, ids=ids)

    def search(
        self,
        question: str,
        *,
        top_k: int,
        filename: str | None = None,
    ) -> list[RetrievalResult]:
        if self.backend == "json":
            store = PersistentVectorStore(VectorStoreConfig())
            query_vector = self.provider.embed_query(question)
            return store.similarity_search(
                query_vector=query_vector,
                provider=self.provider,
                top_k=top_k,
                filename=filename,
            )

        if self.backend == "chroma":
            store = ChromaVectorStore(ChromaVectorStoreConfig())
            query_vector = self.provider.embed_query(question)
            return store.similarity_search(
                query_vector=query_vector,
                provider=self.provider,
                top_k=top_k,
                where={"filename": filename} if filename else None,
            )

        vectorstore = create_langchain_chroma(self.provider, LangChainChromaConfig())
        search_kwargs: dict[str, object] = {"k": top_k}
        if filename:
            search_kwargs["filter"] = {"filename": filename}
        results = vectorstore.similarity_search_with_score(question, **search_kwargs)
        return retrieval_results_from_scored_documents(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare JSON store, Chroma, and LangChain Chroma backends.")
    parser.add_argument(
        "--backend",
        choices=["json", "chroma", "langchain"],
        default="json",
        help="Which backend to run for the Chapter 4 demo.",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="如何申请退费？",
        help="Question to search against the selected backend.",
    )
    parser.add_argument("--filename", help="Optional filename filter.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--reset", action="store_true", help="Reset the selected backend before indexing.")
    args = parser.parse_args()

    manager = VectorStoreManager(
        backend=args.backend,
        provider=LocalKeywordEmbeddingProvider(),
    )
    if args.reset:
        manager.reset()
        print(f"Backend `{args.backend}` was reset first.")
    manager.ensure_index()

    results = manager.search(
        args.question,
        top_k=args.top_k,
        filename=args.filename,
    )

    print(f"Backend: {args.backend}")
    print(f"Question: {args.question}")
    if args.filename:
        print(f"Filename filter: {args.filename}")
    for result in results:
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id} "
            f"filename={result.chunk.metadata.get('filename')}"
        )


if __name__ == "__main__":
    main()
