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
from typing import Callable

import requests
from fake_useragent import UserAgent
from loguru import logger

from wauo.exceptions import ResponseCodeError, ResponseTextError
from wauo.spiders.response import Response


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
        encode_value = base64.b64encode(s.encode('utf-8')).decode('utf-8')
        return encode_value

    @staticmethod
    def b64_decode(s: str):
        """base64解密"""
        decode_value = base64.b64decode(s).decode('utf-8')
        return decode_value

    @staticmethod
    def make_str(leng=9):
        """获取随机字符串，a-zA-Z0-9"""
        s = "".join(random.sample(string.ascii_letters + string.digits, leng))
        return s

    @staticmethod
    def make_md5(src: str | bytes, *args) -> str:
        """获取md5"""
        hasher = hashlib.md5()
        data = src if isinstance(src, bytes) else src.encode('utf-8')
        hasher.update(data)
        for arg in args:
            hasher.update(str(arg).encode('utf-8'))
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
        cookie_str = ''
        for key, value in cookie.items():
            cookie_str += '{}={}; '.format(key, value)
        return cookie_str.rstrip('; ')

    @staticmethod
    def cookie_to_dict(cookie: str) -> dict:
        """Cookie转换为dict类型"""
        cookie_dict = {kv.split('=')[0]: kv.split('=')[1] for kv in cookie.split('; ')}
        return cookie_dict

    @staticmethod
    def save_file(path: str, content, mode='w', encoding='UTF-8'):
        """保存文件"""
        p_dir = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(p_dir):
            os.makedirs(p_dir)
        with open(path, mode, encoding=None if mode == 'wb' else encoding) as f:
            f.write(content)


def retry(func):
    """重试请求"""

    def _retry(*args, **kwargs):
        url = args[1]
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    '''
                    URL         {}
                    ERROR       {}
                    '''.format(url, e)
                )
        logger.error('Failed  ==>  {}'.format(url))

    return _retry


class BaseSpider(SpiderTools):
    """爬虫基类"""

    ua = UserAgent()

    def get_headers(self) -> dict:
        """获取headers"""
        headers = {'User-Agent': self.ua.random}
        return headers

    @staticmethod
    def get_proxies() -> dict:
        """获取代理"""
        return {}


class WauoSpider(BaseSpider):
    """该爬虫默认保持会话状态"""

    def __init__(self, session=True, default_headers: dict = None):
        self.client = requests.Session() if session else requests
        self.default_headers = default_headers or {}

    @retry
    def send(
            self, url: str, headers: dict = None, proxies: dict = None, timeout=3,
            data: dict = None, json: dict = None,
            cookie: str = None, codes: list = None, checker: Callable = None,
            delay: int | float = 0,
            **kwargs
    ) -> Response:
        """
        发送请求，获取响应。默认为GET请求，如果传入了data或者json参数则为POST请求。
        """
        time.sleep(delay)
        proxies = proxies or self.get_proxies()
        headers = headers or self.get_headers()
        headers.setdefault('User-Agent', self.ua.random)
        if cookie:
            headers.setdefault('Cookie', cookie)
        for key, value in self.default_headers.items():
            headers.setdefault(key, value)

        same = dict(headers=headers, proxies=proxies, timeout=timeout)
        if data is None and json is None:
            response = self.client.get(url, **same, **kwargs)
        else:
            response = self.client.post(url, data=data, json=json, **same, **kwargs)

        if codes and response.status_code not in codes:
            raise ResponseCodeError('{} not in {}'.format(response.status_code, codes))
        if checker and checker(response) is False:
            raise ResponseTextError('not ideal text')

        return Response(response)

    def get_local_ip(self) -> str:
        """获取本地IP"""
        return self.send('https://httpbin.org/ip').json()['origin']

    def update_default_headers(self, **kwargs):
        """更新默认headers，若key重复，则替换原有key"""
        for k, v in kwargs:
            self.default_headers[k] = v

    def download(self, url: str, path: str, mode=1, encoding='UTF-8'):
        """mode=1或2（1下载文本，2下载二进制）"""
        assert mode in [1, 2], '1：文本，2：二进制'
        resp = self.send(url)
        if mode == 1:
            self.save_file(path, resp.text, encoding=encoding)
        else:
            self.save_file(path, resp.content, mode='wb')
