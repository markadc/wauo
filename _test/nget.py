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
