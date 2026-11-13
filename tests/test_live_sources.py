"""Test en ligne : chaque source passe par la vraie pipeline (collect_source) et on
recupere la derniere news publiee. Desactive par defaut (pytest reste hors ligne).

    RUN_LIVE=1 python -m pytest tests/test_live_sources.py -s
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from collector.collect import collect_source
from collector.sources import load_sources
from collector.storage import FileStorage

SOURCES = load_sources(Path(__file__).parent.parent / "config" / "sources.csv")

pytestmark = pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="test en ligne : definir RUN_LIVE=1")


@pytest.mark.parametrize("source", SOURCES, ids=[s["name"] for s in SOURCES])
def test_latest_news_through_pipeline(source, tmp_path):
    now = datetime.now(timezone.utc)
    store = FileStorage(tmp_path)
    report = collect_source(source, store, {}, now)
    assert report["status"] == "ok", report["error"]
    rows = report.pop("_rows")
    assert rows, "flux sans entree exploitable"

    dated = [r for r in rows if r["published_at_utc"]]
    assert dated, "aucune entree datee"
    latest = max(dated, key=lambda r: r["published_at_utc"])
    print(f"\n[{source['name']}] {latest['published_at_utc']}\n  {latest['title']}\n  {latest['url']}")

    assert latest["title"] and latest["url"].startswith("http") and len(latest["url_hash"]) == 64
    assert now - datetime.fromisoformat(latest["published_at_utc"]) < timedelta(days=7)
    assert (tmp_path / "bronze").exists()
    # silver : ecriture puis idempotence
    day = now.strftime("%Y-%m-%d")
    assert store.append_silver(day, rows) == len({r["url_hash"] for r in rows})
    assert store.append_silver(day, rows) == 0
