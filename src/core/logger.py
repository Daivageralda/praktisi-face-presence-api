import os
import logging

from pathlib import Path
from datetime import datetime


"""
Logger configuration for the Face Presence API.

This sets up a dual logging system that logs to both the console and a daily rotating log file
inside the 'logs' directory. The log level is dynamically set based on the DEBUG setting.

Usage:
    from src.core.logger import logger
    logger.info("This is a log message.")
"""
LOG_PATH = Path(__file__).resolve().parents[2] / "src/logs"
os.makedirs(LOG_PATH, exist_ok=True)

log_filename = f"{datetime.now():%Y-%m-%d}.log"
log_path = os.path.join(LOG_PATH, log_filename)

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("face-presence-api")
