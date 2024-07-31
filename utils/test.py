import random

from loguru import logger

from wauo.utils.pool_manager import PoolManagerPLUS
from wauo.utils.pools import SpeedPool


def test1():
    def task1(name):
        import time
        uid = "任务{}".format(name)
        logger.warning("{} running...".format(uid))
        delay = random.randint(1, 3)
        assert delay != 3, "{}: ~_~".format(uid)
        time.sleep(delay)
        logger.success("...over {}".format(uid))

    with PoolManagerPLUS() as pool1:
        i = 0
        while True:
            i += 1
            pool1.todo(task1, i)


def test2():
    def task2(name):
        import time
        uid = "任务{}".format(name)
        while True:
            time.sleep(1)
            logger.warning("{}执行中...".format(uid))
            n = random.randint(1, 10)
            if n == 10:
                raise Exception("{}出现错误".format(uid))
            if n == 2:
                logger.success("...{}完成了".format(uid))
                break

    with SpeedPool() as pool2:
        i = 0
        while True:
            i += 1
            pool2.todo(task2, i)


if __name__ == '__main__':
    # test1()
    test2()
