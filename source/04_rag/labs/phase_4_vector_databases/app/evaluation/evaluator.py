from app.schemas import EvalSample


def summarize_samples(samples: list[EvalSample]) -> dict[str, int]:
    """Minimal placeholder to keep the evaluation package concrete."""

    return {
        "total_samples": len(samples),
        "samples_with_expected_sources": sum(
            1 for sample in samples if sample.expected_sources
        ),
    }
