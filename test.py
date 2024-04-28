# -*- coding: utf-8 -*-

from wauo import WauoSpider

s = WauoSpider(default_headers={'Cookie': 'Your Cookies'})
url = 'https://www.baidu.com'
resp = s.send(url)
print(resp)
print(resp.request.headers)
