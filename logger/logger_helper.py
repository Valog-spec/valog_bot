import logging.config
from logging import Logger

from logger.config.config import dict_config


def get_logger(name) -> Logger:
    """
    Создает и возвращает логгер с заданным именем, используя предустановленную конфигурацию

    Args:
        name (str): Имя логгера.
    Returns:
        Logger: Объект логгера, настроенный согласно конфигурации dict_config.
    """
    logging.config.dictConfig(dict_config)
    logger = logging.getLogger(name)
    return logger
