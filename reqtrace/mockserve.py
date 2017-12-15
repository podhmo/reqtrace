import logging
import json
from wsgiref.simple_server import make_server
from .util import (
    find_freeport,
    get_statuscode_from_int,
)
logger = logging.getLogger(__name__)


def coerce_response(body, encoding="utf-8"):
    if isinstance(body, str):
        return body.encode(encoding)
    elif hasattr(body, "keys"):
        return json.dumps(body).encode(encoding)
    else:
        return str(body).encode(encoding)


def create_app(fn, contenttype='text/plain', encoding="utf-8"):
    contenttype_heder = ('Content-type', '{}; charset={}'.format(contenttype, encoding))

    def app(environ, start_response):
        headers = [contenttype_heder]
        result = fn(environ)

        if isinstance(result, tuple) and len(result) == 2:
            body, code = result
        else:
            body = result
            code = 200

        status = get_statuscode_from_int(code)
        start_response(status, headers)
        return [coerce_response(body)]

    return app


def create_server(app, host='', port=None):
    port = port or find_freeport()
    return make_server(host, port, app)
