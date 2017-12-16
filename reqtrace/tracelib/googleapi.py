import functools
import json
import googleapiclient.model
from googleapiclient.discovery import build as build_google
from .httplib2 import create_factory as create_httplib2_factory


class OrderedJsonModel(googleapiclient.model.JsonModel):
    """OrderedJSON is good for caching"""

    def serialize(self, body_value):
        if body_value is None:
            return None

        # this is same as original JsonModel.serialize()
        if (isinstance(body_value, dict) and 'data' not in body_value and self._data_wrapper):
            body_value = {'data': body_value}

        return json.dumps(body_value, sort_keys=True)


def create_factory(*, on_request, on_response):
    # warning: on_response's passed response object is not same at httplib2's one
    Http = create_httplib2_factory(on_request=on_request, on_response=on_response)

    @functools.wraps(build_google)
    def factory(name, version, *args, **kwargs):
        if kwargs.get("model") is None:
            kwargs["model"] = OrderedJsonModel()
        if kwargs.get("http") is None:
            kwargs["http"] = Http()
        if kwargs.get("cache") is None:
            kwargs["cache"] = _SimpleDiscoveryCache()
        return build_google(name, version, *args, **kwargs)

    return factory


class _SimpleDiscoveryCache:
    def __init__(self):
        self.docs = {}

    def get(self, url):
        return self.docs.get(url)

    def set(self, url, doc):
        self.docs[url] = doc


# # xxx:
# import httplib2
# httplib2.debuglevel = 1
