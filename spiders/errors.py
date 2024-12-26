class SpiderError(Exception):
    pass


class ResponseCodeError(SpiderError):
    pass


class ResponseTextError(SpiderError):
    pass


class RequestMethodError(SpiderError):
    pass


class MaxRetryError(SpiderError):
    pass
