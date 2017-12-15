from functools import partial
from requests import sessions


class TracealbeHTTPAdapter:
    def __init__(self, internal, *, on_request, on_response):
        self.internal = internal
        self.on_request = on_request
        self.on_response = on_response

    def send(self, request, *args, **kwargs):
        self.on_request(request)
        response = self.internal.send(request, *args, **kwargs)
        self.on_response(response)
        return response

    def close(self):
        return self.internal.close()


_original = None
_factory = None


def request(method, url, **kwargs):
    global _factory
    with sessions.Session() as session:
        session.mount("http://", _factory(session.get_adapter("http://")))
        session.mount("https://", _factory(session.get_adapter("https://")))
        return session.request(method=method, url=url, **kwargs)


def monkeypatch(*, on_request, on_response):
    global _original
    global _factory

    import requests
    import requests.api

    if _original is not None:
        return

    if _factory is None:
        _factory = partial(TracealbeHTTPAdapter, on_request=on_request, on_response=on_response)

    _original = requests.api.request

    requests.request = request
    requests.api.request = request
