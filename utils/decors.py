import inspect
import random
import time
from functools import wraps

from loguru import logger


def type_check(func):
    """检查参数的注解，类型不一致则抛出异常"""

    @wraps(func)
    def inner(*args, **kwargs):
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
                        raise TypeError(
                            f"参数 '{name}' 应该是 {expected} 而不是 {type(value)}"
                        )
                if value != default_value and not isinstance(value, expected):
                    raise TypeError(
                        f"参数 '{name}' 应该是 {expected} 而不是 {type(value)}"
                    )

        return func(*args, **kwargs)

    return inner


def forever(interval=60, errback=None):
    """永远在运行"""

    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            while True:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        "{}  ==>  {}出现异常了  ==>  {}秒后继续启动".format(
                            e, func.__name__, interval
                        )
                    )
                    if errback:
                        errback(e, *args, **kwargs)
                else:
                    logger.info(
                        "{}正常结束了 ==> {}秒后继续启动".format(
                            func.__name__, interval
                        )
                    )
                finally:
                    time.sleep(interval)

        return inner

    return outer


def safe(func, when_failed=False):
    """异常时返回False"""

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("{}  ==>  {}".format(e, func.__name__))
            return when_failed

    return inner


def retry(times=5, rest=2, is_raise=True, when_all_failed=False):
    """重试（当函数异常时，触发重试，重试全部失败时返回False）"""

    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            err = None
            for i in range(times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error("{}  ==>  {}".format(e, func.__name__))
                    time.sleep(rest)
                    err = e
            if is_raise:
                raise err
            logger.critical("重试全部失败  ==>  {}".format(func.__name__))
            return when_all_failed

        return inner

    return outer


def min_work(seconds: int):
    """最少运行多少秒"""

    def outer(func):
        begin = time.time()

        @wraps(func)
        def inner(*args, **kwargs):
            result = None
            while True:
                if time.time() - begin >= seconds:
                    return result
                result = func(*args, **kwargs)

        return inner

    return outer


def timer(func):
    """计时器（输出函数的执行时间）"""

    @wraps(func)
    def inner(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        logger.info("{}耗时{:.4f}秒".format(func.__name__, t2 - t1))
        return result

    return inner


def defer(func):
    """延迟1-2秒后调用"""

    @wraps(func)
    def inner(*args, **kwargs):
        time.sleep(random.uniform(1, 2))
        return func(*args, **kwargs)

    return inner


def retry_request(func):
    """重试请求"""

    @wraps(func)
    def inner(*args, **kwargs):
        url = args[1]
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    """
                    URL         {}
                    ERROR       {}
                    TYPE        {}
                    """.format(url, e, type(e))
                )
        logger.critical("Failed  ==>  {}".format(url))

    return inner
