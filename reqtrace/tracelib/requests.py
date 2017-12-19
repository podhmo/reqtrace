import functools
import urllib.parse as parselib
from requests import sessions
from . import models


class TraceableHTTPAdapter:
    def __init__(self, internal, *, on_request, on_response):
        self.internal = internal
        self.on_request = on_request
        self.on_response = on_response

    def send(self, request, *args, **kwargs):
        request = RequestsTracingRequest(request)
        self.on_request(request)
        response = self.internal.send(request.rawrequest, *args, **kwargs)
        self.on_response(RequestsTracingResponse(request, response))
        return response

    def close(self):
        return self.internal.close()


_registry = {
    "original": None,
    "factory": None,
}


def request(method, url, factory=None, **kwargs):
    global _registry
    factory = factory or _registry["factory"]
    with factory() as session:
        return session.request(method=method, url=url, **kwargs)


def monkeypatch(*, on_request, on_response, force=False):
    global _registry

    import requests
    import requests.api
    original = _registry.get("original")

    if original is not None and not force:
        return

    if original is None:
        _registry["original"] = requests.api.request

    _registry["factory"] = create_factory(on_request=on_request, on_response=on_response)

    requests.request = request
    requests.api.request = request


def create_factory(
    *, on_request, on_response, internal_cls=sessions.Session, wrapper_cls=TraceableHTTPAdapter
):
    @functools.wraps(internal_cls)
    def factory(*args, **kwargs):
        s = internal_cls(*args, **kwargs)
        s.mount(
            "http://",
            wrapper_cls(s.get_adapter("http://"), on_request=on_request, on_response=on_response)
        )
        s.mount(
            "https://",
            wrapper_cls(s.get_adapter("https://"), on_request=on_request, on_response=on_response)
        )
        return s

    return factory


class RequestsTracingRequest(models.TracingRequest):
    __slots__ = ("rawrequest", )

    def __init__(self, rawrequest):
        self.rawrequest = rawrequest

    @property
    def headers(self):
        return dict(self.rawrequest.headers)

    @property
    def url(self):
        return self.rawrequest.url

    @property
    def host(self):
        return parselib.urlparse(self.url).netloc

    @property
    def path(self):
        return parselib.urlparse(self.url).path

    @property
    def queries(self):
        return parselib.parselib.urlparse(self.url).query

    @property
    def method(self):
        return self.rawrequest.method

    @property
    def body(self):
        return self.rawrequest.body

    def modify_url(self, url):
        self.rawrequest.url = url


class RequestsTracingResponse(models.TracingResponse):
    __slots__ = ("request", "rawresponse")

    def __init__(self, request, rawresponse):
        self.request = request
        self.rawresponse = rawresponse

    @property
    def url(self):
        return self.rawresponse.url

    @property
    def status_code(self):
        return self.rawresponse.status_code  # int

    @property
    def headers(self):
        return dict(self.rawresponse.headers)  # Dict

    @property
    def rawbody(self):
        return self.rawresponse.content  # bytes

    @property
    def body(self):
        if "/json" in self.rawresponse.headers["content-type"]:
            try:
                return self.rawresponse.json()
            except Exception as e:
                return self.rawresponse.text
        elif hasattr(self.rawbody, "decode"):
            return self.rawresponse.text
        else:
            return self.rawbody
