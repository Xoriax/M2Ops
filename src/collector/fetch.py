"""Telechargement d'un flux RSS/Atom (retries, requete conditionnelle)."""
import time
from dataclasses import dataclass, field

import requests

USER_AGENT = "M2Ops-Gazette/0.1 (projet pedagogique EFREI)"
TIMEOUT = (10, 20)
BACKOFFS = (1, 4)  # 3 essais au total : attentes de 1 s puis 4 s (10 s si un 4e essai est ajoute)


@dataclass
class FetchResult:
    status: str  # ok, not_modified, error
    http_code: int | None = None
    content: bytes = b""
    etag: str | None = None
    last_modified: str | None = None
    error: str | None = None
    attempts: int = 0
    headers: dict = field(default_factory=dict)


def fetch_feed(url, etag=None, last_modified=None, session=None, sleep=time.sleep):
    """Telecharge un flux. 3 essais, attente croissante sur erreur reseau et 5xx."""
    http = session or requests
    headers = {"User-Agent": USER_AGENT,
               "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    last_error, code = None, None
    for attempt in range(len(BACKOFFS) + 1):
        if attempt:
            sleep(BACKOFFS[attempt - 1])
        try:
            r = http.get(url, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as exc:
            last_error, code = f"{type(exc).__name__}: {exc}", None
            continue
        code = r.status_code
        if code == 304:
            return FetchResult("not_modified", 304, attempts=attempt + 1, etag=etag, last_modified=last_modified)
        if code >= 500:
            last_error = f"HTTP {code}"
            continue
        if code >= 400:
            return FetchResult("error", code, error=f"HTTP {code}", attempts=attempt + 1)
        return FetchResult("ok", code, content=r.content, etag=r.headers.get("ETag"),
                           last_modified=r.headers.get("Last-Modified"), attempts=attempt + 1)
    return FetchResult("error", code, error=last_error, attempts=len(BACKOFFS) + 1)
