"""Nettoyage des entrees : URL canonique, hash, extrait, dates UTC."""
import hashlib
import html
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

EXCERPT_MAX = 500
RECENT_WINDOW = timedelta(hours=24)
TRACKING_PARAMS = {"ocid", "eafs_enabled", "gclid", "fbclid", "mc_cid", "mc_eid", "cmpid",
                   "smid", "smtyp", "referrer", "ref", "taid", "partner", "outputtype"}
COLUMNS = ["source", "type", "region", "title", "excerpt", "url", "url_hash",
           "published_at_utc", "collected_at_utc", "is_recent"]

_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")


def canonical_url(url):
    parts = urlsplit((url or "").strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), ""))


def url_hash(canonical):
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def clean_text(text):
    text = html.unescape(_TAG.sub(" ", text or ""))
    return _SPACES.sub(" ", text).strip()


def make_excerpt(summary):
    text = clean_text(summary)
    if len(text) <= EXCERPT_MAX:
        return text
    return text[:EXCERPT_MAX - 3].rstrip() + "..."


def parse_date(struct_time):
    """struct_time UTC de feedparser -> datetime UTC, ou None (on n'invente rien)."""
    if not struct_time:
        return None
    try:
        return datetime(*struct_time[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def normalize_entry(entry, source, collected_at):
    """Retourne une ligne (dict) ou None si l'entree n'a ni lien ni titre."""
    link = entry.get("link")
    title = clean_text(entry.get("title"))
    if not link or not title:
        return None
    url = canonical_url(link)
    published = parse_date(entry.get("published_parsed") or entry.get("updated_parsed"))
    is_recent = bool(published and timedelta(0) <= collected_at - published < RECENT_WINDOW)
    return {
        "source": source["name"], "type": source["type"], "region": source["region"],
        "title": title, "excerpt": make_excerpt(entry.get("summary")),
        "url": url, "url_hash": url_hash(url),
        "published_at_utc": published.isoformat() if published else "",
        "collected_at_utc": collected_at.isoformat(),
        "is_recent": is_recent,
    }
