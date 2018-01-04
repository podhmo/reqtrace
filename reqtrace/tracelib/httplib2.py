import functools
import logging
import io
import json
from httplib2 import Http
from . import models
logger = logging.getLogger(__name__)


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
        text = None
        if "/json" in content_type:
            try:
                text = self.rawbody.decode(self.encoding)
                return json.loads(text)  # xxx:
            except Exception as e:
                logger.warn(str(e), exc_info=True)
                return text or self.rawbody
        elif "binary/" in content_type or "/octet-stream" in content_type or (
            "image/" in content_type and "image/svg" != content_type
        ):
            return self.rawbody
        elif hasattr(self.rawbody, "decode"):
            try:
                text = self.rawbody.decode(self.encoding)
            except Exception as e:
                logger.warn(str(e), exc_info=True)
            return text or self.rawbody
        else:
            return self.rawbody


def create_factory(*, on_request, on_response, internal_cls=Http, wrapper_cls=TraceableHttpWrapper):
    @functools.wraps(internal_cls)
    def factory(*args, **kwargs):
        internal = internal_cls(*args, **kwargs)
        return wrapper_cls(internal, on_request=on_request, on_response=on_response)

    return factory


_registry = {"original": None, "factory": None}


def monkeypatch(*, on_request, on_response, force=False):
    import httplib2
    original = _registry.get("original")

    if original is not None and not force:
        return

    if original is None:
        original = _registry["original"] = Http

    factory = _registry["factory"] = create_factory(on_request=on_request, on_response=on_response)

    class _Http:
        def __init__(self, *args, **kwargs):
            self.core = factory(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.core, name)

    httplib2.Http = _Http
