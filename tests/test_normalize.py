from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

from collector.fetch import fetch_feed
from collector.normalize import EXCERPT_MAX, canonical_url, make_excerpt, normalize_entry, url_hash
from collector.storage import FileStorage

FIX = Path(__file__).parent / "fixtures"
SRC = {"name": "Demo", "type": "PQN", "region": "national"}
NOW = datetime(2026, 11, 13, 9, 0, tzinfo=timezone.utc)


def rows(fixture):
    parsed = feedparser.parse((FIX / fixture).read_bytes())
    return [r for e in parsed.entries if (r := normalize_entry(e, SRC, NOW))]


def test_canonical_url_strips_tracking_and_fragment():
    assert canonical_url("https://Example.com/a/1?utm_source=x&id=7&ocid=abc#frag") == "https://example.com/a/1?id=7"


def test_hash_is_stable_across_tracking_variants():
    a = url_hash(canonical_url("https://example.com/a?utm_medium=1"))
    b = url_hash(canonical_url("https://example.com/a#top"))
    assert a == b and len(a) == 64


def test_excerpt_truncated_and_cleaned():
    assert len(make_excerpt("mot " * 400)) <= EXCERPT_MAX
    assert make_excerpt("<p>a   <b>b</b> &amp; c</p>") == "a b & c"
    assert make_excerpt(None) == ""


def test_rss_row_without_full_text_and_recent():
    r = rows("sample_rss.xml")[0]
    assert r["title"] == "Premier article"
    assert r["excerpt"] == "Du texte gras & plus"
    assert r["published_at_utc"].startswith("2026-11-13T08:00:00")
    assert r["is_recent"] is True
    assert "INTEGRAL" not in str(r) and "Jane" not in str(r)


def test_missing_date_left_empty_and_entry_without_link_skipped():
    rs = rows("sample_rss.xml")
    assert len(rs) == 2
    assert rs[1]["published_at_utc"] == "" and rs[1]["is_recent"] is False


def test_atom_date_converted_to_utc():
    r = rows("sample_atom.xml")[0]
    assert r["published_at_utc"].startswith("2026-11-13T06:30:00")
    assert r["url"] == "https://example.org/x"


def test_silver_dedup_idempotent_across_days(tmp_path):
    store = FileStorage(tmp_path)
    rs = rows("sample_rss.xml")
    assert store.append_silver("2026-11-13", rs) == 2
    assert store.append_silver("2026-11-13", rs) == 0
    assert store.append_silver("2026-11-14", rs) == 0


class FakeResp:
    def __init__(self, code, content=b"x", headers=None):
        self.status_code, self.content, self.headers = code, content, headers or {}


class FakeSession:
    def __init__(self, *items):
        self.items, self.calls = list(items), 0

    def get(self, url, **kw):
        self.calls += 1
        it = self.items.pop(0)
        if isinstance(it, Exception):
            raise it
        return it


def test_fetch_retries_on_5xx_then_succeeds():
    s = FakeSession(FakeResp(503), requests.ConnectionError("boom"), FakeResp(200))
    waits = []
    res = fetch_feed("http://x", session=s, sleep=waits.append)
    assert res.status == "ok" and waits == [1, 4]


def test_fetch_gives_up_after_three_tries_and_304():
    s = FakeSession(*[FakeResp(500)] * 3)
    res = fetch_feed("http://x", session=s, sleep=lambda _: None)
    assert res.status == "error" and s.calls == 3
    assert fetch_feed("http://x", session=FakeSession(FakeResp(304)), sleep=lambda _: None).status == "not_modified"
