"""Shared fixtures and Chunk contract for retrieval-route comparisons."""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from rag_core import (
    ChunkPolicy,
    ChunkStrategy,
    EvidenceEligibility,
    SourceRole,
    chunk_document,
    load_document,
)

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
DOCUMENT_PATH = REPO_ROOT / "review_assistant/fixtures/v0/ingestion/order_rules.md"
QUERIES_PATH = (
    REPO_ROOT / "review_assistant/fixtures/v0/retrieval/retrieval_queries.json"
)


def load_workspace_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def load_query_payload(path: Path = QUERIES_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_retrieval_chunks():
    document = load_document(
        DOCUMENT_PATH,
        document_id="KR-ORDER-STATE",
        document_version="1.0.0",
        source_role=SourceRole.REFERENCE_KNOWLEDGE,
        evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
        metadata={"knowledge_scope": "after_sale"},
    ).document
    result = chunk_document(
        document,
        ChunkPolicy(
            name="rag_retrieval_structure_aware",
            version="1.0.0",
            strategy=ChunkStrategy.STRUCTURE_AWARE,
            max_tokens=48,
        ),
    )
    return result.retrieval_chunks
