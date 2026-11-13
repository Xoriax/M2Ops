"""Catalogue des sources : config/sources.csv (name, type, region, feed_url)."""
import csv
import os
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("SOURCES_FILE", "config/sources.csv"))
REQUIRED = ("name", "type", "region", "feed_url")


def load_sources(path=None):
    with Path(path or DEFAULT_PATH).open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        missing = [c for c in REQUIRED if not (r.get(c) or "").strip()]
        if missing:
            raise ValueError(f"source invalide {r!r} : colonnes manquantes {missing}")
    return [{c: r[c].strip() for c in REQUIRED} for r in rows]
