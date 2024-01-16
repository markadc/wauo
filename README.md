# 项目说明

- 基于requests封装的一个爬虫类

# Python解释器

- python3.10+

# 如何使用？

```python
from wauo import BaseSpider

s = BaseSpider()
```

## GET

```python
url = 'https://xxx.xxx.xxx'
resp = s.send(url)
```

## POST

#### 使用data参数

```python
api = 'https://xxx.xxx.xxx'
data = {
    'key1': 'value1',
    'key2': 'value2'
}
resp = s.send(api, data=data)
```

#### 使用json参数

```python
api = 'https://xxx.xxx.xxx'
json = {
    'key1': 'value1',
    'key2': 'value2'
}
resp = s.send(api, json=json)
```

## 限制响应

#### 限制响应码

- 如果响应码不在codes范围里则抛弃响应

```python
resp = s.send('https://www.baidu.com/xxx', codes=[200, 301, 302])
```

#### 限制响应内容

- 如果checker返回False则抛弃响应

```python
def is_ok(response):
    html = response.text
    if html.find('验证码') != -1:
        return False


resp = s.send('https://xxx.xxx.xxx', checker=is_ok)
```
