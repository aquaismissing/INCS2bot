import json
import logging.config
import logging.handlers
from pathlib import Path


__all__ = ['get_logger']


def get_rotating_file_handler(name: str, logs_path: Path) -> logging.handlers.BaseRotatingHandler:
    logs_folder = Path(logs_path) / name.lower()
    if not logs_folder.exists():
        logs_folder.mkdir()

    # return logging.handlers.RotatingFileHandler(
    #     logs_folder / f'{name.lower()}.log',
    #     maxBytes=270 * 1024, backupCount=5  # each log file is <=270 KB, ~1.32 MB in total)
    # )
    return logging.handlers.TimedRotatingFileHandler(logs_folder / 'latest.log', when='midnight', backupCount=5)


def get_logger(name: str, logs_path: Path, config_path: str | Path):
    """Applies all the settings from a logging config, as well as a RotatingFileHandler (for per-logger logs output)."""

    logger = logging.getLogger(name)

    with open(config_path, encoding='utf-8') as f:
        logging_config = json.load(f)
    logging.config.dictConfig(logging_config)

    logging_config['formatters']['detailed']['fmt'] = logging_config['formatters']['detailed'].pop('format')
    detailed_formatter = logging.Formatter(**logging_config['formatters']['detailed'])

    logs_folder = Path(logs_path) / name.lower()
    if not logs_folder.exists():
        logs_folder.mkdir()

    file_handler = get_rotating_file_handler(name, logs_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    return logger
