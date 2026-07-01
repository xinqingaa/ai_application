from llm_core import ContextSource, build_review_context, estimate_tokens, format_context_source


def test_build_review_context_keeps_traceable_evidence():
    source = ContextSource(
        source_id="EV-1",
        title="接口说明",
        content="售后接口 v2 需要 order_id。",
        priority=80,
    )

    context = build_review_context(
        requirement_text="订单详情页新增申请售后按钮。",
        sources=[source],
        token_budget=500,
    )

    assert context.included_source_ids == ["EV-1"]
    assert context.dropped_source_ids == []
    assert "[EV-1] 接口说明" in context.evidence_block
    assert "售后接口 v2" in context.to_prompt_variables()["evidence_block"]
    assert context.estimated_tokens > 0


def test_build_review_context_drops_low_priority_source_when_budget_is_limited():
    high = ContextSource(source_id="high", content="must keep", priority=90)
    low = ContextSource(source_id="low", content="word " * 200, priority=10)
    budget = (
        estimate_tokens("short requirement")
        + estimate_tokens(format_context_source(high))
        + 1
    )

    context = build_review_context(
        requirement_text="short requirement",
        sources=[low, high],
        token_budget=budget,
    )

    assert context.included_source_ids == ["high"]
    assert context.dropped_source_ids == ["low"]
    assert context.dropped_sources[0].reason == "token_budget_exceeded"


def test_build_review_context_deduplicates_sources_by_priority():
    older = ContextSource(source_id="EV-1", content="old content", priority=10)
    newer = ContextSource(source_id="EV-1", content="new content", priority=90)

    context = build_review_context(
        requirement_text="requirement",
        sources=[older, newer],
        token_budget=500,
    )

    assert context.included_source_ids == ["EV-1"]
    assert "new content" in context.evidence_block
    assert "old content" not in context.evidence_block


def test_build_review_context_uses_no_evidence_placeholder():
    context = build_review_context(
        requirement_text="只有一句需求。",
        sources=[],
        token_budget=100,
    )

    assert context.included_sources == []
    assert "无可用证据" in context.evidence_block
