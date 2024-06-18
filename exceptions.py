class SpiderError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.msg)


class ResponseCodeError(SpiderError):
    pass


class ResponseTextError(SpiderError):
    pass


class RequestMethodError(SpiderError):
    pass
