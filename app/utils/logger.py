import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a structured JSON logger configured for Palette and CloudWatch.
    Logs are emitted in JSON format with timestamp and level keys.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        # Prevent adding multiple handlers if already configured
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonLogFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        import datetime

        log_record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # Include exception info if present
        if record.exc_info:
            import traceback

            log_record["exception"] = "".join(traceback.format_exception(*record.exc_info))

        # Include extra keys if any
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_record.update(record.extra)

        return json.dumps(log_record)
