import sys

from loguru import logger


class Loger:
    def __init__(self, level="INFO", file=None):
        self.__logger = logger
        self.remove()
        self.add(file or sys.stdout, level=level)  # 设置日志级别

    def __getattr__(self, item):
        return getattr(self.__logger, item)
