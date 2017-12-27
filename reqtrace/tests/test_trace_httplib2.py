import unittest
import tempfile
import os
import json
import urllib.parse as parselib
from collections import namedtuple
from reqtrace.testing import background_server


class Tests(unittest.TestCase):
    def _makeEchoApp(self):
        from reqtrace.mockserve import create_app
        from reqtrace.mockserve.echohandler import echohandler
        return create_app(echohandler, content_type="application/json")

    def _makeClient(self, tmpdir):
        from reqtrace.tracelib.httplib2 import create_factory
        from reqtrace.tracelib.hooks import trace, noop
        factory = create_factory(on_request=noop, on_response=trace(tmpdir))
        return factory()

    def test_get(self):
        C = namedtuple("C", "path, params, expected")
        Expected = namedtuple("Expected", "queries, method, status_code")

        candidates = [
            C(
                path="/",
                params=None,
                expected=Expected(queries=[], method="GET", status_code=200),
            ),
            C(
                path="/foo",
                params={"name": "foo"},
                expected=Expected(queries=[["name", "foo"]], method="GET", status_code=200)
            ),
            C(
                path="/foo/foo",
                params=[("name", "foo"), ("name", "bar")],
                expected=Expected(
                    queries=[["name", "foo"], ["name", "bar"]], method="GET", status_code=200
                )
            ),
        ]

        for c in candidates:
            with self.subTest(c=c):
                with tempfile.TemporaryDirectory() as dirpath:
                    with background_server(self._makeEchoApp()) as baseurl:
                        http = self._makeClient(dirpath)
                        response, body = http.request(
                            baseurl + c.path + "?" + parselib.urlencode(c.params or {}),
                            method="GET"
                        )
                    with open(os.path.join(dirpath, os.listdir(dirpath)[0])) as rf:
                        traced = json.load(rf)

                    # response
                    self.assertEqual(json.loads(body.decode("utf-8")), traced["response"]["body"])
                    self.assertEqual(c.expected.status_code, traced["response"]["status_code"])

                    # request
                    self.assertEqual(c.expected.method, traced["request"]["method"])
                    self.assertEqual(baseurl.replace("http://", ""), traced["request"]["host"])
                    self.assertEqual(c.expected.queries, traced["request"]["queries"])
                    self.assertEqual(None, traced["request"]["body"])

    def test_post(self):
        C = namedtuple("C", "path, params, data, headers, expected")
        Expected = namedtuple("Expected", "queries, method, status_code, body")

        candidates = [
            C(
                path="/",
                params=None,
                data=parselib.urlencode([("items", "x"), ("items", "y"), ("items", "z")]),
                headers={'Content-type': 'application/x-www-form-urlencoded'},
                expected=Expected(
                    queries=[], method="POST", status_code=200, body="items=x&items=y&items=z"
                ),
            ),
            C(
                path="/",
                params=None,
                data=parselib.urlencode(
                    [("key", "value"), ("items", "x"), ("items", "y"), ("items", "z")]
                ),
                headers={'Content-type': 'application/x-www-form-urlencoded'},
                expected=Expected(
                    queries=[],
                    method="POST",
                    status_code=200,
                    body="key=value&items=x&items=y&items=z"
                ),
            ),
            C(
                path="/",
                params=None,
                data=json.dumps({
                    "name": "foo",
                    "age": 20
                }),
                headers={"content-type": "application/json"},
                expected=Expected(
                    queries=[], method="POST", status_code=200, body='{"name": "foo", "age": 20}'
                ),
            ),
        ]

        for c in candidates:
            with self.subTest(c=c):
                with tempfile.TemporaryDirectory() as dirpath:
                    with background_server(self._makeEchoApp()) as baseurl:
                        http = self._makeClient(dirpath)
                        response, body = http.request(
                            baseurl + c.path, method="POST", body=c.data, headers=c.headers
                        )
                    with open(os.path.join(dirpath, os.listdir(dirpath)[0])) as rf:
                        traced = json.load(rf)
                    # response
                    self.assertEqual(json.loads(body), traced["response"]["body"])
                    self.assertEqual(c.expected.status_code, traced["response"]["status_code"])

                    # request
                    self.assertEqual(c.expected.method, traced["request"]["method"])
                    self.assertEqual(baseurl.replace("http://", ""), traced["request"]["host"])
                    self.assertEqual(c.expected.queries, traced["request"]["queries"])
                    self.assertEqual(c.expected.body, traced["request"]["body"])
