from app.prompts.rag_prompt import RAG_SYSTEM_PROMPT
from app.schemas import RetrievalResult


def format_context(results: list[RetrievalResult]) -> str:
    """Render retrieved chunks into a plain-text context block."""

    lines: list[str] = []
    for item in results:
        source = item.chunk.metadata.get("source", "unknown")
        lines.append(f"[source={source}] {item.chunk.content}")
    return "\n\n".join(lines)


def build_prompt(question: str, results: list[RetrievalResult]) -> str:
    """Build the final prompt string before an LLM call exists."""

    context = format_context(results)
    return f"{RAG_SYSTEM_PROMPT}\n\n上下文：\n{context}\n\n问题：{question}"
