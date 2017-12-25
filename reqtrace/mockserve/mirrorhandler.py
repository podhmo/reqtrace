import logging
import json
import os
import hashlib
import urllib.parse as parselib
from .echohandler import _extract_body

logger = logging.getLogger(__name__)


def genkey(extractor, source):
    d = {}
    d.update(extractor.extract_urlinfo(source))
    d.update(extractor.extract_body(source))
    s = json.dumps(d, sort_keys=True).encode("utf-8")
    return hashlib.sha224(s).hexdigest()


class RequestInfoExtractor:
    def __init__(self, origin_host_key, encoding="utf-8"):
        self.origin_host_key = origin_host_key
        self.encoding = encoding

    def extract_urlinfo(self, environ):
        queries = []
        origin = None
        origin_k = self.origin_host_key
        for pair in parselib.parse_qsl(environ["QUERY_STRING"]):
            if pair[0] == origin_k:
                origin = parselib.unquote_plus(pair[1])
            else:
                queries.append(pair)
        return {
            "method": environ["REQUEST_METHOD"],
            "host": origin or environ["HTTP_HOST"],
            "path": environ["PATH_INFO"],
            "query": sorted(queries),
        }

    def extract_body(self, environ):
        return _extract_body(environ, encoding=self.encoding)


class TracedDataExtractor:
    def extract_urlinfo(self, data):
        parsed = parselib.urlparse(data["request"]["url"])
        return {
            "method": data["request"]["method"],
            "host": parsed.netloc,
            "path": parsed.path,
            "query": sorted(parselib.parse_qsl(parsed.query)),
        }

    def extract_body(self, data):
        d = {}
        request_data = data["request"]
        for k in ["body"]:
            if k in request_data:
                headers = request_data["headers"]
                if "json" in headers.get("Content-Type", "") or "json" in headers.get("content-type", ""):
                    d[k] = json.loads(request_data[k])
                else:
                    d[k] = sorted(parselib.parse_qsl(request_data[k]))
        return d


def create_mirrorhandler(
    inputdir=".",
    *,
    matcher=lambda x: x.endswith(".json"),
    loader=json.load,
    origin_host_key="_origin"
):
    store = {}
    extractor_for_data = TracedDataExtractor()
    for entry in os.scandir(inputdir):
        if entry.is_file() and matcher(entry.path):
            with open(entry.path) as rf:
                d = loader(rf)
            k = genkey(extractor_for_data, d)
            logger.info("generate key: %s (from %s)", k, entry.path)
            store[k] = d["response"]

    def handler(environ, store=store, extractor=RequestInfoExtractor(origin_host_key)):
        k = genkey(extractor, environ)

        fmt = "generate key: %s (from request method=%s, path=%s)"
        logger.info(fmt, k, environ["REQUEST_METHOD"], environ["PATH_INFO"])

        if k not in store:
            return {"k": k}, 404

        response_dict = store[k]
        status_code = response_dict["status_code"]
        headers = list(response_dict["headers"].items())

        if "/json" in response_dict["headers"].get("Content-Type", ""):
            return response_dict["body"], status_code, headers
        else:
            return response_dict.get("body", ""), status_code, headers

    return handler
