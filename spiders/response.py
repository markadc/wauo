from parsel import Selector
from requests import Response as BaseResponse


class Response(BaseResponse):
    def __init__(self, resp: BaseResponse):
        super().__init__()
        self.__dict__.update(resp.__dict__)
        self.sele = Selector(text=resp.text)

    def __str__(self):
        return '<Response {}>'.format(self.status_code)

    def xpath(self, query: str):
        sele = self.sele.xpath(query)
        return sele

    def css(self, query: str):
        sele = self.sele.css(query)
        return sele

    def get_one(self, query: str):
        value = self.sele.xpath(query).get('').strip()
        return value

    def get_all(self, query: str):
        value = [v.strip() for v in self.sele.xpath(query).getall()]
        return value
