import functools
import json
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

    def modify_url(self, url):
        self.url = url


class Httplib2TracingResponse(models.TracingResponse):
    __slots__ = ("request", "rawresponse", "rawbody")
    encoding = "utf-8"  # xxx

    def __init__(self, request, rawresponse, rawbody):
        self.request = request
        self.rawresponse = rawresponse
        self.rawbody = rawbody

    @property
    def url(self):
        return self.request.url

    @property
    def status_code(self):
        return int(self.rawresponse["status"])

    @property
    def headers(self):
        return self.rawresponse

    @property
    def body(self):
        content_type = self.headers["content-type"]
        if "/json" in content_type and self.encoding in content_type:
            try:
                return json.loads(self.rawbody.decode(self.encoding))  # xxx:
            except Exception as e:
                return self.rawbody.decode(self.encoding)  # xxx:
        elif hasattr(self.rawbody, "decode"):
            return self.rawbody.decode(self.encoding)
        else:
            return self.rawbody


def create_factory(*, on_request, on_response, internal_cls=Http, wrapper_cls=TraceableHttpWrapper):
    @functools.wraps(internal_cls)
    def factory(*args, **kwargs):
        internal = internal_cls(*args, **kwargs)
        return wrapper_cls(internal, on_request=on_request, on_response=on_response)

    return factory
