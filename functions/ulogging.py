import json
import logging.config
import logging.handlers
from pathlib import Path


__all__ = ['setup_logging']


def setup_logging(logger: logging.Logger, logs_path: str | Path, config_path: str | Path):
    """Applies all the settings from a logging config, as well as a RotatingFileHandler (for per-logger logs output)."""

    with open(config_path, encoding='utf-8') as f:
        logging_config = json.load(f)
    logging.config.dictConfig(logging_config)

    logging_config['formatters']['detailed']['fmt'] = logging_config['formatters']['detailed'].pop('format')
    detailed_formatter = logging.Formatter(**logging_config['formatters']['detailed'])

    logs_folder = Path(logs_path) / logger.name.lower()
    if not logs_folder.exists():
        logs_folder.mkdir()

    file_handler = logging.handlers.RotatingFileHandler(
        Path(logs_path) / logger.name.lower() / f'{logger.name.lower()}.log',
        maxBytes=10000, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
