import unittest
import requests
from reqtrace.testing import background_server


class MockServerTests(unittest.TestCase):
    def _makeOne(self, *args, **kwargs):
        from reqtrace.mockserve import create_app
        return create_app(*args, **kwargs)

    def test_text(self):
        candidates = [
            ("ok", 200),
            ("hmm", 404),
        ]
        for (body, code) in candidates:

            def callback(environ):
                return body, code

            with self.subTest(body=body, code=code):
                with background_server(self._makeOne(callback)) as url:
                    response = requests.get(url)
                    self.assertEqual(code, response.status_code)
                    self.assertEqual(body, response.text)

    def test_json(self):
        candidates = [
            ({
                "message": "ok"
            }, 200),
            ({
                "message": "not found"
            }, 404),
        ]
        for (body, code) in candidates:

            def callback(environ):
                return body, code

            with self.subTest(body=body, code=code):
                with background_server(self._makeOne(callback)) as url:
                    response = requests.get(url)
                    self.assertEqual(code, response.status_code)
                    self.assertEqual(body, response.json())
