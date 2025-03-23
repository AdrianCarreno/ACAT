import logging
import os
import sys

from loguru import logger


class PropagateHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)


# Re-add the stderr handler with the appropriate level
log_level = os.getenv("LOG_LEVEL", logging.WARNING)
logger.remove()
logger.add(sys.stderr, level=log_level)

# Add a handler to propagate the logs to the root logger
logger.add(PropagateHandler(), format="{message}")
