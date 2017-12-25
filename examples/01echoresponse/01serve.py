import os.path
import urllib.parse as parselib
import logging
import threading
import requests
from reqtrace.mockserve import create_server, create_app
from reqtrace.mockserve.mirrorhandler import create_mirrorhandler
from reqtrace.tracelib.requests import monkeypatch


def main():
    dirpath = os.path.join(os.path.dirname(__file__), "data/00requests/")
    mirrorhandler = create_mirrorhandler(dirpath)
    port = 55555

    origin_host = "localhost:4444"

    def mirror_redirect(request):
        request.modify_url(
            "http://localhost:55555?_origin={}".format(parselib.quote_plus(origin_host))
        )

    with create_server(create_app(mirrorhandler), port=port) as httpd:
        # th = threading.Thread(target=httpd.serve_forever, daemon=True)
        # th.start()
        # monkeypatch(on_request=mirror_redirect, on_response=print)
        # requests.get("http://localhost:4444/")
        httpd.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    main()
