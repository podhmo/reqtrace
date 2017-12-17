import functools
from httplib2 import Http
from . import models


class TraceableHttpWrapper:
    def __init__(self, internal, *, on_request, on_response):
        self.internal = internal
        self.on_request = on_request
        self.on_response = on_response

    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        kwargs["method"] = method
        kwargs["body"] = body
        kwargs["headers"] = headers or {}
        request = Httplib2TracingRequest(uri, kwargs)
        self.on_request(request)
        rawresponse, content = self.internal.request(request.url, **kwargs)
        self.on_response(Httplib2TracingResponse(request, rawresponse, content))
        return rawresponse, content


class Httplib2TracingRequest(models.TracingRequest):
    __slots__ = ("url", "kwargs")

    def __init__(self, url, kwargs):
        self.url = url
        self.kwargs = kwargs

    @property
    def headers(self):
        return self.kwargs.get("headers") or {}

    @property
    def method(self):
        return self.kwargs.get("method") or ""

    @property
    def body(self):
        return self.kwargs.get("body")


class Httplib2TracingResponse(models.TracingResponse):
    __slots__ = ("request", "rawresponse", "content")

    def __init__(self, request, rawresponse, content):
        self.request = request
        self.rawresponse = rawresponse
        self.content = content

    @property
    def url(self):
        return self.request.url

    @property
    def status_code(self):
        return int(self.rawresponse["status"])

    @property
    def headers(self):
        return self.rawresponse


def create_factory(*, on_request, on_response, internal_cls=Http, wrapper_cls=TraceableHttpWrapper):
    @functools.wraps(internal_cls)
    def factory(*args, **kwargs):
        internal = internal_cls(*args, **kwargs)
        return wrapper_cls(internal, on_request=on_request, on_response=on_response)

    return factory
