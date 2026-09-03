from __future__ import annotations

import json

from llm_core import ContextSource, LLMResponse, build_review_context, get_context_policy
from llm_core.config import TokenUsage
from llm_core.schemas.parse import parse_structured_model
from llm_core.structured import StructuredLLMResponse
from rag_core import (
    CitationSupportInput,
    CitationSupportValidationStatus,
    CitationSupportVerdict,
    QuoteLocationStatus,
    validate_citation_support,
)


class FakeSupportClient:
    def __init__(self, payload: dict | str) -> None:
        self.payload = payload
        self.calls = []

    def chat_structured(self, messages, config_ref, *, response_model, **kwargs):
        self.calls.append((messages, config_ref, response_model, kwargs))
        content = (
            self.payload
            if isinstance(self.payload, str)
            else json.dumps(self.payload, ensure_ascii=False)
        )
        return StructuredLLMResponse(
            llm=LLMResponse(
                content=content,
                raw_response={},
                usage=TokenUsage(
                    prompt_tokens=100,
                    completion_tokens=20,
                    total_tokens=120,
                ),
                latency_ms=12.0,
                provider="fake-provider",
                model="fake-model",
                config_ref=config_ref,
            ),
            parse=parse_structured_model(content, response_model),
            structured_mode=kwargs["structured_mode"],
            request_params=kwargs,
        )


def _context(*sources: ContextSource):
    return build_review_context(
        requirement_text="订单详情页新增申请售后入口。",
        sources=sources,
        policy=get_context_policy("full_context"),
    )


def _source(source_id: str, content: str) -> ContextSource:
    return ContextSource(
        source_id=source_id,
        content=content,
        source_type="evidence",
        title="售后接口规则",
        metadata={"source_locators": "markdown, lines=8-10"},
    )


def _input(claim_id: str, source_id: str, excerpt: str) -> CitationSupportInput:
    return CitationSupportInput(
        claim_id=claim_id,
        claim_text="现行售后接口 v2 的所有请求都必须提供 source_channel。",
        source_id=source_id,
        excerpt=excerpt,
    )


def test_located_quotes_are_judged_once_and_only_supported_becomes_verified():
    excerpt = "请求必须提供 source_channel。"
    context = _context(
        _source("support", f"现行 v2 对全部入口生效。{excerpt}"),
        _source("unrelated", f"以下只描述营销活动曝光，不适用于售后。{excerpt}"),
        _source(
            "contradicted",
            f"以下是已废弃的 v1 规则：{excerpt}现行 v2 允许省略该字段。",
        ),
        _source(
            "indeterminate",
            f"部分售后请求适用以下规则，具体入口范围未记录：{excerpt}",
        ),
        _source("missing", "现行 v2 对全部入口生效。"),
    )
    client = FakeSupportClient(
        {
            "judgments": [
                {
                    "claim_id": "support",
                    "verdict": "supported",
                    "reason": "现行规则直接要求该字段。",
                },
                {
                    "claim_id": "unrelated",
                    "verdict": "unrelated",
                    "reason": "该句属于营销活动范围。",
                },
                {
                    "claim_id": "contradicted",
                    "verdict": "contradicted",
                    "reason": "该句属于废弃规则，现行规则相反。",
                },
                {
                    "claim_id": "indeterminate",
                    "verdict": "indeterminate",
                    "reason": "资料没有说明是否覆盖全部请求。",
                },
            ]
        }
    )

    result = validate_citation_support(
        context,
        (
            _input("support", "support", excerpt),
            _input("unrelated", "unrelated", excerpt),
            _input("contradicted", "contradicted", excerpt),
            _input("indeterminate", "indeterminate", excerpt),
            _input("missing", "missing", excerpt),
        ),
        client=client,  # type: ignore[arg-type]
    )

    assert result.report.status is CitationSupportValidationStatus.COMPLETED
    assert result.report.model_call_count == 1
    assert result.report.located_count == 4
    assert result.report.quote_not_found_count == 1
    assert [check.verdict for check in result.checks[:4]] == [
        CitationSupportVerdict.SUPPORTED,
        CitationSupportVerdict.UNRELATED,
        CitationSupportVerdict.CONTRADICTED,
        CitationSupportVerdict.INDETERMINATE,
    ]
    assert result.checks[4].location_status is QuoteLocationStatus.QUOTE_NOT_FOUND
    assert [item.claim_id for item in result.verified_citations] == ["support"]
    assert result.report.usage is not None
    assert result.report.usage.total_tokens == 120


def test_whitespace_and_nfkc_are_normalized_without_semantic_rewriting():
    content = "接口规则：请求\n必须提供 ｓｏｕｒｃｅ＿ｃｈａｎｎｅｌ。"
    context = _context(_source("support", content))
    client = FakeSupportClient(
        {
            "judgments": [
                {
                    "claim_id": "support",
                    "verdict": "supported",
                    "reason": "引文直接支持。",
                }
            ]
        }
    )

    result = validate_citation_support(
        context,
        (
            _input(
                "support",
                "support",
                "请求 必须提供 source_channel。",
            ),
        ),
        client=client,  # type: ignore[arg-type]
    )

    check = result.checks[0]
    assert check.location_status is QuoteLocationStatus.LOCATED
    assert check.char_start is not None
    assert check.char_end is not None
    assert content[check.char_start : check.char_end].startswith("请求")


def test_ambiguous_quote_is_visible_and_does_not_call_model():
    excerpt = "请求必须提供 source_channel。"
    context = _context(_source("duplicate", f"{excerpt}\n{excerpt}"))
    client = FakeSupportClient({"judgments": []})

    result = validate_citation_support(
        context,
        (_input("duplicate", "duplicate", excerpt),),
        client=client,  # type: ignore[arg-type]
    )

    assert result.checks[0].location_status is QuoteLocationStatus.AMBIGUOUS_QUOTE
    assert result.checks[0].match_count == 2
    assert result.report.model_call_count == 0
    assert client.calls == []


def test_unallowed_source_and_missing_excerpt_are_not_judged():
    context = _context(_source("allowed", "请求必须提供 source_channel。"))
    client = FakeSupportClient({"judgments": []})

    result = validate_citation_support(
        context,
        (
            _input("outside", "outside", "请求必须提供 source_channel。"),
            _input("empty", "allowed", ""),
        ),
        client=client,  # type: ignore[arg-type]
    )

    assert [check.location_status for check in result.checks] == [
        QuoteLocationStatus.SOURCE_NOT_ALLOWED,
        QuoteLocationStatus.MISSING_EXCERPT,
    ]
    assert result.report.model_call_count == 0


def test_invalid_judgment_identity_does_not_become_supported():
    excerpt = "请求必须提供 source_channel。"
    context = _context(_source("support", excerpt))
    client = FakeSupportClient(
        {
            "judgments": [
                {
                    "claim_id": "different",
                    "verdict": "supported",
                    "reason": "错误映射。",
                }
            ]
        }
    )

    result = validate_citation_support(
        context,
        (_input("support", "support", excerpt),),
        client=client,  # type: ignore[arg-type]
    )

    assert result.report.status is CitationSupportValidationStatus.JUDGMENT_SET_INVALID
    assert result.verified_citations == ()
    assert result.checks[0].verdict is None


def test_structured_failure_is_visible_and_does_not_become_indeterminate():
    excerpt = "请求必须提供 source_channel。"
    context = _context(_source("support", excerpt))
    client = FakeSupportClient("not json")

    result = validate_citation_support(
        context,
        (_input("support", "support", excerpt),),
        client=client,  # type: ignore[arg-type]
    )

    assert result.report.status is (
        CitationSupportValidationStatus.STRUCTURED_OUTPUT_INVALID
    )
    assert result.report.parse_error_stage == "json"
    assert result.checks[0].verdict is None
    assert result.verified_citations == ()
