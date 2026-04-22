from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    """Intermediate chunk shape before it becomes a canonical SourceChunk."""

    content: str
    start_index: int
    end_index: int


@dataclass(slots=True)
class SplitterConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")


def _trimmed_window(window: str, start_index: int) -> tuple[str, int, int]:
    left_trimmed = window.lstrip()
    leading_chars = len(window) - len(left_trimmed)
    trimmed = left_trimmed.rstrip()
    chunk_start = start_index + leading_chars
    chunk_end = chunk_start + len(trimmed)
    return trimmed, chunk_start, chunk_end


def _choose_breakpoint(window: str, chunk_size: int) -> int:
    min_breakpoint = max(chunk_size // 2, 1)
    separators = ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ")

    for separator in separators:
        position = window.rfind(separator)
        if position >= min_breakpoint:
            return position + len(separator)

    return len(window)


def split_text(text: str, config: SplitterConfig) -> list[TextChunk]:
    """Split text into overlapping windows while preferring paragraph boundaries."""

    if not text:
        return []

    chunks: list[TextChunk] = []
    start_index = 0
    text_length = len(text)

    while start_index < text_length:
        tentative_end = min(start_index + config.chunk_size, text_length)
        window = text[start_index:tentative_end]
        if tentative_end < text_length:
            breakpoint = _choose_breakpoint(window, config.chunk_size)
            tentative_end = start_index + breakpoint
            window = text[start_index:tentative_end]

        trimmed, chunk_start, chunk_end = _trimmed_window(window, start_index)
        if trimmed:
            chunks.append(
                TextChunk(
                    content=trimmed,
                    start_index=chunk_start,
                    end_index=chunk_end,
                )
            )

        if tentative_end >= text_length:
            break

        start_index = max(tentative_end - config.chunk_overlap, start_index + 1)

    return chunks
