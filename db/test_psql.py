from psql import PostgresqlClient

psql_cfg = {
    "host": "localhost",
    "port": 5432,
    "db": "test",
    "user": "wauo",
    "password": "admin1",
}
psql = PostgresqlClient(**psql_cfg)
psql.connect()

name = 'temp'

# 删除表
psql.drop_table(name)
print(f"表 {name} 已删除（如果存在）")

# 创建新表
psql.create_table(name, ['name', 'age'])

# 插入数据
n = psql.insert_one(name, {'name': 'Alice', 'age': 30})
print(f"插入的行数: {n}")
psql.insert_many(name, [{'name': 'Bob', 'age': 25}, {'name': 'Charlie', 'age': 35}])
print(f"批量插入的行数: {n}")

# 查询数据
lines = psql.query(f"SELECT * FROM {name}")
for line in lines:
    print(dict(line))

# 更新数据
n = psql.update(name, {'age': 31}, "name = %s", ('Alice',))
print(f"更新的行数: {n}")

# 删除数据
psql.delete(name, "name = %s", ('Bob',))
print("删除了 Bob 的记录")
