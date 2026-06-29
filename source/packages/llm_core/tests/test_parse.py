"""Tests for parse_risk_list — moved from demo fixtures."""

from llm_core import parse_risk_list


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
