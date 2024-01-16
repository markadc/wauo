# -*- coding: utf-8 -*-

from typing import Callable

import requests
from fake_useragent import UserAgent
from loguru import logger

from wauo.exceptions import ResponseCodeError, ResponseTextError


def retry(func):
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


class BaseSpider:
    def __init__(self, cookie: str = None, session=False):
        self.cookie_str = cookie or ''
        self.cookie_dict = self.cookie_to_dict(cookie) if cookie else {}
        self.ua = UserAgent()
        self.req = requests.Session() if session else requests

    def get_local_ip(self) -> str:
        return self.send('https://httpbin.org/ip').json()['origin']

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

    def get_headers(self) -> dict:
        headers = {'User-Agent': self.ua.random}
        return headers

    @staticmethod
    def get_proxies() -> dict:
        return {}

    @retry
    def send(
            self, url: str, headers: dict = None, cookie: str = None, proxies: dict = None,
            data: dict = None, json: dict = None,
            timeout=6,
            codes: list = None, checker: Callable = None,
            **kwargs
    ):
        """
        发送请求，获取响应。默认为GET请求，如果传入了data或者json参数则为POST请求。
        """
        headers = headers or self.get_headers()
        headers.setdefault('User-Agent', self.ua.random)
        proxies = proxies or self.get_proxies()
        cookie_dict = self.cookie_to_dict(cookie) if cookie else self.cookie_dict
        same = dict(headers=headers, cookies=cookie_dict, proxies=proxies, timeout=timeout)

        if not (data or json):
            response = self.req.get(url, **same, **kwargs)
        else:
            response = self.req.post(url, data=data, json=json, **same, **kwargs)

        if codes and response.status_code not in codes:
            raise ResponseCodeError('{} not in {}'.format(response.status_code, codes))

        if checker and checker(response) is False:
            raise ResponseTextError('not ideal text')

        return response
