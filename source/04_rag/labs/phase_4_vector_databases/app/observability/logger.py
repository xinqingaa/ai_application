import logging


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Return a project logger with a simple default formatter."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("rag_lab")
