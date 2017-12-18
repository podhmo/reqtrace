from wsgiref.simple_server import make_server
from .util import find_freeport
from .core import create_app  # noqa
from .echo import echo_handler  # noqa


def create_server(app, host='', port=None):
    port = port or find_freeport()
    return make_server(host, port, app)
