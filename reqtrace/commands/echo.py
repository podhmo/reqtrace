import argparse
import logging
import magicalimport
from reqtrace.mockserve import create_app, create_server
from reqtrace.mockserve.echohandler import echohandler


def pdb_callback(fn):
    def _call(environ):
        import pdb
        pdb.set_trace()
        return fn(environ)

    return _call


def run(*, port, callback, pretty=False):
    handler = echohandler
    if callback:
        handler = callback(handler)

    app = create_app(handler, content_type="application/json", pretty=pretty)
    with create_server(app, port=port) as httpd:
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None, type=int)
    parser.add_argument("--logging", choices=list(logging._nameToLevel.keys()), default="DEBUG")
    parser.add_argument("--callback", default=None)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--pdb", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=args.logging)
    callback = args.callback
    if callback is not None:
        callback = magicalimport.import_symbol(callback, cwd=True)
    elif args.pdb:
        callback = pdb_callback
    run(port=args.port, callback=callback, pretty=args.pretty)


if __name__ == "__main__":
    main()
