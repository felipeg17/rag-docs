import logging
import sys

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

logger = logging.getLogger("rag-docs")
logger.setLevel(LOG_LEVEL)

if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False
