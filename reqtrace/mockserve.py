import logging
import json
from wsgiref.simple_server import make_server
from .messages import get_reason_from_int
from .util import find_freeport
logger = logging.getLogger(__name__)


def coerce_response(body, encoding="utf-8"):
    if isinstance(body, str):
        return body.encode(encoding)
    elif hasattr(body, "keys"):
        return json.dumps(body).encode(encoding)
    else:
        return str(body).encode(encoding)


def create_app(handler, content_type=None, encoding="utf-8", default_content_type="application/json"):
    def app(environ, start_response):
        detected_content_type = content_type or environ.get("CONTENT_TYPE") or default_content_type
        content_type_header = ('Content-type', '{}; charset={}'.format(detected_content_type, encoding))

        headers = [content_type_header]
        result = handler(environ)

        if isinstance(result, tuple) and len(result) == 2:
            body, code = result
        else:
            body = result
            code = 200

        status = "{} {}".format(code, get_reason_from_int(code))
        start_response(status, headers)
        return [coerce_response(body)]

    return app


def echo_handler(environ):
    import cgi
    d = {
        "method": environ["REQUEST_METHOD"],
        "path": environ["PATH_INFO"],
        "querystring": environ["QUERY_STRING"],
        "content_type": environ["CONTENT_TYPE"],
        "content_length": environ["CONTENT_LENGTH"],
    }
    for k in environ.keys():
        if k.startswith("HTTP_"):
            d[k.replace("HTTP_", "").lower()] = environ[k]

    if int(d.get("content_length") or 0):
        if d.get("content_type").endswith("/json"):
            content_length = int(d["content_length"])
            data = json.loads(environ["wsgi.input"].read(content_length))
            d["jsonbody"] = data
        else:
            form = cgi.FieldStorage(
                fp=environ["wsgi.input"], environ=environ, keep_blank_values=True
            )
            data = {}
            for k in form:
                f = form[k]
                if isinstance(f, list):
                    data[k] = [x.value for x in f]
                else:
                    data[k] = f.value
            d["formdata"] = data

    return d, 200


def create_server(app, host='', port=None):
    port = port or find_freeport()
    return make_server(host, port, app)
