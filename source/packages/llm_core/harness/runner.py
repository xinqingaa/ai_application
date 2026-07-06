"""Batch calling harness built on ReliableLLMService."""

from __future__ import annotations

from typing import Any

from llm_core.config import LLMResponse
from llm_core.harness.cases import HarnessCase, HarnessRunConfig
from llm_core.harness.records import HarnessRunRecord, HarnessSummary
from llm_core.reliability import ReliableCallResult, ReliableLLMService
from llm_core.structured import StructuredLLMResponse


class LLMCallingHarness:
    """Run a stable case set and turn every call into a comparable record."""

    def __init__(self, service: ReliableLLMService) -> None:
        self._service = service

    def run_cases(
        self,
        cases: list[HarnessCase],
        config: HarnessRunConfig,
    ) -> tuple[list[HarnessRunRecord], HarnessSummary]:
        records = [self.run_case(case, config) for case in cases]
        return records, HarnessSummary.from_records(records)

    def run_case(self, case: HarnessCase, config: HarnessRunConfig) -> HarnessRunRecord:
        if config.structured:
            result = self._service.chat_structured(
                case.messages,
                config.config_ref,
                retry_policy=config.retry_policy,
                degradation_policy=config.degradation_policy,
                structured_mode=config.structured_mode,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        else:
            result = self._service.chat(
                case.messages,
                config.config_ref,
                retry_policy=config.retry_policy,
                degradation_policy=config.degradation_policy,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        return _record_from_result(case, result)


def _record_from_result(case: HarnessCase, result: ReliableCallResult[Any]) -> HarnessRunRecord:
    report = result.report
    latency_ms = sum(attempt.latency_ms for attempt in report.attempts)
    if not result.ok or result.output is None:
        return HarnessRunRecord(
            case_id=case.case_id,
            title=case.title,
            status="failed",
            config_ref=report.final_config_ref,
            latency_ms=latency_ms,
            error_code=report.final_error_code,
            message=report.final_message,
            attempt_count=report.attempt_count,
            degraded=report.degraded,
        )

    output = result.output
    if isinstance(output, StructuredLLMResponse):
        llm = output.llm
        parse = output.parse
        return HarnessRunRecord(
            case_id=case.case_id,
            title=case.title,
            status="success",
            config_ref=report.final_config_ref,
            model=llm.model,
            content_preview=_preview(llm.content),
            parse_ok=parse.ok,
            risk_count=parse.risk_count,
            latency_ms=latency_ms or llm.latency_ms,
            total_tokens=llm.usage.total_tokens if llm.usage else None,
            attempt_count=report.attempt_count,
            degraded=report.degraded,
        )

    if isinstance(output, LLMResponse):
        return HarnessRunRecord(
            case_id=case.case_id,
            title=case.title,
            status="success",
            config_ref=report.final_config_ref,
            model=output.model,
            content_preview=_preview(output.content),
            parse_ok=None,
            risk_count=None,
            latency_ms=latency_ms or output.latency_ms,
            total_tokens=output.usage.total_tokens if output.usage else None,
            attempt_count=report.attempt_count,
            degraded=report.degraded,
        )

    return HarnessRunRecord(
        case_id=case.case_id,
        title=case.title,
        status="success",
        config_ref=report.final_config_ref,
        content_preview=_preview(str(output)),
        latency_ms=latency_ms,
        attempt_count=report.attempt_count,
        degraded=report.degraded,
    )


def _preview(text: str, *, limit: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."
