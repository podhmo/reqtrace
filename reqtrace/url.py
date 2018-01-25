import urllib.parse as parselib

# todo: support params (e.g. %s;%s)


def append_queries(url, **queries):
    parsed = parselib.urlparse(url)
    q = merge_query(parsed.query, queries)
    return parselib.urlunparse(parsed._replace(query=q))


def merge_url(src_url, dst_url, *, replace=False, fullreplace=False):
    src_parsed = parselib.urlparse(src_url)
    dst_parsed = parselib.urlparse(dst_url)
    q = merge_query(src_parsed.query, dst_parsed.query, replace=replace, fullreplace=fullreplace)
    return parselib.urlunparse(dst_parsed._replace(query=q))


def merge_query(src_query, dst_query, *, replace=False, fullreplace=False):  # default is append
    if fullreplace or not src_query:
        if hasattr(dst_query, "keys"):
            return parselib.urlencode(dst_query)
        else:
            return dst_query
    elif not dst_query:
        return src_query
    elif replace:
        if hasattr(dst_query, "keys"):
            qd = dst_query
        else:
            qd = parselib.parse_qs(dst_query)

        for name, value in parselib.parse_qsl(src_query):
            if name not in qd:
                qd[name] = value
        return parselib.urlencode(qd)
    else:
        qsl = parselib.parse_qsl(src_query)
        if hasattr(dst_query, "keys"):
            qsl.extend(dst_query.items())
        else:
            qsl.extend(parselib.parse_qsl(dst_query))
        return parselib.urlencode(qsl)
