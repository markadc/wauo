import threading
from concurrent.futures import ThreadPoolExecutor


class LimitedThreadPool:
    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
        self.current_tasks = 0
        self.condition = threading.Condition()

    def submit(self, fn, *args, **kwargs):
        """提交任务，如果达到最大并发数则阻塞"""
        with self.condition:
            # 等待直到有空闲线程
            self.condition.wait_for(lambda: self.current_tasks < self.max_workers)
            self.current_tasks += 1
            future = self.pool.submit(fn, *args, **kwargs)
            future.add_done_callback(self._task_done)
        return future

    def _task_done(self, future):
        """任务完成时的回调"""
        with self.condition:
            self.current_tasks -= 1
            self.condition.notify()  # 通知等待的线程

    def shutdown(self):
        """关闭线程池"""
        self.pool.shutdown()


if __name__ == "__main__":
    import time, random
    from wauo import printer as p


    def work(x):
        p.yellow(f'{x} 执行中')
        time.sleep(random.uniform(1, 3))
        p.green(f'{x} 已完成')


    pool = LimitedThreadPool(max_workers=3)

    for i in range(20):
        pool.submit(work, i + 1)

    pool.shutdown()
