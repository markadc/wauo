from concurrent.futures import as_completed
from datetime import datetime

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


now = lambda: datetime.now().strftime("%Y:%m:%d %H:%M:%S")


def cprint(content, color=None):
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
    color_code = color_codes.get(color, "37")
    print(f"\033[{color_code}m{now()} | {content}\033[0m")
