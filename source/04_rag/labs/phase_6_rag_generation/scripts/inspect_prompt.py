from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chains.rag_chain import build_messages, format_context
from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.prompts.rag_prompt import NO_ANSWER_TEXT
from app.retrievers.chroma import ChromaRetriever, RetrievalStrategyConfig
from app.services.rag_service import filter_retrieval_results
from app.vectorstores.chroma_store import ChromaVectorStore, ChromaVectorStoreConfig


def ensure_index(store: ChromaVectorStore) -> None:
    if store.count() > 0:
        return

    provider = create_embedding_provider(
        EmbeddingProviderConfig(
            provider_name=settings.default_embedding_provider,
            model_name=settings.default_embedding_model,
            dimensions=settings.default_embedding_dimensions,
            api_key_env=settings.embedding_api_key_env,
            base_url=settings.embedding_base_url,
        )
    )
    split_config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    embedded_chunks = build_embedded_chunk_corpus(
        data_dir=settings.data_dir,
        split_config=split_config,
        supported_suffixes=settings.supported_suffixes,
        provider=provider,
        batch_size=settings.default_embedding_batch_size,
    )
    store.upsert(
        embedded_chunks,
        batch_size=settings.default_vector_store_batch_size,
    )


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Inspect the context and prompt used by the Phase 6 RAG chain.")
    parser.add_argument(
        "question",
        nargs="?",
        default="Where do we keep source path and chunk index metadata?",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.default_top_k,
    )
    parser.add_argument(
        "--strategy",
        choices=["similarity", "threshold", "mmr"],
        default=settings.default_retrieval_strategy,
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=settings.default_retrieval_score_threshold,
    )
    parser.add_argument(
        "--candidate-k",
        type=int,
        default=settings.default_retrieval_candidate_k,
    )
    parser.add_argument(
        "--mmr-lambda",
        type=float,
        default=settings.default_retrieval_mmr_lambda,
    )
    parser.add_argument(
        "--min-source-score",
        type=float,
        default=settings.default_generation_min_score,
    )
    parser.add_argument(
        "--max-context-chunks",
        type=int,
        default=settings.default_context_max_chunks,
    )
    parser.add_argument(
        "--max-chars-per-chunk",
        type=int,
        default=settings.default_context_max_chars_per_chunk,
    )
    parser.add_argument("--filename")
    return parser


def main() -> None:
    args = parse_args().parse_args()
    provider = create_embedding_provider(
        EmbeddingProviderConfig(
            provider_name=settings.default_embedding_provider,
            model_name=settings.default_embedding_model,
            dimensions=settings.default_embedding_dimensions,
            api_key_env=settings.embedding_api_key_env,
            base_url=settings.embedding_base_url,
        )
    )
    store = ChromaVectorStore(
        ChromaVectorStoreConfig(
            persist_directory=settings.vector_store_dir,
            collection_name=settings.default_vector_collection,
            distance_metric=settings.default_vector_distance,
        )
    )
    ensure_index(store)

    retriever = ChromaRetriever(
        store=store,
        provider=provider,
        config=RetrievalStrategyConfig(
            strategy_name=args.strategy,
            candidate_k=args.candidate_k,
            score_threshold=args.threshold if args.strategy == "threshold" else None,
            mmr_lambda=args.mmr_lambda,
            metadata_filter={"filename": args.filename} if args.filename else None,
        ),
    )
    retrieved = retriever.retrieve(args.question, top_k=args.top_k)
    accepted = filter_retrieval_results(retrieved, min_score=args.min_source_score)

    print(f"Question: {args.question}")
    print(
        "Retriever: "
        f"strategy={args.strategy} "
        f"top_k={args.top_k} "
        f"candidate_k={args.candidate_k} "
        f"threshold={retriever.config.score_threshold} "
        f"mmr_lambda={args.mmr_lambda}"
    )
    if args.filename:
        print(f"Filter: filename={args.filename}")
    print(
        "Context policy: "
        f"min_source_score={args.min_source_score:.2f} "
        f"max_context_chunks={args.max_context_chunks} "
        f"max_chars_per_chunk={args.max_chars_per_chunk}"
    )
    print()
    print(f"Retrieved chunks: {len(retrieved)}")
    for index, item in enumerate(retrieved, start=1):
        preview = item.chunk.content.replace("\n", " ")[:88]
        score_text = f"{item.score:.3f}" if item.score is not None else "n/a"
        print(
            f"- raw[{index}] score={score_text} "
            f"filename={item.chunk.metadata.get('filename')} "
            f"chunk={item.chunk.metadata.get('chunk_index')}"
        )
        print(f"  preview={preview}")

    print()
    print(f"Accepted chunks: {len(accepted)}")
    if not accepted:
        print(NO_ANSWER_TEXT)
        return

    context = format_context(
        accepted,
        max_chunks=args.max_context_chunks,
        max_chars_per_chunk=args.max_chars_per_chunk,
    )
    messages = build_messages(
        question=args.question,
        results=accepted,
        max_chunks=args.max_context_chunks,
        max_chars_per_chunk=args.max_chars_per_chunk,
    )

    print()
    print("Formatted context:")
    print(context)
    print()
    print("Messages:")
    for message in messages:
        print(f"[{message['role']}]")
        print(message["content"])
        print()


if __name__ == "__main__":
    main()
