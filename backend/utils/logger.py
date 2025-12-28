from loguru import logger
import sys
from pathlib import Path
from backend.config.settings import settings

# Create logs directory if it doesn't exist
Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

# Remove default handler
logger.remove()

# Add console handler
logger.add(
    sys.stdout,
    format="<green>{time: YYYY-MM-DD HH:mm:ss}</green> | <level>{level:  <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>: <cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)

# Add file handler
logger.add(
    settings.LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL,
    rotation="100 MB",
    retention="30 days",
    compression="zip"
)

__all__ = ["logger"]