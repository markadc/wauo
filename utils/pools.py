import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future, wait as _wait
from functools import partial
from typing import Callable

from loguru import logger


class BasePool(ABC):
    """线程池基类"""

    def __init__(self, speed=10, limit: int = None):
        self.speed = speed
        self.pool = ThreadPoolExecutor(max_workers=self.speed)
        self.count = 0
        self.max_count = limit or speed
        self.running_futures = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self, wait=True, cancel_futures=False):
        """释放资源"""
        self.pool.shutdown(wait=wait, cancel_futures=cancel_futures)

    def done(self, func_name: str, future: Future):
        """线程的回调函数"""
        try:
            future.result()
        except Exception as e:
            logger.error("{} => {}".format(func_name, e))

    @abstractmethod
    def add(self, func: Callable, *args, **kwargs):
        pass

    def adds(self, func, *some):
        for args in zip(*some):
            self.add(func, *args)

    def record(self, func: Callable, *args, **kwargs):
        future = self.pool.submit(func, *args, **kwargs)
        self.count += 1
        self.running_futures.append(future)
        return future

    def block(self):
        """阻塞，等待所有任务完成"""
        _wait(self.running_futures)

    def is_running(self):
        """是否还有任务在运行"""
        for f in self.running_futures:
            if f.running():
                return True
        return False


class PoolWait(BasePool):
    """需要等待同一批的线程全部结束后，才能分配下一批新线程"""

    def add(self, func: Callable, *args, **kwargs):
        """核心"""
        if self.count >= self.max_count:
            _wait(self.running_futures)
            self.count = 0
        future = self.record(func, *args, **kwargs)
        future.add_done_callback(partial(self.done, func.__name__))


class PoolMan(BasePool):
    """当池子里有任意线程结束时，可以立刻分配新的线程"""

    def __init__(self, speed=10, limit: int = None):
        super().__init__(speed, limit)
        self.add_task = threading.Condition()
        self.running_futures = []

    def add(self, func, *args, **kwargs):
        """核心"""
        with self.add_task:
            while self.count >= self.max_count:
                # logger.info('wait......{}'.format(args))
                self.add_task.wait()
            future = self.record(func, *args, **kwargs)
            future.add_done_callback(partial(self.done, func.__name__))

    def done(self, func_name: str, future: Future):
        """线程的回调函数"""
        super().done(func_name, future)

        with self.add_task:
            self.count -= 1
            self.running_futures.remove(future)
            self.add_task.notify()
