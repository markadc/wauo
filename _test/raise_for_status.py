from wauo import WauoSpider

s = WauoSpider()
url = 'http://www.baidu.com'
r = s.do(url)
r.raise_for_status(codes=[301, 302])
