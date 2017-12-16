from reqtrace.testing import background_server
from reqtrace.mockserve import create_app
from reqtrace.tracelib.httplib2 import create_factory


def callback(environ):
    return "*ok*"


with background_server(create_app(callback)) as url:

    def coerce_redirect(request):
        request.url = url

    Http = create_factory(on_request=print, on_response=print)
    h = Http()
    response, content = h.request(
        "http://www.google.com/", "GET", headers={"content-type": "text/plain"}
    )
    print(response)
    print(content)
