from reqtrace.testlib.testing import background_server
from reqtrace.testlib.mockserve import create_app
from urllib3.connectionpool import ConnectionPool
import requests


def callback(environ):
    return "ok"


# with background_server(create_app(callback)) as url:
if True:
    original_init = ConnectionPool.__init__

    def init(self, host, port=None):
        # host_and_port = url.replace("https://", "http://").replace("http://", "")
        # host, port = host_and_port.rsplit(":", 1)
        host, port = "www.google.co.jp", None
        print("@", "@", host, port)
        original_init(self, host, port=port)

    ConnectionPool.__init__ = init

    # response = requests.get("https://www.google.co.jp")
    response = requests.get("https://pod.hatenablog.com/")

    print(response.text)
