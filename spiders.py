# -*- coding: utf-8 -*-

import base64
import hashlib
import os
import random
import string
import time
import uuid
from datetime import datetime
from typing import Callable

import requests
from fake_useragent import UserAgent
from loguru import logger

from wauo.exceptions import ResponseCodeError, ResponseTextError
from wauo.response import Response


class SpiderTools:
    """爬虫工具"""

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
    def make_md5(s: str) -> str:
        """获取字符串的md5"""
        value = hashlib.md5(s.encode(encoding='UTF-8')).hexdigest()
        return value

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
    def __init__(self, session=True, default_headers: dict = None):
        self.req = requests.Session() if session else requests
        self.default_headers = default_headers or {}

    @retry
    def send(
            self, url: str, headers: dict = None, proxies: dict = None, timeout=3,
            data: dict = None, json: dict = None,
            cookie: str = None, codes: list = None, checker: Callable = None,
            **kwargs
    ) -> Response:
        """
        发送请求，获取响应。默认为GET请求，如果传入了data或者json参数则为POST请求。
        """
        proxies = proxies or self.get_proxies()
        headers = headers or self.get_headers()
        headers.setdefault('User-Agent', self.ua.random)
        if cookie:
            headers.setdefault('Cookie', cookie)
        for key, value in self.default_headers.items():
            headers.setdefault(key, value)

        same = dict(headers=headers, proxies=proxies, timeout=timeout)
        if data is None and json is None:
            response = self.req.get(url, **same, **kwargs)
        else:
            response = self.req.post(url, data=data, json=json, **same, **kwargs)

        if codes and response.status_code not in codes:
            raise ResponseCodeError('{} not in {}'.format(response.status_code, codes))
        if checker and checker(response) is False:
            raise ResponseTextError('not ideal text')

        return Response(response)

    def get_local_ip(self) -> str:
        """获取本地IP"""
        return self.send('https://httpbin.org/ip').json()['origin']

    def download_text(self, path: str, url: str, encoding='UTF-8'):
        """从URL下载文本数据"""
        text = self.send(url).text
        self.save_file(path, text, encoding=encoding)

    def download_bdata(self, path: str, url: str):
        """从URL下载二进制数据"""
        bdata = self.send(url).content
        self.save_file(path, bdata, 'wb')
