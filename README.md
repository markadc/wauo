# 更新历史

- 新增`jsonp2json`静态方法
- 爬虫默认保持会话状态
- 新增`get_uuid`、`base64`加解密的静态方法
- 删除`download_text`、`download_bdata`，合并为`download`
- 新增`update_default_headers`方法
- `make_md5`支持字符串、二进制参数，并且可以加盐
- `send`方法加入`delay`参数，请求时可以设置延迟
- 新增`tools`包、`spiders`包
- 线程池管理者加入上下文，可以使用`with`了
- 新增`get_results`方法，获取所有`fs`的返回值
- 可以提前在send方法之前自定义延迟、超时
- 线程池管理者新增`running`方法，可以用于判断任务状态
- `send`方法加入详细注释
- 新增`todos`方法、tools改为utils

# 项目说明

- 基于requests封装的一个爬虫类

# Python解释器

- python3.10+

# 如何使用？

## 开始导入

```python
from wauo import WauoSpider

spider = WauoSpider()
```

## 请求

### GET

- 默认是get请求

```python
url = 'https://github.com/markadc'
resp = spider.send(url)
print(resp.text)
```

### POST

- 使用了`data`或者`json`参数，则是post请求

```python
api = 'https://github.com/markadc'
payload = {
    'key1': 'value1',
    'key2': 'value2'
}
resp = spider.send(api, data=payload)  # 使用data参数
resp = spider.send(api, json=payload)  # 使用json参数
```

## 响应

### 校验响应

#### 1、限制响应码

- 如果响应码不在codes范围里则抛弃响应（此时`send`返回`None`）

```python
resp = spider.send('https://github.com/markadc', codes=[200, 301, 302])
```

#### 2、限制响应内容

- 如果checker返回False则抛弃响应（此时`send`返回`None`）

```python
def is_ok(response):
    html = response.text
    if html.find('验证码') != -1:
        return False


resp = spider.send('https://github.com/markadc', checker=is_ok)
```

## 设置默认请求配置

- 给headers设置Cookie
- 给headers设置代理
- 给headers设置认证信息
- ...

### 例子1

- 每一次请求的headers都带上`cookie`

```python
from wauo import WauoSpider

cookie = 'Your Cookies'
spider = WauoSpider(default_headers={'Cookie': cookie})
resp1 = spider.send('https://github.com/markadc')
resp2 = spider.send('https://github.com/markadc/wauo')
print(resp1.request.headers)
print(resp2.request.headers)
```