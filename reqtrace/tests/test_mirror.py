import unittest
import json
import tempfile
import threading


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


class RequestTraceMirrorTests(unittest.TestCase):
    def test_it(self):
        from reqtrace.tracelib.requests import create_factory
        from reqtrace.tracelib.hooks import noop, trace

        from reqtrace.mockserve.echohandler import echohandler
        from reqtrace.mockserve import create_app, create_server

        from reqtrace.mockserve.mirrorhandler import create_mirrorhandler
        from reqtrace.util import find_freeport

        accessing = _RequestAccessing()

        with tempfile.TemporaryDirectory() as tmpdir:
            port = find_freeport()
            baseurl = "http://localhost:{port}".format(port=port)
            httpd = create_server(create_app(echohandler), port=port)
            th = threading.Thread(target=httpd.serve_forever, daemon=True)
            th.start()
            import logging
            logging.basicConfig(level=logging.INFO)

            trace_session = create_factory(on_request=noop, on_response=trace(tmpdir))()
            trace_response = accessing.get0(trace_session, baseurl)

            mirrorhandler = create_mirrorhandler(tmpdir)
            port2 = find_freeport()
            mirrorurl = "http://localhost:{}".format(port2)

            def replay_redirect(request):
                request.modify_url("{}?_origin=localhost:{port}".format(mirrorurl, port=port))

            httpd = create_server(create_app(mirrorhandler), port=port2)
            th = threading.Thread(target=httpd.serve_forever, daemon=True)
            th.start()

            # get0

            replay_session = create_factory(on_request=replay_redirect, on_response=noop)()
            replay_response = accessing.get0(replay_session, mirrorurl)
            self.assertDictEqual(trace_response, replay_response)


# TODO: trace=requests, replay=httplib2,requests
# TODO: trace=httplib2, replay=httplib2,requests
# TODO: trace=googleapi, replay=googleapi

if __name__ == "__main__":
    unittest.main()
