import sys
from loguru import logger


def _terminal_filter(record):
    if record["name"].startswith("app.tools"):
        return record["level"].no > 40
    return True


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, filter=_terminal_filter,
               format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}")
    logger.add("logs/screening.log", level="DEBUG", rotation="10 MB", retention=7)
