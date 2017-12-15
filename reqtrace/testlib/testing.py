import threading
import contextlib
import sys
import io
import os
from .mockserve import create_server

_outputstream_factory = None


def set_debug():
    global _outputstream_factory

    def debug_outputstream():
        return sys.stderr

    _outputstream_factory = debug_outputstream


def _get_output_stream():
    global _outputstream_factory
    if _outputstream_factory is None:
        _outputstream_factory = io.StringIO
        if bool(os.environ.get("DEBUG")):
            set_debug()
    return _outputstream_factory()


def get_port_from_httpd(httpd):
    return httpd.server_address[1]


@contextlib.contextmanager
def background_server(app, *, host="http://localhost", timeout=None, stderr=None):
    stderr = stderr or _get_output_stream()
    with contextlib.redirect_stderr(stderr):
        with create_server(app) as httpd:
            port = get_port_from_httpd(httpd)
            url = "{}:{}".format(host, port)
            th = threading.Thread(target=httpd.handle_request, daemon=True)
            th.start()
            yield url
            th.join(timeout)
    return stderr
