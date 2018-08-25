import io
import functools
import logging
import urllib.parse as parselib
from requests.sessions import Session
from . import models
logger = logging.getLogger(__name__)


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


_registry = {"original": None, "factory": None, "originalSession": None}


def request(method, url, factory=None, **kwargs):
    global _registry
    factory = factory or _registry["factory"]
    with factory() as session:
        return session.request(method=method, url=url, **kwargs)


def monkeypatch(*, on_request, on_response, force=False, pip=False):
    global _registry

    import requests
    from requests import api
    from requests import sessions
    original = _registry.get("original")

    if original is not None and not force:
        return

    if original is None:
        original = _registry["original"] = requests.api.request

    class _Session(Session):
        @functools.wraps(Session.__init__)
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            activate_tracing_hook(self, on_request=on_request, on_response=on_response)

    _registry["factory"] = create_factory(on_request=on_request, on_response=on_response)
    _registry["originalSession"] = Session

    requests.request = request
    api.request = request
    requests.Session = _Session
    sessions.Session = _Session
    if pip:
        # hmm.
        import pip.download
        import pip.basecommand
        _registry["originalPipSession"] = pip.download.PipSession

        class _PipSession(pip.download.PipSession):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                activate_tracing_hook(self, on_request=on_request, on_response=on_response)

        # pip.download.PipSession = _PipSession  # hack
        pip.basecommand.PipSession = _PipSession


def activate_tracing_hook(s, *, on_request, on_response, wrapper_cls=TraceableHTTPAdapter):
    s.mount(
        "http://",
        wrapper_cls(s.get_adapter("http://"), on_request=on_request, on_response=on_response)
    )
    s.mount(
        "https://",
        wrapper_cls(s.get_adapter("https://"), on_request=on_request, on_response=on_response)
    )


def create_factory(
    *, on_request, on_response, internal_cls=Session, wrapper_cls=TraceableHTTPAdapter
):
    @functools.wraps(internal_cls)
    def factory(*args, **kwargs):
        s = internal_cls(*args, **kwargs)
        activate_tracing_hook(s, on_request=on_request, on_response=on_response)
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
        body = self.rawrequest.body
        if hasattr(body, "decode"):
            return body.decode("utf-8")  # xxx
        return body

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
        content_type = self.rawresponse.headers.get("content-type", "text/html")
        if "/xml" in content_type:
            if not self.rawresponse.raw.seekable():
                raw = self.rawresponse.raw
                rawbody = raw._fp.read()
                raw._fp = io.BytesIO(rawbody)  # xxx:
                self.rawresponse._content = rawbody
                self.rawresponse._content_consumed = True
            else:
                rawbody = self.rawbody
            if hasattr(rawbody, "decode"):
                return self.rawresponse.text
            return rawbody
        elif "/json" in content_type:
            try:
                return self.rawresponse.json()
            except Exception as e:
                logger.warn(str(e), exc_info=True)
                return self.rawresponse.text
        elif "binary/" in content_type or "/octet-stream" in content_type or (
            "image/" in content_type and "image/svg" != content_type
        ):
            if not self.rawresponse.raw.seekable():
                raw = self.rawresponse.raw
                rawbody = raw._fp.read()
                raw._fp = io.BytesIO(rawbody)
                self.rawresponse._content = rawbody
                self.rawresponse._content_consumed = True
            return rawbody
        elif hasattr(self.rawbody, "decode"):
            return self.rawresponse.text
        else:
            return self.rawbody
