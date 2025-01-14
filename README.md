# 安装

```bash
pip install wauo -U
```

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
- `done`加入func_name参数，可以定位到具体是哪一个`线程函数`出现异常
- `PoolWait`、`PoolMan`
- 一些参数的变化（改名、补充注解）
- 加入了一些装饰器函数
- 补充`send`方法中`**kwargs`的说明
- 新增`block`方法，可以进行阻塞
- 一些优化
- utils包新增`cget`方法，字典多层取值，KEY不存在则返回<default>
- cprint参数有误则默认不加入颜色打印
- 一些优化，新增raise_for_status、raise_for_text、do方法、函数文档模板修改等

# 项目说明

- 基于requests封装的一个爬虫

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

- 如果响应码不在codes范围里则引发异常

```python
resp = spider.send('https://github.com/markadc')
resp.raise_for_status(codes=[301, 302])
```

#### 2、限制响应内容

- 如果is_ok返回False则引发异常

```python
def is_ok(html: str):
    return html.find('验证') == -1


resp = spider.send('https://wenku.baidu.com/wkvcode.html')
resp.raise_for_text(validate=is_ok)
```

## 设置默认请求配置

- 给headers设置Cookie
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

# 一些工具

- 传入变量，可以直接打印该变量的字符串名称、实际值

- 时间戳转时间、时间转时间戳、获取今天任意时刻的时间戳

- 字典多层取值，KEY不存在则返回设定的默认值

- 处理线程任务，有序获取（先返回的靠前）所有线程的返回值（异常的线程、假值除外）

- 带颜色的打印函数

- 检查参数的注解，类型不一致则抛出异常

- 封装的线程池（自带阻塞，不用担心溢出）

- ...