"""Verifie que chaque flux repond et est frais : python -m collector.check_feeds"""
import sys
from datetime import datetime, timedelta, timezone

import feedparser

from collector.fetch import fetch_feed
from collector.sources import load_sources

MAX_AGE = timedelta(days=7)


def entry_dates(parsed):
    out = []
    for e in parsed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        if t:
            out.append(datetime(*t[:6], tzinfo=timezone.utc))
    return out


def main():
    sources = load_sources()
    failures = 0
    for s in sources:
        res = fetch_feed(s["feed_url"])
        if res.status != "ok":
            print(f"[ERREUR] {s['name']}: {res.error} (HTTP {res.http_code})")
            failures += 1
            continue
        parsed = feedparser.parse(res.content)
        dates = entry_dates(parsed)
        n = len(parsed.entries)
        newest = max(dates) if dates else None
        oldest = min(dates) if dates else None
        problem = None
        if n == 0:
            problem = "flux vide"
        elif newest is None or datetime.now(timezone.utc) - newest > MAX_AGE:
            problem = "derniere entree > 7 jours ou sans date"
        tag = "ERREUR" if problem else "OK"
        print(f"[{tag}] {s['name']}: HTTP {res.http_code}, {n} entrees, "
              f"plus recente {newest}, plus ancienne {oldest}" + (f" ({problem})" if problem else ""))
        failures += bool(problem)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
