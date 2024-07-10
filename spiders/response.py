from parsel import Selector
from requests import Response


class StrongResponse(Response):
    """可以使用Xpath、CSS"""

    def __init__(self, response: Response):
        super().__init__()
        self.__dict__.update(response.__dict__)
        self.seler = Selector(text=response.text)

    def __str__(self):
        return '<Response {}>'.format(self.status_code)

    def xpath(self, query: str):
        sele = self.seler.xpath(query)
        return sele

    def css(self, query: str):
        sele = self.seler.css(query)
        return sele

    def get_one(self, query: str):
        value = self.seler.xpath(query).get('').strip()
        return value

    def get_all(self, query: str):
        value = [v.strip() for v in self.seler.xpath(query).getall()]
        return value
