import urllib.parse as parselib
from ..langhelpers import reify


class URLAnalyzer:
    __slots__ = ("url", "parsed")

    def __init__(self, url):
        self.url = url
        self.parsed = parselib.urlparse(url)

    @property
    def host(self):
        return self.parsed.netloc

    @property
    def path(self):
        return self.parsed.path

    @property
    def queries(self):
        return parselib.parse_qsl(self.parsed.query)


class TracingRequest:
    def __repr__(self):
        return "<{self.__class__.__name__} url={self.url!r}>".format(self=self)

    @reify
    def urlanalyzer(self):
        return URLAnalyzer(self.url)

    @property
    def headers(self):
        raise NotImplementedError("dict")

    @property
    def method(self):
        raise NotImplementedError("str")

    @property
    def body(self):
        raise NotImplementedError("bytes?")

    def modify_url(self, url):
        raise NotImplementedError("")

    def __json__(self):
        d = {
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "body": self.body,
        }
        return d


class TracingResponse:
    def __repr__(self):
        return "<{self.__class__.__name__} url={self.url!r}, status_code={self.status_code}>".format(
            self=self
        )

    @property
    def url(self):
        raise NotImplementedError("str")

    @property
    def status_code(self):
        raise NotImplementedError("int")

    @property
    def headers(self):
        raise NotImplementedError("dict")

    @property
    def body(self):
        raise NotImplementedError("bytes?")

    def __json__(self):
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }
