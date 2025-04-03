from pathlib import Path
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Loading .env file from: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("Successfully loaded .env file")
else:
    logger.warning(".env file not found")

# Debug print all environment variables
logger.info("Environment variables:")
for key, value in os.environ.items():
    if "API" in key or "KEY" in key:  # Only show relevant sensitive keys
        logger.info(f"{key}={value[:3]}...{value[-3:] if len(value) > 6 else ''}")

# Logging configuration
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_LOG_SIZE_MB = int(os.getenv('MAX_LOG_SIZE_MB', '10'))
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

# 1Password Credentials
OP_SERVICE_ACCOUNT_NAME = os.getenv('OP_SERVICE_ACCOUNT_NAME', '')
OP_SERVICE_ACCOUNT_TOKEN = os.getenv('OP_SERVICE_ACCOUNT_TOKEN', '')
OP_VAULT_NAME = os.getenv('OP_VAULT_NAME', '')
OP_ITEM_NAME = os.getenv('OP_ITEM_NAME', '')

# Credentials
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
REQUESTY_API_KEY = os.getenv('REQUESTY_API_KEY', '')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
ROBINHOOD_USERNAME = os.getenv('ROBINHOOD_USERNAME', '')
ROBINHOOD_PASSWORD = os.getenv('ROBINHOOD_PASSWORD', '')
ROBINHOOD_MFA_SECRET = os.getenv('ROBINHOOD_MFA_SECRET', '')

# Basic config parameters
MODE = os.getenv('MODE', 'test')
RUN_INTERVAL_SECONDS = int(os.getenv('RUN_INTERVAL_SECONDS', '60'))
TRADING_INTERVAL_MINUTES = int(os.getenv('TRADING_INTERVAL_MINUTES', '15'))
MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', '10'))

# Robinhood config parameters
TRADE_EXCEPTIONS = []
WATCHLIST_NAMES = []
WATCHLIST_OVERVIEW_LIMIT = 5
PORTFOLIO_LIMIT = 5
MIN_SELLING_AMOUNT_USD = 1.0
MAX_SELLING_AMOUNT_USD = 10.0
MIN_BUYING_AMOUNT_USD = 1.0
MAX_BUYING_AMOUNT_USD = 10.0

# AI config params
DEFAULT_AI_PROVIDER = os.getenv('DEFAULT_AI_PROVIDER', 'requesty')
DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'parasail/parasail-gemma3-27b-it')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')

# Verify critical credentials
if not REQUESTY_API_KEY:
    logger.error("REQUESTY_API_KEY not found in environment variables")
if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY not found in environment variables")