import unittest
import requests
from reqtrace.testing import background_server


class MockServerTests(unittest.TestCase):
    def _makeOne(self, *args, **kwargs):
        from reqtrace.mockserve import create_app
        return create_app(*args, **kwargs)

    def test_200_text(self):
        def callback(environ):
            return "ok"

        with background_server(self._makeOne(callback)) as url:
            response = requests.get(url)
            self.assertEqual(200, response.status_code)
            self.assertEqual("ok", response.text)

    def test_404_text(self):
        def callback(environ):
            return "hmm", 404

        with background_server(self._makeOne(callback)) as url:
            response = requests.get(url)
            self.assertEqual(404, response.status_code, 404)
            self.assertEqual("hmm", response.text)

    def test_200_json(self):
        def callback(environ):
            return {"message": "ok"}

        with background_server(self._makeOne(callback)) as url:
            response = requests.get(url)
            self.assertEqual(200, response.status_code)
            self.assertEqual({"message": "ok"}, response.json())
