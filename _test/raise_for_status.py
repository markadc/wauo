from wauo import WauoSpider

s = WauoSpider()
url = 'http://www.baidu.com'
r = s.do(url)
try:
    r.raise_for_status(codes=[301, 302])
except Exception as e:
    print("{!r} {!r}".format(type(e).__name__, e))
