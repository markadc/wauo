# 更新历史

- 新增`jsonp2json`静态方法
- 爬虫`默认保持会话`状态
- 新增`get_uuid`、`base64加解密`静态方法
- 删除`download_text`、`download_bdata`，合并为`download`
- 新增`update_default_headers`方法
- `make_md5`支持`字符串`、`二进制`参数，并且可以加盐
- `send`方法加入`delay`参数，请求时可以设置延迟
- 新增`tools`包、`spiders`包
- `线程池管理者`加入上下文，可以使用`with`了
- 新增`get_results`方法，获取`所有fs`的返回值
- 可以`提前`在send方法之前`自定义延迟、超时`
- 线程池管理者新增`running`方法，可以用于判断任务状态
- `send`方法加入`详细注释`
- 新增`todos`方法、tools改为utils

# 项目说明

- 基于requests封装的一个爬虫类

# Python解释器

- python3.10+

# 如何使用？

```python
from wauo import WauoSpider

spider = WauoSpider()
```

## GET

```python
url = 'https://github.com/markadc'
resp = spider.send(url)
print(resp.text)
```

## POST

#### 使用data参数

```python
api = 'https://github.com/markadc'
data = {
    'key1': 'value1',
    'key2': 'value2'
}
resp = spider.send(api, data=data)
```

#### 使用json参数

```python
api = 'https://github.com/markadc'
json = {
    'key1': 'value1',
    'key2': 'value2'
}
resp = spider.send(api, json=json)
```

## 限制响应

#### 限制响应码

- 如果响应码不在codes范围里则抛弃响应

```python
resp = spider.send('https://github.com/markadc', codes=[200, 301, 302])
```

#### 限制响应内容

- 如果checker返回False则抛弃响应

```python
def is_ok(response):
    html = response.text
    if html.find('验证码') != -1:
        return False


resp = spider.send('https://github.com/markadc', checker=is_ok)
```

#### 为headers增加默认字段

- 实例化的时候使用default_headers参数

##### 例子1

- 每一次请求的headers都带上cookie

```python
cookie = 'Your Cookies'

spider = WauoSpider(default_headers={'Cookie': cookie})
resp1 = spider.send('https://github.com/markadc')
resp2 = spider.send('https://github.com/markadc/wauo')

print(resp1.request.headers)
print(resp2.request.headers)
```