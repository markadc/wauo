from wauo.utils import type_check


@type_check
def add(x: int, y: int) -> int:
    print(f'{x} + {y} = {x + y}')
    return x + y


# 正常
add(1, 2)  # 1 + 2 = 3

# 报错
add(1, "2")  # 参数 'y' 应该是 <class 'int'> 而不是 <class 'str'>
