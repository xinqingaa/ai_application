"""
定义最小问答流程使用的 Prompt 组装逻辑。

这个文件的重点是把 Prompt 从 service 和 client 中独立出来，保持输入结构
稳定可读。
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
    """把问题、检索上下文和工具结果组装成统一 Prompt。"""

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
