import functools
from httplib2 import Http
from collections import namedtuple


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


# todo: replacing correct model object
class _Request:
    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "<{} url={}>".format(self.__class__.__name__, self.url)


_Response = namedtuple("_Response", "rawresponse, body")


def create_factory(*, on_request, on_response, internal_cls=Http, wrapper_cls=TraceableHttpWrapper):
    @functools.wraps(internal_cls)
    def factory(*args, **kwargs):
        internal = internal_cls(*args, **kwargs)
        return wrapper_cls(internal, on_request=on_request, on_response=on_response)

    return factory
