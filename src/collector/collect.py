"""Point d'entree : python -m collector.collect"""
import os
import sys
import time
from datetime import datetime, timezone

import feedparser
import requests

from collector.fetch import fetch_feed
from collector.normalize import normalize_entry
from collector.sources import load_sources
from collector.storage import FileStorage

DATA_DIR = os.environ.get("DATA_DIR", "data")
PAUSE_BETWEEN_SOURCES = 1.0


def bronze_entry(e):
    """Champs bruts utiles uniquement : ni contenu integral ni auteur."""
    return {"title": e.get("title"), "link": e.get("link"), "summary": e.get("summary"),
            "published": e.get("published") or e.get("updated"), "id": e.get("id")}


def collect_source(source, store, etags, now):
    t0 = time.monotonic()
    cached = etags.get(source["name"], {})
    res = fetch_feed(source["feed_url"], cached.get("etag"), cached.get("last_modified"))
    report = {"status": res.status, "http_code": res.http_code, "entries": 0,
              "error": res.error}
    rows = []
    if res.status == "ok":
        parsed = feedparser.parse(res.content)
        if parsed.bozo and not parsed.entries:
            report.update(status="error", error=f"flux illisible: {parsed.bozo_exception}")
        else:
            rows = [r for e in parsed.entries if (r := normalize_entry(e, source, now))]
            report["entries"] = len(rows)
            store.write_bronze(now.strftime("%Y-%m-%d"), source["name"], {
                "feed_url": source["feed_url"], "collected_at_utc": now.isoformat(),
                "http_code": res.http_code, "entries": [bronze_entry(e) for e in parsed.entries]})
            etags[source["name"]] = {"etag": res.etag, "last_modified": res.last_modified}
    report["_rows"] = rows
    report["duration_s"] = round(time.monotonic() - t0, 2)
    return report


def main():
    started = datetime.now(timezone.utc)
    sources = load_sources()
    store = FileStorage(DATA_DIR)
    etags = store.read_state("etags.json")
    day = started.strftime("%Y-%m-%d")
    reports, all_rows = {}, []

    for i, s in enumerate(sources):
        if i:
            time.sleep(PAUSE_BETWEEN_SOURCES)
        try:
            rep = collect_source(s, store, etags, started)
        except Exception as exc:  # une source ne bloque jamais les autres
            rep = {"status": "error", "http_code": None, "entries": 0,
                   "error": f"{type(exc).__name__}: {exc}", "duration_s": 0, "_rows": []}
        all_rows.extend(rep.pop("_rows"))
        reports[s["name"]] = rep
        print(f"{s['name']}: {rep['status']} ({rep['entries']} entrees)")

    new = store.append_silver(day, all_rows)
    store.write_state("etags.json", etags)
    ok = any(r["status"] in ("ok", "not_modified") for r in reports.values())
    store.write_state("last_run.json", {
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "success": ok, "new_rows": new, "sources": reports})
    print(f"{new} nouvelles lignes silver")

    url = os.environ.get("HEALTHCHECK_URL")
    if ok and url:
        try:
            requests.get(url, timeout=10)
        except requests.RequestException as exc:
            print(f"healthcheck ping echoue: {exc}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
