import hashlib


def stable_document_id(source: str) -> str:
    """Generate a stable document id from the source path or URI."""

    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def stable_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    """Generate a stable chunk id that survives repeated indexing."""

    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    return f"{document_id}:{chunk_index}:{digest}"
