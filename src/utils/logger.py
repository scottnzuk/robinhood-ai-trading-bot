import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.config import LOG_LEVEL, LOG_DIR, MAX_LOG_SIZE_MB, LOG_BACKUP_COUNT

# Create log directory if it doesn't exist
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger('robinhood_bot')
logger.setLevel(LOG_LEVEL)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler
file_handler = RotatingFileHandler(
    filename=f'{LOG_DIR}/robinhood_bot.log',
    maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
    backupCount=LOG_BACKUP_COUNT
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions"""
    logger.error(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

# Set exception hook
sys.excepthook = log_exception

# Convenience functions
def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)
