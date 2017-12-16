import requests
from reqtrace.testlib.testing import background_server
from reqtrace.testlib.mockserve import create_app
from reqtrace.tracelib.requests import monkeypatch


def callback(environ):
    return "*ok*"


with background_server(create_app(callback)) as url:

    def coerce_redirect(request):
        request.url = url

    # changing permanently
    monkeypatch(on_request=coerce_redirect, on_response=print)

    response = requests.get(url)
    print(response.text)
