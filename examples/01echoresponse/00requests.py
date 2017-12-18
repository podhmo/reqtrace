import requests
import json
import os.path
import threading
from reqtrace.mockserve import create_app, echohandler, create_server
from reqtrace.tracelib.requests import monkeypatch
from reqtrace.tracelib.hooks import trace

port = 4444
dirpath = os.path.join(os.path.dirname(__file__), "data/00requests")
monkeypatch(on_request=print, on_response=trace(dirpath))


def get0(baseurl):
    response = requests.get(baseurl)
    print(response.json())


def get1(baseurl):
    payload = {"name": "foo"}
    response = requests.get(baseurl, params=payload)
    print(response.json())


def get2(baseurl):
    payload = {"items": ["x", "y", "z"]}
    response = requests.get(baseurl, params=payload)
    print(response.json())


def post0(baseurl):
    payload = {"key": "value", "items": ["x", "y", "z"]}
    response = requests.post(baseurl, data=payload)
    print(response.json())


def post1(baseurl):
    payload = (("key", "value0"), ("key", "value1"))
    response = requests.post(baseurl, data=payload)
    print(response.json())


def post2(baseurl):
    headers = {'content-type': 'application/json'}
    payload = {"items": ["x", "y", "z"]}
    response = requests.post(baseurl, data=json.dumps(payload, sort_keys=True), headers=headers)
    print(response.json())


def put0(baseurl):
    response = requests.put(baseurl, data={'key': 'value'})
    print(response.json())


def delete0(baseurl):
    response = requests.delete(baseurl)
    print(response.content)


def head0(baseurl):
    response = requests.head(baseurl)
    print(response.content)


def options0(baseurl):
    response = requests.options(baseurl)
    print(response.content)


with create_server(create_app(echohandler, content_type="application/json"), port=port) as httpd:
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()

    url = "http://localhost:{port}".format(port=port)
    print("----------------------------------------")
    get0(url)
    get1(url)
    get2(url)

    print("----------------------------------------")
    post0(url)
    post1(url)
    post2(url)

    print("----------------------------------------")
    put0(url)
    delete0(url)
    head0(url)
    options0(url)
