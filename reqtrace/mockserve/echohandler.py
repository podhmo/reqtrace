import cgi
import json


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
