from concurrent.futures import ThreadPoolExecutor, Future
from functools import partial
from threading import Event
from typing import Callable

from loguru import logger


class PoolManager:
    def __init__(self, speed=5, limit: int = None):
        """
        池子里所有的线程完成后，才能继续分配新的线程开始工作
        Args:
            speed: 线程并发数
            limit: 线程限制数
        """
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

    def todo(self, func: Callable, *args, **kwargs):
        """核心"""
        if self.count >= self.max_count:
            self.pool.shutdown()
            self.pool = ThreadPoolExecutor(max_workers=self.speed)
            self.count = 0
        future = self.pool.submit(func, *args, **kwargs)
        self.count += 1
        future.add_done_callback(partial(self.done, func.__name__))

    def done(self, func_name: str, future: Future):
        """线程的回调函数"""
        try:
            future.result()
        except Exception as e:
            logger.error("{} => {}".format(func_name, e))


class PoolManagerPLUS(PoolManager):
    def __init__(self, speed=5, limit: int = None):
        """
        当池子里有线程结束时，新的线程可以立刻进来
        Args:
            speed: 线程并发数
            limit: 线程限制数
        """
        super().__init__(speed, limit)
        self.event = Event()
        self.running_futures = []

    def todo(self, func: Callable, *args, **kwargs):
        """核心"""
        while True:
            if self.count < self.max_count:  # 无视阻塞，因为 活跃的线程数 没超过 并发数
                break
            self.event.wait()  # 开始阻塞

        future = self.pool.submit(func, *args, **kwargs)
        self.count += 1
        self.running_futures.append(future)
        self.event.clear()  # 发出 开始阻塞 信号
        future.add_done_callback(partial(self.done, func.__name__))

    def todos(self, func: Callable, *some):
        for args in zip(*some):
            self.todo(func, *args)

    def done(self, func_name: str, future: Future):
        """线程的回调函数"""
        super().done(func_name, future)
        if future in self.running_futures:
            self.running_futures.remove(future)
        self.count -= 1
        if self.count < self.max_count:
            self.event.set()  # 有线程完成，发出 取消阻塞 信号

    def running(self):
        """是否还有任务在运行"""
        for f in self.running_futures:
            if f.running():
                return True
        return False
