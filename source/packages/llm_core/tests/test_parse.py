"""Tests for parse_risk_list — moved from demo fixtures."""

from llm_core import QuotedReviewRiskList, parse_risk_list
from llm_core.schemas.parse import parse_structured_model


def test_valid_object():
    result = parse_risk_list(
        '{"risks":[{"title":"t","category":"interaction","level":"medium",'
        '"rationale":"r","citations":[]}]}'
    )
    assert result.ok
    assert result.risk_count == 1


def test_fenced_json():
    result = parse_risk_list(
        '```json\n{"risks":[{"title":"t","category":"api","level":"high",'
        '"rationale":"r","citations":[]}]}\n```'
    )
    assert result.ok


def test_legacy_array():
    result = parse_risk_list(
        '[{"title":"t","category":"state_flow","level":"medium",'
        '"rationale":"r","citations":[]}]'
    )
    assert result.ok


def test_not_json():
    result = parse_risk_list("以下是风险分析")
    assert not result.ok
    assert result.error_stage == "json"


def test_bad_enum():
    result = parse_risk_list(
        '{"risks":[{"title":"x","category":"交互","level":"high","rationale":"y"}]}'
    )
    assert not result.ok
    assert result.error_stage == "schema"


def test_empty():
    result = parse_risk_list("")
    assert not result.ok
    assert result.error_stage == "empty"


def test_quoted_review_schema_requires_excerpt_for_each_citation():
    result = parse_structured_model(
        '{"risks":[{"title":"t","category":"api","level":"high",'
        '"rationale":"r","citations":[{"source_id":"chunk-api"}]}]}',
        QuotedReviewRiskList,
    )

    assert not result.ok
    assert result.error_stage == "schema"
