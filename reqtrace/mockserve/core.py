import logging
import json
from ..messages import get_reason_from_int
logger = logging.getLogger(__name__)


def coerce_response(body, encoding="utf-8"):
    if isinstance(body, str):
        return body.encode(encoding)
    elif hasattr(body, "keys"):
        return json.dumps(body).encode(encoding)
    else:
        return str(body).encode(encoding)


def create_app(
    handler, content_type=None, encoding="utf-8", default_content_type="application/json"
):
    def app(environ, start_response):
        detected_content_type = content_type or environ.get("CONTENT_TYPE") or default_content_type
        content_type_header = (
            'Content-type', '{}; charset={}'.format(detected_content_type, encoding)
        )

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
