import logging
import os.path
import json
import pickle
from collections import OrderedDict
logger = logging.getLogger(__name__)


# todo refactoring
def noop(target):
    pass


def trace(dirpath=None, logger=logger):
    """ on response hook, tracing request and response"""
    i = 0
    dirpath = dirpath or "."

    def _trace(response):
        logger.info("traced %s", response.url)
        nonlocal i
        filename = response.url.replace("/", "_")
        no = "{:04}".format(i)
        i += 1
        d = OrderedDict()
        d["request"] = response.request.__serialize__()
        d["response"] = response.__serialize__()
        if not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        request_method = response.request.method.lower()
        jsonpath = os.path.join(dirpath, "{}{}_{}.json".format(no, request_method, filename))

        if d["request"].get("pickle", False):
            body = d["request"].pop("body")
            picklename = os.path.join(dirpath, "{}request.pickle".format(no))
            d["request"]["body"] = os.path.basename(picklename)
            with open(picklename, "wb") as wf:
                pickle.dump(body, wf)

        if d["response"].get("pickle", False):
            body = d["response"].pop("body")
            picklename = os.path.join(dirpath, "{}response.pickle".format(no))
            d["response"]["body"] = os.path.basename(picklename)
            with open(picklename, "wb") as wf:
                pickle.dump(body, wf)

        with open(jsonpath, "w") as wf:
            json.dump(d, wf, sort_keys=True, indent=2, ensure_ascii=False, default=_convert)

    return _trace


def _convert(o, encoding="utf-8"):
    if hasattr(o, "decode"):
        return o.decode(encoding)
    raise TypeError("{!r} is not JSON serializable".format(o))
