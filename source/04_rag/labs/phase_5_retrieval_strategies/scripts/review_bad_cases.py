from __future__ import annotations

import json
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


def load_cases() -> list[dict[str, object]]:
    path = PROJECT_ROOT / "evals" / "retrieval_bad_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
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

    cases = load_cases()
    for case in cases:
        question = str(case["question"])
        metadata_filter = case.get("metadata_filter")
        print("=" * 72)
        print(f"Case: {case['name']}")
        print(f"Question: {question}")
        print(f"Why it matters: {case['why']}")
        if metadata_filter:
            print(f"Filter: {metadata_filter}")

        strategy_names = ["similarity", "threshold", "mmr"]
        for strategy_name in strategy_names:
            config = RetrievalStrategyConfig(
                strategy_name=strategy_name,
                candidate_k=settings.default_retrieval_candidate_k,
                score_threshold=(
                    settings.default_retrieval_score_threshold
                    if strategy_name == "threshold"
                    else None
                ),
                mmr_lambda=settings.default_retrieval_mmr_lambda,
                metadata_filter=metadata_filter if isinstance(metadata_filter, dict) else None,
            )
            retriever = ChromaRetriever(store=store, provider=provider, config=config)
            results = retriever.retrieve(question, top_k=settings.default_top_k)
            print()
            print(f"[{strategy_name}] {len(results)} result(s)")
            if not results:
                print("- no results")
                continue
            for item in results[: settings.default_top_k]:
                print(
                    f"- score={item.score:.3f} "
                    f"filename={item.chunk.metadata.get('filename')} "
                    f"chunk={item.chunk.metadata.get('chunk_index')}"
                )


if __name__ == "__main__":
    main()
