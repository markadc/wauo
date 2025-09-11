from wauo.spiders import WauoSpider

cli = WauoSpider()
url = 'https://httpbin.orgxx/get'
resp = cli.go(url)
print(resp.text)
