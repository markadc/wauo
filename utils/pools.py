import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from functools import partial
from typing import Callable

from loguru import logger


class BasePool(ABC):
    """线程池基类"""

    def __init__(self, speed=5, limit: int = None):
        self.speed = speed
        self.pool = ThreadPoolExecutor(max_workers=self.speed)
        self.count = 0
        self.max_count = limit or speed

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
    def todo(self, func: Callable, *args, **kwargs):
        pass

    def todos(self, func, *some):
        for args in zip(*some):
            self.todo(func, *args)


class WaitPool(BasePool):
    """需要等待同一批的线程全部结束后，才能分配下一批新线程"""

    def todo(self, func: Callable, *args, **kwargs):
        """核心"""
        if self.count >= self.max_count:
            self.pool.shutdown()
            self.pool = ThreadPoolExecutor(max_workers=self.speed)
            self.count = 0
        future = self.pool.submit(func, *args, **kwargs)
        self.count += 1
        future.add_done_callback(partial(self.done, func.__name__))


class SpeedPool(BasePool):
    """当池子里有任意线程结束时，新的线程可以立刻分配"""

    def __init__(self, speed=5, limit: int = None):
        super().__init__(speed, limit)
        self.add_task = threading.Condition()
        self.running_futures = []

    def todo(self, func, *args, **kwargs):
        """核心"""
        with self.add_task:
            while self.count >= self.max_count:
                # logger.info('wait......{}'.format(args))
                self.add_task.wait()

            future = self.pool.submit(func, *args, **kwargs)
            self.count += 1
            self.running_futures.append(future)
            future.add_done_callback(partial(self.done, func.__name__))

    def done(self, func_name: str, future: Future):
        """线程的回调函数"""
        super().done(func_name, future)

        with self.add_task:
            self.count -= 1
            self.running_futures.remove(future)
            self.add_task.notify()

    def running(self):
        """是否还有任务在运行"""
        for f in self.running_futures:
            if f.running():
                return True
        return False
