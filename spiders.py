# -*- coding: utf-8 -*-

import hashlib
import random
import string
import time
from datetime import datetime
from typing import Callable

import requests
from fake_useragent import UserAgent
from loguru import logger

from wauo.exceptions import ResponseCodeError, ResponseTextError


class SpiderTools:
    """爬虫工具"""

    @staticmethod
    def make_str(n=9):
        """获取随机字符串，a-zA-Z0-9"""
        s = "".join(random.sample(string.ascii_letters + string.digits, n))
        return s

    @staticmethod
    def make_md5(s: str):
        """获取字符串的md5"""
        value = hashlib.md5(s.encode(encoding='UTF-8')).hexdigest()
        return value

    @staticmethod
    def current_timestamp():
        """当前时间戳"""
        return int(time.time())

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
        cookie_str = ''
        for key, value in cookie.items():
            cookie_str += '{}={}; '.format(key, value)
        return cookie_str.rstrip('; ')

    @staticmethod
    def cookie_to_dict(cookie: str) -> dict:
        cookie_dict = {kv.split('=')[0]: kv.split('=')[1] for kv in cookie.split('; ')}
        return cookie_dict


def retry(func):
    """重试"""

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
        logger.critical('Failed  ==>  {}'.format(url))

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
    def __init__(self, cookie: str = None, session=False):
        self.cookie = cookie or ''
        self.req = requests.Session() if session else requests

    @retry
    def send(
            self, url: str, headers: dict = None, proxies: dict = None, timeout=3,
            data: dict = None, json: dict = None,
            cookie: str = None, codes: list = None, checker: Callable = None,
            **kwargs
    ):
        """
        发送请求，获取响应。默认为GET请求，如果传入了data或者json参数则为POST请求。
        """
        proxies = proxies or self.get_proxies()
        headers = headers or self.get_headers()
        headers.setdefault('User-Agent', self.ua.random)
        if cookie:
            headers.setdefault('Cookie', cookie)
        elif self.cookie:
            headers.setdefault('Cookie', self.cookie)

        same = dict(headers=headers, proxies=proxies, timeout=timeout)
        if data is None and json is None:
            response = self.req.get(url, **same, **kwargs)
        else:
            response = self.req.post(url, data=data, json=json, **same, **kwargs)

        if codes and response.status_code not in codes:
            raise ResponseCodeError('{} not in {}'.format(response.status_code, codes))

        if checker and checker(response) is False:
            raise ResponseTextError('not ideal text')

        return response

    def get_local_ip(self) -> str:
        """获取本地IP"""
        return self.send('https://httpbin.org/ip').json()['origin']
