from wauo import WauoSpider

s = WauoSpider()
url = 'https://wenku.baidu.com/wkvcode.html'
res = s.send(url)
res.encoding = "utf8"
res.raise_has_text("安全验证")
print(res, len(res.text))
