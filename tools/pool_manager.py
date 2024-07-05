from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

from loguru import logger


def get_results(fs: list, timeout=None):
    """处理线程任务，有序获取（先返回的靠前）所有线程的返回值（异常的线程、假值除外）"""
    results = []
    try:
        for v in as_completed(fs, timeout=timeout):
            try:
                result = v.result()
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(e)
    except Exception as e:
        logger.error(e)
    return results


class PoolManager:
    def __init__(self, speed=5, limit: int = None):
        """
        线程池管理者\n
        说明：池子里所有的线程完成后，才能继续分配新的线程开始工作
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

    def todo(self, func, *args, **kwargs):
        """核心"""
        if self.count >= self.max_count:
            self.pool.shutdown()
            self.pool = ThreadPoolExecutor(max_workers=self.speed)
            self.count = 0
        future = self.pool.submit(func, *args, **kwargs)
        future.add_done_callback(self.done)
        self.count += 1

    def done(self, future):
        """线程的回调函数"""
        try:
            future.result()
        except Exception as e:
            logger.error("线程异常 -> {}".format(e))

    def close(self, wait=True, cancel_futures=False):
        """释放资源"""
        self.pool.shutdown(wait=wait, cancel_futures=cancel_futures)


class PoolManagerPLUS(PoolManager):
    def __init__(self, speed=5, limit: int = None):
        """
        线程池高效管理者\n
        说明：当池子里有线程结束时，新的线程可以立刻进来
        Args:
            speed: 线程并发数
            limit: 线程限制数
        """
        super().__init__(speed, limit)
        self.event = Event()

    def todo(self, func, *args, **kwargs):
        """核心"""
        while True:
            if self.count < self.max_count:  # 无视阻塞，因为 活跃的线程数 没超过 并发数
                break
            self.event.wait()  # 开始阻塞

        future = self.pool.submit(func, *args, **kwargs)
        self.count += 1
        self.event.clear()  # 发出 开始阻塞 信号
        future.add_done_callback(self.done)

    def done(self, future):
        """线程的回调函数"""
        super().done(future)
        self.count -= 1
        if self.count < self.max_count:
            self.event.set()  # 有线程完成，发出 取消阻塞 信号
