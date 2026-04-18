from app.config import settings
from app.prompts.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE
from app.schemas import RetrievalResult


def _truncate_content(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def format_context(
    results: list[RetrievalResult],
    max_chunks: int | None = None,
    max_chars_per_chunk: int | None = None,
) -> str:
    """Render retrieved chunks into a prompt-friendly context block."""

    lines: list[str] = []
    chunk_limit = max_chunks or settings.default_context_max_chunks
    char_limit = max_chars_per_chunk or settings.default_context_max_chars_per_chunk
    for index, item in enumerate(results[:chunk_limit], start=1):
        filename = item.chunk.metadata.get("filename", "unknown")
        chunk_index = item.chunk.metadata.get("chunk_index", "unknown")
        score = f" score={item.score:.3f}" if item.score is not None else ""
        content = _truncate_content(item.chunk.content, char_limit)
        lines.append(f"[S{index}] filename={filename} chunk={chunk_index}{score}\n{content}")
    return "\n\n".join(lines)

def build_user_prompt(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int | None = None,
    max_chars_per_chunk: int | None = None,
) -> str:
    """Build the user prompt that carries context and answer constraints."""

    context = format_context(
        results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    return RAG_USER_TEMPLATE.format(context=context, question=question)


def build_messages(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int | None = None,
    max_chars_per_chunk: int | None = None,
) -> list[dict[str, str]]:
    """Build the final messages sent to the generation model."""

    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(
                question=question,
                results=results,
                max_chunks=max_chunks,
                max_chars_per_chunk=max_chars_per_chunk,
            ),
        },
    ]


def build_prompt(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int | None = None,
    max_chars_per_chunk: int | None = None,
) -> str:
    """Keep a plain-text preview path for debugging scripts."""

    messages = build_messages(
        question=question,
        results=results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    return "\n\n".join(f"{message['role'].upper()}:\n{message['content']}" for message in messages)
