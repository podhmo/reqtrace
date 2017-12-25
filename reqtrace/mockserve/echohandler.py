import cgi
import json


def _extract_body(environ):
    content_length = int(environ.get("CONTENT_LENGTH") or 0)
    if content_length == 0:
        return {}

    # todo: binary format support

    if environ.get("CONTENT_TYPE", "").endswith("/json"):
        data = json.loads(environ["wsgi.input"].read(content_length))
        return {"body": data}
    else:
        form = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
        data = []
        for k in form:
            f = form[k]
            if isinstance(f, list):
                data.extend([(k, x.value) for x in f])
            else:
                data.append((k, f.value))
        return {"body": sorted(data)}


def echohandler(environ):
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

    d.update(_extract_body(environ))
    return d, 200
