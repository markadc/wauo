import ctypes
import inspect
import random
from concurrent.futures import as_completed
from datetime import datetime
from threading import Thread

from loguru import logger


def wlog(msg: str, show: bool):
    if show:
        logger.warning(msg)


def cget(data: dict, *args, log=False, default=None):
    """字典多层取值，KEY不存在则返回<default>"""
    temp = data
    for i, a in enumerate(args):
        if a not in temp:
            wlog(f"KEY {a!r} miss", log)
            return default
        temp = temp.get(a)
        if i == len(args) - 1:
            return temp
        if not isinstance(temp, dict):
            wlog(f"KEY {a!r} VALUE {temp!r} not is dict", log)
            return default
    return temp


def kill_thread(thread: Thread):
    """强制杀死线程"""
    tid = thread.ident
    exctype = SystemExit
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))


def get_results(fs: list, timeout: int | float = None):
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


now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def cprint(content, color=None):
    """带颜色的打印"""
    color_codes = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
        "light_red": "91",
        "light_green": "92",
        "light_yellow": "93",
        "light_blue": "94",
        "light_magenta": "95",
        "light_cyan": "96",
        "light_white": "97",
    }
    color_code = color_codes.get(color)
    if color_code:
        print(f"\033[{color_code}m{now()}  {content}\033[0m")
    else:
        print(f"{now()}  {content}")


def make_ua():
    """随机User-Agent"""
    a = random.randint(55, 62)
    c = random.randint(0, 3200)
    d = random.randint(0, 150)
    os_type = [
        '(Windows NT 6.1; WOW64)', '(Windows NT 10.0; WOW64)',
        '(X11; Linux x86_64)',
        '(Macintosh; Intel Mac OS X 10_12_6)'
    ]
    chrome_version = f'Chrome/{a}.0.{c}.{d}'
    os_choice = random.choice(os_type)
    ua = f"Mozilla/5.0 {os_choice} AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} Safari/537.36"
    return ua
