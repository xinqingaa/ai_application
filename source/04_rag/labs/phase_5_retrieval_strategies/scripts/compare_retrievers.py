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
    parser = ArgumentParser(description="Compare Phase 5 retriever strategies.")
    parser.add_argument(
        "question",
        nargs="?",
        default="Where do we keep source path and chunk index metadata?",
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
    metadata_filter = {"filename": args.filename} if args.filename else None

    strategies = [
        RetrievalStrategyConfig(
            strategy_name="similarity",
            candidate_k=settings.default_retrieval_candidate_k,
            metadata_filter=metadata_filter,
        ),
        RetrievalStrategyConfig(
            strategy_name="threshold",
            candidate_k=settings.default_retrieval_candidate_k,
            score_threshold=settings.default_retrieval_score_threshold,
            metadata_filter=metadata_filter,
        ),
        RetrievalStrategyConfig(
            strategy_name="mmr",
            candidate_k=settings.default_retrieval_candidate_k,
            mmr_lambda=settings.default_retrieval_mmr_lambda,
            metadata_filter=metadata_filter,
        ),
    ]

    print(f"Question: {args.question}")
    if metadata_filter:
        print(f"Filter: {metadata_filter}")

    for config in strategies:
        retriever = ChromaRetriever(store=store, provider=provider, config=config)
        results = retriever.retrieve(args.question, top_k=settings.default_top_k)
        print()
        print(
            f"[{config.strategy_name}] "
            f"candidate_k={config.candidate_k} "
            f"threshold={config.score_threshold} "
            f"mmr_lambda={config.mmr_lambda}"
        )
        if not results:
            print("- no results")
            continue
        for item in results:
            preview = item.chunk.content.replace("\n", " ")[:84]
            print(
                f"- score={item.score:.3f} "
                f"filename={item.chunk.metadata.get('filename')} "
                f"chunk={item.chunk.metadata.get('chunk_index')}"
            )
            print(f"  preview={preview}")


if __name__ == "__main__":
    main()
