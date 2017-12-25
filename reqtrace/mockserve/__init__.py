from wsgiref.simple_server import make_server as _make_server
from wsgiref.simple_server import WSGIServer as _WSGIServer
from ..util import find_freeport
from .core import create_app  # noqa

if hasattr(_WSGIServer, "__enter__"):
    WSGIServer = _WSGIServer
else:

    class WSGIServer(_WSGIServer):
        def __enter__(self):
            return self

        def __exit__(self, typ, val, tb):
            self.server_close()


def create_server(app, host='', port=None):
    port = port or find_freeport()
    return _make_server(host, port, app, server_class=WSGIServer)
