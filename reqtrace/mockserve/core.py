import logging
import json
from ..messages import get_reason_from_int
logger = logging.getLogger(__name__)


def coerce_response(body, encoding="utf-8", pretty=False):
    if isinstance(body, str):
        return body.encode(encoding)
    elif hasattr(body, "keys"):
        if pretty:
            return json.dumps(body, indent=2, ensure_ascii=False, sort_keys=True).encode(encoding)
        else:
            return json.dumps(body).encode(encoding)
    else:
        return str(body).encode(encoding)


def create_app(
    handler,
    content_type=None,
    encoding="utf-8",
    default_content_type="application/json",
    pretty=False,
):
    def app(environ, start_response):
        detected_content_type = content_type or environ.get("CONTENT_TYPE") or default_content_type
        content_type_header = (
            'Content-Type', '{}; charset={}'.format(detected_content_type, encoding)
        )

        headers = [content_type_header]
        result = handler(environ)
        code = 200
        if isinstance(result, tuple):
            if len(result) == 2:
                body, code = result
            elif len(result) >= 3:
                body, code, headers = result[:3]
            else:
                body = result
        else:
            body = result

        status = "{} {}".format(code, get_reason_from_int(code))
        start_response(status, headers)
        return [coerce_response(body, pretty=pretty)]

    return app
