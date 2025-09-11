import base64
import hashlib
import json
import os
import random
import re
import string
import time
import uuid
from datetime import datetime
from functools import wraps

import requests
from loguru import logger

from wauo.spiders.errors import MaxRetryError
from wauo.spiders.response import SelectorResponse


class SpiderTools:
    """
    爬虫工具类

    提供常用的爬虫辅助功能，包括：
    - JSONP转JSON
    - UUID生成
    - Base64编解码
    - 随机字符串生成
    - MD5哈希
    - 时间戳和时间格式化
    - Cookie格式转换
    - 文件保存
    """

    @staticmethod
    def jsonp2json(jsonp: str) -> dict:
        """jsonp转换为json"""
        match = re.search(r".*?({.*}).*", jsonp, re.S)
        if not match:
            raise ValueError("Invalid JSONP format")
        return json.loads(match.group(1))

    @staticmethod
    def get_uuid() -> str:
        """获取uuid"""
        return str(uuid.uuid4())

    @staticmethod
    def b64_encode(s: str) -> str:
        """base64加密"""
        return base64.b64encode(s.encode("utf-8")).decode("utf-8")

    @staticmethod
    def b64_decode(s: str) -> str:
        """base64解密"""
        return base64.b64decode(s).decode("utf-8")

    @staticmethod
    def rand_str(length: int = 9) -> str:
        """获取随机字符串，a-zA-Z0-9"""
        return "".join(random.sample(string.ascii_letters + string.digits, length))

    @staticmethod
    def make_md5(src: str | bytes, *args: str) -> str:
        """获取md5"""
        hasher = hashlib.md5()
        data = src if isinstance(src, bytes) else src.encode("utf-8")
        hasher.update(data)
        for arg in args:
            hasher.update(str(arg).encode("utf-8"))
        return hasher.hexdigest()

    @staticmethod
    def current_timestamp() -> float:
        """当前时间戳"""
        return time.time()

    @staticmethod
    def current_time() -> str:
        """当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def current_date() -> str:
        """当前日期"""
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def cookie_to_str(cookie: dict) -> str:
        """Cookie转换为str类型"""
        return "; ".join(f"{key}={value}" for key, value in cookie.items())

    @staticmethod
    def cookie_to_dict(cookie: str) -> dict:
        """Cookie转换为dict类型"""
        return {
            kv.split("=", 1)[0]: kv.split("=", 1)[1]
            for kv in cookie.split("; ")
            if "=" in kv
        }

    @staticmethod
    def save_file(path: str, content: str | bytes, encoding="UTF-8"):
        """保存文件"""
        mode = "wb" if isinstance(content, bytes) else "w"
        p_dir = os.path.dirname(os.path.abspath(path))
        os.makedirs(p_dir, exist_ok=True)
        with open(path, mode, encoding=None if mode == "wb" else encoding) as f:
            f.write(content)


class BaseSpider(SpiderTools):
    """
    爬虫基类

    提供爬虫的基础功能：
    - User-Agent管理
    - 代理设置
    - 请求延迟和超时控制
    - 错误处理配置
    """

    def __init__(self, ua_way="local", proxies: dict = None, delay=0, timeout=5):
        assert ua_way in ["api", "local"]
        if ua_way == "api":
            from fake_useragent import UserAgent
            self.ua = UserAgent()
        else:
            from wauo.utils import make_ua
            self.gen_ua = make_ua

        self.proxies = proxies or {}
        self.delay = delay
        self.timeout = timeout
        self.is_raise_error = True  # 是否抛出异常（当请求异常时）
        self.is_merge_default_headers = True  # 是否合并默认请求头（当发送请求时）

    def get_headers(self) -> dict:
        """获取headers"""
        headers = {"User-Agent": self.get_ua()}
        return headers

    def get_ua(self) -> str:
        """获取一个随机ua"""
        ua = self.gen_ua() if hasattr(self, "gen_ua") else self.ua.random
        return ua

    def get_proxies(self) -> dict:
        """获取代理"""
        return self.proxies


def retry_request(func):
    """请求异常时重试2次"""

    @wraps(func)
    def inner(*args, **kwargs):
        url = args[1]
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"""
                    url         {url}
                    error       {e}
                    type        {type(e)}
                    """
                )
        logger.critical(f"Failed => {url}")
        if args[0].is_raise_error:
            raise MaxRetryError(url)

    return inner


class WauoSpider(BaseSpider):
    """
    高级爬虫类

    继承BaseSpider，提供更强大的功能：
    - 会话状态保持
    - 默认请求头管理
    - 自动重试机制
    - 多种请求方法
    - 文件下载功能
    """

    def __init__(self, is_session=True, default_headers: dict = None, ua_way="local", proxies: dict = None, delay=0, timeout=5):
        super().__init__(ua_way=ua_way, proxies=proxies, delay=delay, timeout=timeout)
        self.client = requests.Session() if is_session else requests
        self.default_headers = default_headers or {}

    def update_default_headers(self, **kwargs):
        """更新默认headers，若key重复，则替换原有key"""
        for k, v in kwargs.items():
            self.default_headers[k] = v

    def merge_headers(self, headers: dict):
        """为headers补充默认default_headers的字段"""
        for k, v in self.default_headers.items():
            headers.setdefault(k, v)

    @staticmethod
    def elog(url: str, e: Exception, times: int):
        logger.error(
            f"""
            url         {url}
            error       {e}
            times       {times}
            """
        )

    @retry_request
    def send(
            self,
            url: str,
            headers: dict = None,
            params: dict = None,
            data: dict | str = None,
            json: dict = None,
            proxies: dict = None,
            timeout: float | int = None,
            cookie: str = None,
            delay: int | float = None,
            **kwargs
    ) -> SelectorResponse:
        """
        发送请求，获取响应
        - 默认为GET请求，如果传入了data或者json参数则为POST请求
        - 返回的响应对象可以直接使用Xpath、CSS

        Args:
            cookie: 为headers补充Cookie字段
            delay: 延迟多少秒后才请求
            **kwargs: 跟requests的参数保持一致

        Returns:
            SelectorResponse（可以使用Xpath、CSS）
        """
        delay = delay or self.delay
        time.sleep(delay)

        proxies = proxies or self.get_proxies()
        timeout = timeout or self.timeout

        headers = headers or self.get_headers()
        if cookie:
            headers.setdefault("Cookie", cookie)
        if self.is_merge_default_headers:
            headers = self.default_headers | headers

        same = dict(headers=headers, params=params, proxies=proxies, timeout=timeout, **kwargs)
        response = self.client.get(url, **same) if data is None and json is None else self.client.post(url, data=data, json=json, **same)
        return SelectorResponse(response)

    def do(self, url: str, headers: dict = None, params: dict = None, data: dict | str = None, json: dict = None, proxies: dict = None, timeout: int | float = 5, **kwargs) -> SelectorResponse:
        """默认为GET请求，传递了data或者json参数则为POST请求"""
        headers = headers or self.get_headers()
        if self.is_merge_default_headers:
            headers = self.default_headers | headers
        proxies = proxies or self.get_proxies()
        same = dict(headers=headers, params=params, proxies=proxies, timeout=timeout, **kwargs)
        res = self.client.get(url, **same) if data is None and json is None else self.client.post(url, data=data, json=json, **same)
        return SelectorResponse(res)

    def go(
            self,
            url: str,
            headers: dict = None,
            params: dict = None,
            data: dict | str = None,
            json: dict = None,
            proxies: dict = None,
            timeout=5,
            retry_times=2,
            retry_delay=1,
            keep_headers=True,
            **kwargs
    ) -> SelectorResponse:
        """
        获取响应，自带重试

        Args:
            retry_times: 请求出现异常时，进行重试的次数
            retry_delay: 重试前先睡眠多少秒
            keep_headers: 请求时是否保持同一个headers
            **kwargs: 跟requests的参数保持一致

        Returns:
            SelectorResponse（可以使用Xpath、CSS）
        """

        headers = headers or self.get_headers() if keep_headers else {}
        if headers and self.is_merge_default_headers:
            headers = self.default_headers | headers

        for i in range(retry_times + 1):
            headers = headers or self.get_headers()
            proxies = proxies or self.get_proxies()
            same = dict(headers=headers, params=params, proxies=proxies, timeout=timeout, **kwargs)
            try:
                resp = self.client.get(url, **same) if data is None and json is None else self.client.post(url, data=data, json=json, **same)
                return SelectorResponse(resp)
            except Exception as e:
                logger.error(
                    f"""
                    url             {url}
                    error           {e} => {type(e)}
                    retey_times     {i}/{retry_times}
                    """
                )
                time.sleep(retry_delay)

        if self.is_raise_error:
            raise MaxRetryError(url)

    def download(self, url: str, path: str, bin=True, encoding="UTF-8"):
        """下载"""
        resp = self.send(url)
        if resp is None:
            raise Exception(f"Failed to download {url}")
        content = resp.content if bin else resp.text
        self.save_file(path, content, encoding)

    def get_local_ip(self) -> str:
        """获取本地IP"""
        resp = self.send("https://httpbin.org/ip")
        if resp is None:
            raise Exception("Failed to get local IP")
        return resp.json()["origin"]
