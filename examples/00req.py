from reqtrace.testlib.testing import background_server
from reqtrace.testlib.mockserve import create_app
from reqtrace.tracelib.requests import monkeypatch


def callback(environ):
    return "ok"


monkeypatch(on_request=print, on_response=print)
with background_server(create_app(callback)) as url:
    import requests
    response = requests.get(url)
    print(response.text)
