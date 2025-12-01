# Внешние зависимости
import logging
from logging.handlers import RotatingFileHandler
import sys


def setup_logger(
        name: str = __name__,
        level: str = "INFO",
        format_str: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        log_dir: str = 'logs',
        log_file: str = 'web_log'
) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    # Уровень
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Форматтер
    formatter = logging.Formatter(format_str)

    # Обработчик для stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    file_handler = RotatingFileHandler(
        filename=f'{log_dir}/{log_file}.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,  # храним 5 backup файлов
        encoding='utf-8'
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger