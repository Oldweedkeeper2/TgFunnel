import os

from loguru import logger

from config import LOG_DIR

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file_path = os.path.join(LOG_DIR, "app.log")

logger.add(
        log_file_path,
        rotation="10 MB",
        compression="zip",
        retention="10 days",
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        # level="INFO",
        level="DEBUG",  # DEBUG MODE

)
