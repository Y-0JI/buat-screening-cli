import sys
from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}")
    logger.add("logs/screening.log", level="DEBUG", rotation="10 MB", retention=7)
