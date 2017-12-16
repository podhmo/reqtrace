from httplib2 import Http


class TraceableHttpWrapper:
    def __init__(self, internal, *, on_request, on_response):
        self.internal = internal
        self.on_request = on_request
        self.on_response = on_response

    def request(self, uri, *args, **kwargs):
        request = _Request(uri)
        self.on_request(request)
        rawresponse, content = self.internal.request(request.url, *args, **kwargs)
        response = _Response(rawresponse, content)
        self.on_response(response)
        return rawresponse, content


class _Request:
    def __init__(self, url):
        self.url = url


class _Response:
    def __init__(self, rawresponse, body):
        self.rawresponse = rawresponse
        self.body = body


def make_client(
    *, on_request, on_response, http_class=Http, wrapper_class=TraceableHttpWrapper, **kwargs
):
    internal = Http(**kwargs)
    return wrapper_class(internal, on_request=on_request, on_response=on_response)
