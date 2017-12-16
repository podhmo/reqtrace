from requests import sessions


class TracealbeHTTPWrapper:
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


_registry = {
    "original": None,
    "on_request": None,
    "on_response": None,
}


def make_client(on_request, on_response, *, wrapper_class=TracealbeHTTPWrapper):
    s = sessions.Session()
    s.mount(
        "http://",
        wrapper_class(s.get_adapter("http://"), on_request=on_request, on_response=on_response)
    )
    s.mount(
        "https://",
        wrapper_class(s.get_adapter("https://"), on_request=on_request, on_response=on_response)
    )
    return s


def request(method, url, **kwargs):
    global _registry
    with make_client(_registry["on_request"], _registry["on_response"]) as session:
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

    _registry["on_request"] = on_request
    _registry["on_response"] = on_response

    requests.request = request
    requests.api.request = request
