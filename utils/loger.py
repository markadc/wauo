import sys

from loguru import logger


class Loger:
    def __init__(self, level="INFO", file=None):
        self.__logger = logger
        self.remove()
        self.add(file or sys.stdout, level=level)

    def __getattr__(self, item):
        return getattr(self.__logger, item)

    def debug(self, msg, *args, **kwargs):
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.__logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.__logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.__logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.__logger.critical(msg, *args, **kwargs)
