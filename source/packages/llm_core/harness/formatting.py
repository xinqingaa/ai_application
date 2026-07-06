"""Terminal formatting helpers for harness demos."""

from __future__ import annotations

from llm_core.harness.records import HarnessRunRecord, HarnessSummary


def format_records_table(records: list[HarnessRunRecord]) -> str:
    rows = [
        ("case_id", "status", "parse", "degraded", "attempts", "latency_ms", "error"),
    ]
    for record in records:
        rows.append(
            (
                record.case_id,
                record.status,
                _dash(_parse_label(record)),
                str(record.degraded).lower(),
                str(record.attempt_count),
                f"{record.latency_ms:.1f}",
                record.error_code.value if record.error_code else "-",
            )
        )
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    lines = []
    for row_index, row in enumerate(rows):
        line = "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        lines.append(line)
        if row_index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)


def format_summary(summary: HarnessSummary) -> str:
    error_text = ", ".join(f"{code}={count}" for code, count in sorted(summary.error_counts.items())) or "-"
    return "\n".join(
        [
            f"total: {summary.total}",
            f"success: {summary.success_count}",
            f"failed: {summary.failed_count}",
            f"parse_success_rate: {summary.parse_success_rate:.0%}",
            f"degraded: {summary.degraded_count}",
            f"average_latency_ms: {summary.average_latency_ms:.1f}",
            f"errors: {error_text}",
        ]
    )


def _parse_label(record: HarnessRunRecord) -> str | None:
    if record.parse_ok is None:
        return None
    return "ok" if record.parse_ok else "fail"


def _dash(value: str | None) -> str:
    return value if value else "-"
