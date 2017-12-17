import json
import os.path
from reqtrace.tracelib.googleapi import create_factory
from reqtrace.testing import background_server
from reqtrace.mockserve import create_app


def discovery_callback(environ):
    with open(os.path.join(os.path.dirname(__file__), "data/discovery.json")) as rf:
        return json.load(rf), 200


class RedirectStore:
    def __init__(self, url):
        self.url = url

    def __call__(self, request):
        print("@", request.url, "->", url)
        if request.url != url:
            request.url = url


# discovery
with background_server(create_app(discovery_callback)) as url:
    rs = RedirectStore(url)

    def noop(response):
        print(response)

    build_google = create_factory(on_request=rs, on_response=noop)
    service = build_google("slides", "v1")


def callback(environ):
    with open(os.path.join(os.path.dirname(__file__), "data/presentations.json")) as rf:
        return json.load(rf), 200


# using api
with background_server(create_app(callback)) as url:
    rs.url = url
    presentationId = '1EAYk18WDjIG-zp_0vLm3CsfQh_i8eXc67Jo2O9C6Vuc'

    slides = service.presentations().get(presentationId=presentationId).execute()
    for slide in slides["slides"]:
        print(slide["objectId"])
