import functools
from requests import sessions
from . import models


class TraceableHTTPAdapter:
    def __init__(self, internal, *, on_request, on_response):
        self.internal = internal
        self.on_request = on_request
        self.on_response = on_response

    def send(self, request, *args, **kwargs):
        self.on_request(request)  # xxx:
        response = self.internal.send(request, *args, **kwargs)
        self.on_response(RequestsTracingResponse(RequestsTracingRequest(request), response))
        return response

    def close(self):
        return self.internal.close()


_registry = {
    "original": None,
    "factory": None,
}


def request(method, url, factory=None, **kwargs):
    global _registry
    factory or _registry["factory"]
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

    _registry["factory"] = create_factory(on_request, on_response)

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
        return self.rawrequest.headers

    @property
    def url(self):
        return self.rawrequest.url

    @property
    def method(self):
        return self.rawrequest.method

    @property
    def body(self):
        return self.rawrequest.body


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
        return self.rawresponse.headers  # Dict

    @property
    def content(self):
        return self.rawresponse.content  # bytes
