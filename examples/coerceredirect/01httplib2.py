from reqtrace.testlib.testing import background_server
from reqtrace.testlib.mockserve import create_app
from reqtrace.tracelib.httplib2 import make_client


def callback(environ):
    return "*ok*"


with background_server(create_app(callback)) as url:

    def coerce_redirect(request):
        request.url = url

    h = make_client(on_request=coerce_redirect, on_response=print)
    response, content = h.request(
        "http://www.google.com/", "GET", headers={"content-type": "text/plain"}
    )
    print(response)
    print(content)
