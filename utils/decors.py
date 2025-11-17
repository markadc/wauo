import inspect
import random
import threading
import time
from functools import wraps
from typing import Callable

from loguru import logger


def monitor(interval: int, tip: str):
    """
    监视器
    - 把函数包装成守护线程，周期性执行

    Args:
        interval: 执行间隔（秒）
        tip: 提示信息（异常日志的前缀）
    """

    def outer(func):
        @wraps(func)
        def _monitor(*args, **kwargs):
            def task():
                while True:
                    try:
                        func(*args, **kwargs)
                    except Exception as e:
                        logger.critical("{} | {}".format(tip, e))
                    time.sleep(interval)

            t = threading.Thread(target=task)
            t.daemon = True
            t.start()

        return _monitor

    return outer


def type_check(func):
    """检查参数的注解，类型不一致则抛出异常"""

    @wraps(func)
    def _type_check(*args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for name, value in bound_args.arguments.items():
            param = sig.parameters[name]
            expected = param.annotation
            default_value = param.default

            if expected != inspect.Parameter.empty:
                if default_value == inspect.Parameter.empty:
                    if not isinstance(value, expected):
                        raise TypeError(f"参数 '{name}' 应该是 {expected} 而不是 {type(value)}")
                if value != default_value and not isinstance(value, expected):
                    raise TypeError(f"参数 '{name}' 应该是 {expected} 而不是 {type(value)}")

        return func(*args, **kwargs)

    return _type_check


def forever(interval=60, errback: Callable = None):
    """
    重复运行这个函数
    - 当函数异常时，输出异常信息，并等待 interval 秒后重新启动

    Args:
        interval: 执行间隔（秒）
        errback: 异常回调函数
    """

    def outer(func):
        @wraps(func)
        def _forever(*args, **kwargs):
            while True:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error("{} | {} 出现异常了，{}秒后重新启动".format(e, func.__name__, interval))
                    if errback:
                        errback(e, *args, **kwargs)
                else:
                    logger.info("{} 正常结束了，{}秒后重新启动".format(func.__name__, interval))
                finally:
                    time.sleep(interval)

        return _forever

    return outer


def safe(func, failed="error"):
    """
    安全地执行函数
    - 当函数异常时，输出异常信息，并返回 failed 的值

    Args:
        failed: 异常时的返回值（默认 "error"）
    """

    @wraps(func)
    def _safe(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("{} | {}".format(e, func.__name__))
            return failed

    return _safe


def retry(times=5, rest=2, is_raise=True, failed="error"):
    """
    重试

    Args:
        times: 重试次数（默认 5 次）
        rest: 每次重试前的等待时间（默认 2 秒）
        is_raise: 重试全部失败后，是否抛出异常（默认 True）
        failed: 重试全部失败后，函数的返回值（仅当 is_raise 为 False 时有效）
    """

    def outer(func):
        @wraps(func)
        def _retry(*args, **kwargs):
            for i in range(times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == times and is_raise is True:
                        raise e
                    logger.error("{} | {}".format(e, func.__name__))
                    time.sleep(rest)
            logger.critical("重试全部失败 | {}".format(func.__name__))
            return failed

        return _retry

    return outer


def timer(func):
    """计时器（输出函数的执行时间）"""

    @wraps(func)
    def _timer(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        logger.info(f"Function <{func.__name__}> cost {t2 - t1:.4f} seconds")
        return result

    return _timer
