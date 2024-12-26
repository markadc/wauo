from wauo import WauoSpider

s = WauoSpider()
url = 'https://wenku.baidu.com/wkvcode.html'
r = s.do(url)
r.encoding = "utf8"
r.raise_for_text(validate=lambda html: html.find("验证") == -1)
print(r, len(r.text))
