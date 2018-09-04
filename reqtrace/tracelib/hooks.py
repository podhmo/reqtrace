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

        try:
            with open(jsonpath, "w") as wf:
                json.dump(d, wf, sort_keys=True, indent=2, ensure_ascii=False, default=_convert)
        except Exception as e:
            try:
                d = _fix_dict(d)
                with open(jsonpath, "w") as wf:
                    json.dump(d, wf, sort_keys=True, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning("invalid data (saving as pickle)", exc_info=True)
                body = d["response"].pop("body")
                picklename = os.path.join(dirpath, "{}response.pickle".format(no))
                d["response"]["body"] = os.path.basename(picklename)
                with open(picklename, "wb") as wf:
                    pickle.dump(body, wf)

    return _trace


def _fix_dict(o, encoding="utf-8"):
    if hasattr(o, "decode"):
        return o.decode(encoding)
    elif isinstance(o, (list, tuple)):
        return [_fix_dict(x) for x in o]
    elif hasattr(o, "keys"):
        return {_fix_dict(k): _fix_dict(v) for k, v in o.items()}
    else:
        return o


def _convert(o, encoding="utf-8"):
    if hasattr(o, "decode"):
        return o.decode(encoding)
    raise TypeError("{!r} is not JSON serializable".format(o))
