import random
import time

from wauo.utils import monitor


@monitor(2, "呜呜呜")
def demo(*args, **kwargs):
    print(args, kwargs)
    if random.randint(1, 3) == 1:
        raise Exception("~_~")


if __name__ == '__main__':
    demo(1, 2, name="CLOS")

    while True:
        time.sleep(200)
