from mysql import MysqlClient

cfg = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root@0",
    "database": "test",
    "charset": "utf8mb4",
}

db = MysqlClient(**cfg)

db.execute("delete from user")
print("已删除所有数据")

print(db.insert_one("user", {"name": "test1"}))
print("已插入一条数据")
print(db.insert_many("user", [{"name": "test2"}, {"name": "test3"}]))
print("已插入多条数据")
print(db.update("user", {"name": "test22"}, "name = %s", ("test2",)))
print("已更新一条数据")
print(db.delete("user", "name = %s", ("test3",)))
print("已删除一条数据")

items = [{"name": f"test-{i}"} for i in range(10)]
print(db.insert_many("user", items))
print(f"已插入 {len(items)} 条数据")
print(db.fetchone("SELECT name FROM user"))
print(db.fetchmany("SELECT name FROM user", None, 2))
print(db.fetchall("SELECT name FROM user"))
