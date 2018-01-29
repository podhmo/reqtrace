import unittest
import json
import tempfile
import threading
from collections import namedtuple


class _RequestAccessing:
    def get0(self, s, baseurl):
        response = s.get(baseurl)
        return response.json()

    def get1(self, s, baseurl):
        payload = {"name": "foo"}
        response = s.get(baseurl, params=payload)
        return response.json()

    def get2(self, s, baseurl):
        payload = {"items": ["x", "y", "z"]}
        response = s.get(baseurl, params=payload)
        return response.json()

    def post0(self, s, baseurl):
        payload = {"key": "value", "items": ["x", "y", "z"]}
        response = s.post(baseurl, data=payload, params={"q": "foo"})
        return response.json()

    def post1(self, s, baseurl):
        payload = (("key", "value0"), ("key", "value1"))
        response = s.post(baseurl, data=payload)
        return response.json()

    def post2(self, s, baseurl):
        headers = {'content-type': 'application/json'}
        payload = {"items": ["x", "y", "z"]}
        response = s.post(baseurl, data=json.dumps(payload, sort_keys=True), headers=headers)
        return response.json()

    def put0(self, s, baseurl):
        response = s.put(baseurl, data={'key': 'value'})
        return response.json()

    def delete0(self, s, baseurl):
        response = s.delete(baseurl)
        return response.content

    def head0(self, s, baseurl):
        response = s.head(baseurl)
        return response.content

    def options0(self, s, baseurl):
        response = s.options(baseurl)
        return response.content


class _HTTPlib2Accessing:
    def get0(self, http, baseurl):
        env, body = http.request(baseurl, method="GET")
        return json.loads(body.decode("utf-8"))


class RequestTraceMirrorTests(unittest.TestCase):
    def test_it(self):
        from reqtrace.tracelib.requests import create_factory as req_create_factory
        from reqtrace.tracelib.httplib2 import create_factory as httplib2_create_factory

        from reqtrace.mockserve.echohandler import echohandler
        from reqtrace.mockserve import create_app, create_server
        from reqtrace.tracelib.hooks import noop, trace

        from reqtrace.mockserve.mirrorhandler import create_mirrorhandler
        from reqtrace.util import find_freeport
        from reqtrace.tracelib.hooks import replay_redirect

        C = namedtuple("C", "trace, replay, method, msg")

        candidates = [
            C(trace="requests", replay="requests", method="get0", msg="GET /"),
            C(trace="requests", replay="httplib2", method="get0", msg="GET /"),
            C(trace="httplib2", replay="requests", method="get0", msg="GET /"),
            C(trace="requests", replay="requests", method="get1", msg="GET /?name=foo"),
            C(trace="requests", replay="requests", method="get2", msg="GET /?items=x&items=y&items=z"),
            C(trace="requests", replay="requests", method="post0", msg="POST /?q=foo"),
        ]

        response_store = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            port = find_freeport()
            baseurl = "http://localhost:{port}".format(port=port)

            client_registry = {
                "requests": req_create_factory(on_request=noop, on_response=trace(tmpdir))(),
                "httplib2": httplib2_create_factory(on_request=noop, on_response=trace(tmpdir))(),
            }
            accessing_registry = {
                "requests": _RequestAccessing(),
                "httplib2": _HTTPlib2Accessing(),
            }

            with create_server(create_app(echohandler), port=port) as httpd:
                th = threading.Thread(target=httpd.serve_forever, daemon=True)
                th.start()
                import logging
                logging.basicConfig(level=logging.INFO)

                for c in candidates:
                    if (c.trace, c.msg) in response_store:
                        continue
                    accessing = accessing_registry[c.trace]
                    client = client_registry[c.trace]
                    response_store[(c.trace, c.msg)] = getattr(accessing, c.method)(client, baseurl)
                httpd.shutdown()

            mirrorhandler = create_mirrorhandler(tmpdir)
            port2 = find_freeport()
            mirrorurl = "http://localhost:{}".format(port2)

            # yapf:disable
            replay_client_registry = {
                "requests": req_create_factory(on_request=replay_redirect(mirrorurl), on_response=noop)(),
                "httplib2": httplib2_create_factory(on_request=replay_redirect(mirrorurl), on_response=noop)(),
            }
            # yapf:enable

            with create_server(create_app(mirrorhandler), port=port2) as httpd:
                th = threading.Thread(target=httpd.serve_forever, daemon=True)
                th.start()
                for c in candidates:
                    with self.subTest(msg=c.msg, trace=c.trace, replay=c.replay):
                        client = replay_client_registry[c.replay]
                        accessing = accessing_registry[c.replay]
                        replay_response = getattr(accessing, c.method)(client, baseurl)
                        trace_response = response_store[(c.trace, c.msg)]

                        # xxx:
                        for k in ["user_agent", "connection", "accept"]:
                            trace_response.pop(k, None)
                            replay_response.pop(k, None)

                        self.assertDictEqual(trace_response, replay_response)

                httpd.shutdown()


# TODO: trace=requests, replay=httplib2,requests
# TODO: trace=httplib2, replay=httplib2,requests
# TODO: trace=googleapi, replay=googleapi

if __name__ == "__main__":
    unittest.main()
