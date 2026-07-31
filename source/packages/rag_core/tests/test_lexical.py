from __future__ import annotations

from dataclasses import replace

import pytest

from rag_core import LexicalAnalyzer, LexicalConfig, QueryOperator


def test_analyzer_segments_chinese_and_removes_question_fillers() -> None:
    analyzer = LexicalAnalyzer()

    analysis = analyzer.analyze_query("source_channel 什么时候必填？")

    assert "什么" not in analysis.terms
    assert "时候" not in analysis.terms
    assert "必填" in analysis.terms
    assert "source_channel" in analysis.terms
    assert "techidsourcechannel" in analysis.terms
    assert analysis.query_operator is QueryOperator.OR
    assert " OR " in (analysis.websearch_query or "")


def test_document_analysis_preserves_frequency_and_query_deduplicates() -> None:
    analyzer = LexicalAnalyzer()

    document = analyzer.analyze_document("售后规则说明售后入口。")
    query = analyzer.analyze_query("售后 售后")

    assert document.terms.count("售后") == 2
    assert query.terms.count("售后") == 1


def test_technical_identifier_sentinel_is_stable_across_case() -> None:
    analyzer = LexicalAnalyzer()

    lower = analyzer.analyze_query("source_channel")
    upper = analyzer.analyze_query("SOURCE_CHANNEL")

    assert lower.terms == upper.terms
    assert lower.config_ref == upper.config_ref


def test_and_query_has_no_or_operator() -> None:
    baseline = LexicalConfig()
    config = replace(baseline, query_operator=QueryOperator.AND)
    analysis = LexicalAnalyzer(config).analyze_query("申请售后")

    assert analysis.query_operator is QueryOperator.AND
    assert " OR " not in (analysis.websearch_query or "")
    assert config.config_ref == baseline.config_ref
    assert config.retriever_config_ref != baseline.retriever_config_ref


def test_config_identity_changes_with_effective_policy() -> None:
    baseline = LexicalConfig()
    changed = replace(baseline, stop_terms=(*baseline.stop_terms, "规则"))

    assert baseline.config_ref != changed.config_ref


@pytest.mark.parametrize("text", ["", "   ", "！！！"])
def test_analyzer_rejects_text_without_terms(text: str) -> None:
    analyzer = LexicalAnalyzer()

    with pytest.raises(ValueError, match="不能为空|可检索词项"):
        analyzer.analyze_query(text)
