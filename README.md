# 项目说明

Python工具大全。

- 爬虫
- 装饰器（计时器、类型强校验...）
- 线程池（内存不溢出）
- 快速地操作数据库（MySQL、PostgreSQL）
- ...

# 安装

```bash
pip install wauo -U
```

# Python解释器

- python3.10+

# 如何使用？

## 数据库

### PostgreSQL

```python
from wauo.db import PostgresqlClient

psql_cfg = {
    "host": "localhost",
    "port": 5432,
    "db": "test",
    "user": "wauo",
    "password": "admin1",
}
psql = PostgresqlClient(**psql_cfg)
psql.connect()

tname = 'temp'

# 删除表
psql.drop_table(tname)
print(f"表 {tname} 已删除（如果存在）")

# 创建新表
psql.create_table(tname, ['name', 'age'])

# 插入数据
n = psql.insert_one(tname, {'name': 'Alice', 'age': 30})
print(f"插入的行数: {n}")
psql.insert_many(tname, [{'name': 'Bob', 'age': 25}, {'name': 'Charlie', 'age': 35}])
print(f"批量插入的行数: {n}")

# 查询数据
lines = psql.query(f"SELECT * FROM {tname}")
for line in lines:
    print(dict(line))

# 更新数据
n = psql.update(tname, {'age': 31}, "name = %s", ('Alice',))
print(f"更新的行数: {n}")

# 删除数据
psql.delete(tname, "name = %s", ('Bob',))
print("删除了 Bob 的记录")

```

## 爬虫

```python
from wauo import WauoSpider

spider = WauoSpider()
```

### 请求

#### GET

- 默认是get请求

```python
url = 'https://github.com/markadc'
resp = spider.send(url)
print(resp.text)
```

#### POST

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

### 响应

#### 响应对象

- `SelectorResponse`

```python
resp = spider.send("https://www.baidu.com")
title = resp.get_one("//title/text()")  # 等同于 resp.xpath("//title/text()").get()
print(title)  # 输出：百度一下，你就知道

```

#### 校验响应

限制响应码

- 如果响应码不在 codes 范围里则引发异常

```python
resp = spider.send('https://github.com/markadc')
resp.raise_for_status(codes=[301, 302])
```

限制响应内容

- 如果 is_ok 返回 False 则引发异常

```python
def is_ok(html: str):
    return html.find('验证') == -1


resp = spider.send('https://wenku.baidu.com/wkvcode.html')
resp.raise_for_text(validate=is_ok)
```

### 设置默认请求配置

例子1

- 每一次请求头都带上 Cookie 字段

```python
from wauo import WauoSpider

cookie = 'Your Cookies'
spider = WauoSpider(default_headers={'Cookie': cookie})
resp1 = spider.send('https://github.com/markadc')
resp2 = spider.send('https://github.com/markadc/wauo')
print(resp1.request.headers)
print(resp2.request.headers)
```

## 工具使用

### 颜色输出

```python
from wauo.printer import Printer

p = Printer()
p.red("This is a red message")
p.green("This is a green message")
p.yellow("This is a yellow message")
p.blue("This is a blue message")
p.output("This is a custom color message", "magenta")
```

![_printer.png](_printer.png)

### 函数参数类型强校验

- type_check
- 根据注解检查函数的参数类型，类型不一致则报错

```python
from wauo.utils import type_check


@type_check
def add(x: int, y: int) -> int:
    print(f'{x} + {y} = {x + y}')
    return x + y


# 正常
add(1, 2)  # 1 + 2 = 3

# 报错
add(1, "2")  # 参数 'y' 应该是 <class 'int'> 而不是 <class 'str'>

```

### 字典多层取值

- nget
- 字典多层取值，键不存在则返回设定的默认值

```python
from wauo.utils import nget

item = {
    "data": {
        "info": {
            "user1": {"name": "Charo", "age": 18},
            "user2": {"name": "Jack", "age": 20},
            "user3": {"name": "Peter", "age": 22},
        }
    }
}

print(nget(item, "data.info.user1.name"))
# Charo

print(nget(item, "data.info.user2.age"))
# 20

print(nget(item, "data.info.user3"))
# {'name': 'Peter', 'age': 22}

print(nget(item, "data.info.user4", failed="不存在"))
# 不存在

print(nget(item, "data.info"))
# {'user1': {'name': 'Charo', 'age': 18}, 'user2': {'name': 'Jack', 'age': 20}, 'user3': {'name': 'Peter', 'age': 22}}

```

## 工具说明

- 传入变量，可以直接打印该变量的字符串名称、实际值

- 时间戳转时间、时间转时间戳、获取今天任意时刻的时间戳

- 字典多层取值，键不存在则返回设定的默认值

- 处理线程任务，有序获取（先返回的靠前）所有线程的返回值（异常的线程、假值除外）

- 带颜色的打印函数

- 检查参数的注解，类型不一致则抛出异常

- 封装的线程池（自带阻塞，不用担心溢出）

- ...

# 更新历史

- 新增db，操作MySQL、PostgreSQL数据库
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