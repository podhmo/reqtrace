from reqtrace.testing import background_server
from reqtrace.mockserve import create_app
from reqtrace.tracelib.requests import create_factory


def callback(environ):
    return "*ok*"


with background_server(create_app(callback)) as url:

    def coerce_redirect(request):
        request.url = url

    Session = create_factory(on_request=coerce_redirect, on_response=print)
    s = Session()
    response = s.get(url)
    print(response.text)
