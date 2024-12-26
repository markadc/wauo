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

import requests
from loguru import logger

from wauo.spiders.errors import MaxRetryError
from wauo.spiders.response import StrongResponse
from wauo.utils import retry_request


class SpiderTools:
    """爬虫工具"""

    @staticmethod
    def jsonp2json(jsonp: str):
        """jsonp转换为json"""
        data: dict = json.loads(re.match(".*?({.*}).*", jsonp, re.S).group(1))
        return data

    @staticmethod
    def get_uuid():
        """获取uuid"""
        uuid4 = str(uuid.uuid4())
        return uuid4

    @staticmethod
    def b64_encode(s: str):
        """base64加密"""
        encode_value = base64.b64encode(s.encode("utf-8")).decode("utf-8")
        return encode_value

    @staticmethod
    def b64_decode(s: str):
        """base64解密"""
        decode_value = base64.b64decode(s).decode("utf-8")
        return decode_value

    @staticmethod
    def rand_str(leng=9):
        """获取随机字符串，a-zA-Z0-9"""
        s = "".join(random.sample(string.ascii_letters + string.digits, leng))
        return s

    @staticmethod
    def make_md5(src: str | bytes, *args: str) -> str:
        """获取md5"""
        hasher = hashlib.md5()
        data = src if isinstance(src, bytes) else src.encode("utf-8")
        hasher.update(data)
        for arg in args:
            hasher.update(str(arg).encode("utf-8"))
        md5_value = hasher.hexdigest()
        return md5_value

    @staticmethod
    def current_timestamp(is_int=True):
        """当前时间戳"""
        now = time.time()
        return int(now) if is_int else now

    @staticmethod
    def current_time():
        """当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def current_date():
        """当前日期"""
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def cookie_to_str(cookie: dict) -> str:
        """Cookie转换为str类型"""
        cookie_str = ""
        for key, value in cookie.items():
            cookie_str += "{}={}; ".format(key, value)
        return cookie_str.rstrip("; ")

    @staticmethod
    def cookie_to_dict(cookie: str) -> dict:
        """Cookie转换为dict类型"""
        cookie_dict = {kv.split("=")[0]: kv.split("=")[1] for kv in cookie.split("; ")}
        return cookie_dict

    @staticmethod
    def save_file(path: str, content: str | bytes, encoding="UTF-8"):
        """保存文件"""
        mode = "wb" if isinstance(content, bytes) else "w"
        p_dir = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(p_dir):
            os.makedirs(p_dir)
        with open(path, mode, encoding=None if mode == "wb" else encoding) as f:
            f.write(content)


class BaseSpider(SpiderTools):
    """爬虫基类"""

    def __init__(self, ua_way: str = "local", proxies: dict = None, delay=0, timeout=5):
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
        self._raise_request_error = True  # True，请求异常则抛出异常；False，请求异常则响应返回None

    def allow_request_failed(self):
        """允许请求失败，此时响应为None"""
        self._raise_request_error = False

    def get_headers(self) -> dict:
        """获取一个有随机ua的headers"""
        headers = {"User-Agent": self.get_ua()}
        return headers

    def get_ua(self) -> str:
        """获取一个随机ua"""
        ua = self.gen_ua() if hasattr(self, "gen_ua") else self.ua.random
        return ua

    def get_proxies(self) -> dict:
        """获取代理"""
        return self.proxies

    def update_timeout(self, value: float | int):
        self.timeout = value

    def update_delay(self, value: float | int):
        self.delay = value


class WauoSpider(BaseSpider):
    """该爬虫默认保持会话状态"""

    def __init__(
            self, session=True, default_headers: dict = None,
            ua_way: str = "local", proxies: dict = None,
            delay=0, timeout=5
    ):
        super().__init__(ua_way=ua_way, proxies=proxies, delay=delay, timeout=timeout)
        self.client = requests.Session() if session else requests
        self.default_headers = default_headers or {}

    def update_default_headers(self, **kwargs):
        """更新默认headers，若key重复，则替换原有key"""
        for k, v in kwargs:
            self.default_headers[k] = v

    def add_field(self, headers: dict):
        """为headers补充默认default_headers的字段"""
        for k, v in self.default_headers.items():
            headers.setdefault(k, v)

    @staticmethod
    def elog(url: str, e: Exception, times: int):
        logger.error(
            """
            URL         {}
            ERROR       {}
            TIMES       {}
            """.format(url, e, times)
        )

    def do(self, url: str, headers: dict = None, params: dict = None, data: dict | str = None, json: dict = None, proxies: dict = None, timeout: int | float = 5, **kwargs) -> StrongResponse:
        """获取URL响应"""
        headers, proxies = headers or self.get_headers(), proxies or self.get_proxies()
        self.add_field(headers)
        same = dict(headers=headers, params=params, proxies=proxies, timeout=timeout, **kwargs)
        res = self.client.get(url, **same) if data is None and json is None else self.client.post(url, data=data, json=json, **same)
        return StrongResponse(res)

    def goto(self, url: str, headers: dict = None, params: dict = None, data: dict | str = None, json: dict = None, proxies: dict = None, timeout: int = 5, retry=2, delay=1, keep=True, **kwargs) -> StrongResponse:
        """
        获取响应，自带重试

        Parameters
        ----------
        retry   请求出现异常时，进行重试的次数
        delay   重试前先睡眠多少秒
        keep    所有的请求是否保持同一个headers，仅在headers为None时生效
        codes
        checker
        kwargs  跟requests的参数保持一致

        Returns
        -------
        StrongResponse，可以使用Xpath、CSS
        """
        keep = True if headers else False
        headers2 = headers or self.get_headers()
        for i in range(retry + 1):
            headers2, proxies2 = headers2 if keep else self.get_headers(), proxies or self.get_proxies()
            self.add_field(headers2)
            same = dict(headers=headers2, params=params, proxies=proxies2, timeout=timeout, **kwargs)
            try:
                resp = self.client.get(url, **same) if data is None and json is None else self.client.post(url, data=data, json=json, **same)
                return StrongResponse(resp)
            except Exception as e:
                self.elog(url, e, i + 1)
                time.sleep(delay)

        if self._raise_request_error:
            raise MaxRetryError("URL => {}".format(url))

    @retry_request
    def send(self, url: str, headers: dict = None, params: dict = None, proxies: dict = None, timeout: float | int = None, data: dict | str = None, json: dict = None, cookie: str = None, delay: int | float = None, **kwargs) -> StrongResponse:
        """
        发送请求，获取响应。
        默认为GET请求，如果传入了data或者json参数则为POST请求。
        返回的响应对象可以直接使用Xpath、CSS。

        Parameters
        ----------
        url     请求地址
        headers 请求头
        proxies 代理
        timeout 超时
        data    请求体form-data
        json    请求体json
        cookie  为headers补充Cookie字段，如果headers已存在Cookie字段则不生效
        delay   延迟请求的秒数
        kwargs  跟requests的参数保持一致

        Returns
        -------
        StrongResponse，可以使用Xpath、CSS
        """
        delay = delay or self.delay
        time.sleep(delay)

        proxies = proxies or self.get_proxies()
        headers = headers or self.get_headers()

        headers.setdefault("User-Agent", self.get_ua())
        if cookie:
            headers.setdefault("Cookie", cookie)
        for key, value in self.default_headers.items():
            headers.setdefault(key, value)

        same = dict(headers=headers, params=params, proxies=proxies, timeout=timeout or self.timeout, **kwargs)
        response = self.client.get(url, **same) if data is None and json is None else self.client.post(url, data=data, json=json, **same)
        return StrongResponse(response)

    def download(self, url: str, path: str, bin=True, encoding="UTF-8"):
        """默认下载二进制"""
        resp = self.send(url)
        content = resp.content if bin else resp.text
        self.save_file(path, content, encoding)

    def get_local_ip(self) -> str:
        """获取本地IP"""
        return self.send("https://httpbin.org/ip").json()["origin"]
