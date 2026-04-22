from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.retrievers.chroma import ChromaRetriever, RetrievalStrategyConfig
from app.services.rag_service import RagService
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
    parser = ArgumentParser(description="Run the Phase 5 query demo.")
    parser.add_argument(
        "question",
        nargs="?",
        default="Where do we keep source path and chunk index metadata?",
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
    service = RagService(retriever=retriever)
    result = service.ask(args.question)

    print(
        "Retriever: "
        f"strategy={args.strategy} "
        f"candidate_k={args.candidate_k} "
        f"threshold={retriever.config.score_threshold} "
        f"mmr_lambda={args.mmr_lambda}"
    )
    if args.filename:
        print(f"Filter: filename={args.filename}")
    print()
    print(result.answer)
    print("Sources:")
    for item in result.sources:
        print(
            f"- {item.metadata.get('filename')} "
            f"chunk={item.metadata.get('chunk_index')} "
            f"source={item.metadata.get('source')}"
        )


if __name__ == "__main__":
    main()
