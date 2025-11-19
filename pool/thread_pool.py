from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class SmartThreadPool:
    """
    智能线程池
    - 当有任务提交时，如果达到了最大并发数，则阻塞，直到有线程执行结束释放了资源
    """

    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
        self.current_tasks = 0
        self.condition = threading.Condition()

    def submit(self, fn, *args, **kwargs):
        """提交任务，如果达到最大并发数则阻塞"""
        with self.condition:
            self.condition.wait_for(lambda: self.current_tasks < self.max_workers)  # 等待，直到有空闲线程
            self.current_tasks += 1
            future = self.pool.submit(fn, *args, **kwargs)
            future.add_done_callback(self._task_done)
        return future

    def _task_done(self, future):
        """任务完成时的回调"""
        with self.condition:
            self.current_tasks -= 1
            self.condition.notify()  # 通知等待的线程

    def map(self, fn, *iterables, timeout=None):
        """
        Args:
            fn: 要执行的函数
            *iterables: 一个或多个可迭代对象
            timeout: 超时时间（秒）
        Returns:
            返回结果的迭代器（先完成的先返回）
        """
        futures = [self.submit(fn, *args) for args in zip(*iterables)]
        for future in as_completed(futures, timeout=timeout):
            yield future.result()

    def shutdown(self):
        """关闭线程池"""
        self.pool.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False


if __name__ == "__main__":
    import time, random
    from wauo import printer as p

    def job(i):
        p.yellow(f"{i} 执行中...")
        delay = random.uniform(1, 5)
        time.sleep(delay)
        p.green(f"✅ {i} 已完成")
        return delay, i

    # 方式1
    with SmartThreadPool(max_workers=5) as pool:
        for i in range(10):
            pool.submit(job, i)

    # 方式2
    with SmartThreadPool(max_workers=10) as pool:
        pool.map(job, range(10))

    # 获取线程返回值
    # with SmartThreadPool(max_workers=5) as pool:
    #     fs = [pool.submit(job, i) for i in range(10)]
    #     for f in fs:
    #         print(f.result())

    # 获取线程返回值（先完成的线程先返回）
    # with SmartThreadPool(max_workers=10) as pool:
    #     results = pool.map(job, range(10))
    #     for result in results:
    #         print(result)
