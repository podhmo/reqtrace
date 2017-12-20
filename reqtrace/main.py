import sys
import logging
import os.path
import shutil
import uuid
import argparse
from importlib.util import (
    spec_from_file_location,
    module_from_spec,
)
from importlib.machinery import SourceFileLoader
from magicalimport import import_symbol
from reqtrace.tracelib.hooks import trace
from reqtrace.tracelib.requests import monkeypatch as monkeypatch_requests
logger = logging.getLogger(__name__)


def call_file(fname, extras):
    sys.argv = [fname]
    sys.argv.extend(extras)
    if ":" in fname:
        return import_symbol(fname)()
    elif os.path.exists(fname) and not os.path.isdir(fname):
        spec = spec_from_file_location("__main__", fname)
        module = module_from_spec(spec)
        code = spec.loader.get_code(module.__name__)
        return exec(code, module.__dict__)

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
    parser.add_argument("--logging", choices=list(logging._nameToLevel.keys()), default="INFO")

    args, extras = parser.parse_known_args()
    logging.basicConfig(level=args.logging)
    if args.with_uid:
        args.outdir = os.path.join(args.outdir, uuid.uuid4().hex[:8])
    logger.info("outdir is %s", args.outdir)
    usepip = args.command.strip() == "pip"
    monkeypatch_requests(on_request=noop, on_response=trace(dirpath=args.outdir), pip=usepip)
    call_file(args.command, extras)
