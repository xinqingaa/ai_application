"""Stable chunk identity derived from document, policy and source spans."""

from __future__ import annotations

import hashlib
import json

from rag_core.chunking.models import ChunkKind, ChunkSourceSpan


def build_chunk_id(
    *,
    document_id: str,
    document_version: str,
    policy_fingerprint: str,
    kind: ChunkKind,
    text: str,
    source_spans: tuple[ChunkSourceSpan, ...],
) -> str:
    payload = {
        "document_id": document_id,
        "document_version": document_version,
        "policy_fingerprint": policy_fingerprint,
        "kind": kind.value,
        "text": text,
        "source_spans": [
            {
                "element_id": span.element_id,
                "start_char": span.start_char,
                "end_char": span.end_char,
            }
            for span in source_spans
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"chunk_{hashlib.sha256(encoded).hexdigest()[:16]}"
