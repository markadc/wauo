from wauo import WauoSpider

s = WauoSpider()
url = 'http://www.baidu.com'
r = s.do(url)
print(r.get_one("//title/text()"))
print(r.request.headers)
