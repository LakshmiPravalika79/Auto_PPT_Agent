"""
logger.py

Provides structured logging for debugging and demo clarity.
"""

import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("PPTAgent")