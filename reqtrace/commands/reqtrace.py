import sys
import logging
import os.path
import shutil
import uuid
import argparse
from functools import partial
from importlib.util import spec_from_file_location
from importlib.machinery import SourceFileLoader
from magicalimport import import_symbol
from reqtrace.tracelib.hooks import trace
from reqtrace.tracelib.requests import monkeypatch as monkeypatch_requests
from reqtrace.tracelib.httplib2 import monkeypatch as monkeypatch_httplib2

logger = logging.getLogger(__name__)


def call_file(fname, extras):
    sys.argv = [fname]
    sys.argv.extend(extras)
    if ":" in fname:
        return import_symbol(fname, cwd=True)()
    elif os.path.exists(fname) and not os.path.isdir(fname):
        # for: python <file>
        spec = spec_from_file_location("__main__", fname)
        return SourceFileLoader("__main__", spec.origin).load_module()

    cmd_path = shutil.which(fname)
    if cmd_path:
        return SourceFileLoader("__main__", cmd_path).load_module()
    else:
        raise RuntimeError("{} is not found".format(fname))


def noop(request):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--outdir", default="./roundtrips")
    parser.add_argument("--with-uid", action="store_true")
    parser.add_argument(
        "--logging", choices=list(logging._nameToLevel.keys()), default="INFO"
    )
    parser.add_argument(
        "--enable",
        dest="enables",
        action="append",
        choices=["requests", "httplib2"],
        default=None,
    )

    args, extras = parser.parse_known_args()
    logging.basicConfig(level=args.logging)
    if args.with_uid:
        args.outdir = os.path.join(args.outdir, uuid.uuid4().hex[:8])

    logger.info("outdir is %s", args.outdir)
    usepip = args.command.strip() == "pip"

    hook = trace(dirpath=args.outdir)
    enables = args.enables or ["requests", "httplib2"]

    for module_name in enables:
        logger.info("monkey patching for %s", module_name)
        monkeypatch = globals()[f"monkeypatch_{module_name}"]
        if module_name == "requests":
            monkeypatch = partial(monkeypatch, pip=usepip)
        monkeypatch(on_request=noop, on_response=hook)

    call_file(args.command, extras)
