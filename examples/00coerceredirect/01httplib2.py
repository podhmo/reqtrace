from reqtrace.testing import background_server
from reqtrace.mockserve import create_app
from reqtrace.tracelib.httplib2 import create_factory


def callback(environ):
    return "*ok*"


with background_server(create_app(callback)) as url:

    def coerce_redirect(request):
        request.url = url

    def on_response(response):
        print(response)

    Http = create_factory(on_request=coerce_redirect, on_response=on_response)
    h = Http()
    response, content = h.request(
        "http://www.google.com/", method="GET", headers={"content-type": "text/plain"}
    )
    print(response)
    print(content)
