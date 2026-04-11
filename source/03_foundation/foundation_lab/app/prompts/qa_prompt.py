"""
Prompt helpers for the minimal QA flow.
"""

from __future__ import annotations

from collections.abc import Sequence


SYSTEM_PROMPT = (
    "You are the foundation_lab assistant. "
    "Answer clearly, stay within the provided context, and avoid inventing unsupported facts."
)


def format_qa_prompt(
    question: str,
    context_blocks: Sequence[str] | None = None,
    tool_result: str | None = None,
) -> str:
    context_text = "\n".join(f"- {item}" for item in (context_blocks or [])) or "- No extra context provided."
    tool_text = tool_result or "No tool result provided."
    return (
        f"System Instruction:\n{SYSTEM_PROMPT}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Tool Result:\n{tool_text}\n\n"
        f"User Question:\n{question}\n\n"
        "Answer Requirements:\n"
        "- Use concise language.\n"
        "- Separate explanation from assumptions.\n"
        "- If context is missing, say so explicitly."
    )
