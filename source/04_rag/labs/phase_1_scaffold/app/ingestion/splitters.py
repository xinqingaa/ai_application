from dataclasses import dataclass


@dataclass(slots=True)
class SplitterConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50


def split_text(text: str, config: SplitterConfig) -> list[str]:
    """A temporary pure-Python splitter used until real splitters are wired in."""

    if not text:
        return []

    step = max(config.chunk_size - config.chunk_overlap, 1)
    return [text[index : index + config.chunk_size] for index in range(0, len(text), step)]
