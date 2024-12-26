from wauo.utils import cget

data = {
    1: {
        11: {
            111: 111
        }
    },
    2: {
        22: {
            222: 222
        }
    },
    3: {
        33: [3, 33, 333]
    }
}

v = cget(data, 1, 11, 111)
print(v)

v = cget(data, 2, 22, 222)
print(v)

v = cget(data, 3, 44, log=True)
print(v)

v = cget(data, 3, 33, 333, log=True)
print(v)
