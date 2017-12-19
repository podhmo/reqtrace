import logging
import os.path
import json
from collections import OrderedDict
logger = logging.getLogger(__name__)

# todo refactoring


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
        d["request"] = response.request.__json__()
        d["response"] = response.__json__()
        if not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        outpath = os.path.join(
            dirpath, "{}{}_{}.json".format(no, response.request.method.lower(), filename)
        )
        with open(outpath, "w") as wf:
            json.dump(d, wf, sort_keys=True, indent=2, ensure_ascii=False)

    return _trace
