import threading
import contextlib
import sys
import io
from .mockserve import create_server
from .util import get_port_from_httpd

_outputstream_factory = io.StringIO


def set_debug():
    global _outputstream_factory

    def debug_outputstream():
        return sys.stderr

    _outputstream_factory = debug_outputstream


def _get_output_stream():
    global _outputstream_factory
    return _outputstream_factory()


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
