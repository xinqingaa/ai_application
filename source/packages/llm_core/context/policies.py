"""Context policy presets for review-oriented tasks."""

from __future__ import annotations

from llm_core.context.types import ContextBuildPolicy


def list_context_policy_names() -> tuple[str, ...]:
    return ("minimal", "full_context", "balanced", "evidence_first", "tight_budget", "agent_summary_only")


def get_context_policy(name: str = "balanced") -> ContextBuildPolicy:
    """Return a fresh policy preset for demos and tests."""

    policies: dict[str, ContextBuildPolicy] = {
        "minimal": ContextBuildPolicy(
            name="minimal",
            token_budget=500,
            section_budgets={
                "requirement": 500,
                "evidence": 0,
                "history": 0,
                "agent_summary": 0,
                "other": 0,
            },
            allow_compression=False,
            max_source_tokens=None,
            include_source_types={"requirement"},
        ),
        "full_context": ContextBuildPolicy(
            name="full_context",
            token_budget=2200,
            section_budgets={
                "requirement": 600,
                "evidence": 1000,
                "history": 300,
                "agent_summary": 220,
                "other": 80,
            },
            allow_compression=False,
            max_source_tokens=None,
        ),
        "balanced": ContextBuildPolicy(
            name="balanced",
            token_budget=1400,
            section_budgets={
                "requirement": 450,
                "evidence": 650,
                "history": 160,
                "agent_summary": 120,
                "other": 20,
            },
            allow_compression=True,
            max_source_tokens=180,
        ),
        "evidence_first": ContextBuildPolicy(
            name="evidence_first",
            token_budget=1300,
            section_budgets={
                "requirement": 420,
                "evidence": 760,
                "history": 60,
                "agent_summary": 50,
                "other": 10,
            },
            allow_compression=True,
            max_source_tokens=180,
        ),
        "tight_budget": ContextBuildPolicy(
            name="tight_budget",
            token_budget=620,
            section_budgets={
                "requirement": 220,
                "evidence": 300,
                "history": 50,
                "agent_summary": 40,
                "other": 10,
            },
            allow_compression=True,
            max_source_tokens=90,
            min_compression_tokens=36,
        ),
        "agent_summary_only": ContextBuildPolicy(
            name="agent_summary_only",
            token_budget=800,
            section_budgets={
                "requirement": 420,
                "evidence": 0,
                "history": 0,
                "agent_summary": 340,
                "other": 40,
            },
            allow_compression=True,
            max_source_tokens=160,
            include_source_types={"agent_summary", "tool_result", "other"},
        ),
    }
    if name not in policies:
        available = ", ".join(list_context_policy_names())
        raise KeyError(f"未知 context policy {name!r}，可选：{available}")
    return policies[name]
