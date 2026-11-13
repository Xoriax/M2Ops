import json
from pathlib import Path

import pytest

from collector import alert
from collector.sources import load_sources

ROOT = Path(__file__).parent.parent


def test_sources_csv_has_the_8_sources():
    sources = load_sources(ROOT / "config" / "sources.csv")
    assert len(sources) == 8
    assert {s["type"] for s in sources} == {"PQN", "PQR"}
    assert all(s["feed_url"].startswith("https://") for s in sources)


def test_sources_csv_rejects_missing_column(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("name,type,region,feed_url\nX,PQN,national,\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_sources(f)


def test_no_alert_when_all_ok():
    assert alert.build_message(0, {"sources": {"A": {"status": "ok"}, "B": {"status": "not_modified"}}}) is None


def test_partial_failure_lists_failed_sources():
    msg = alert.build_message(0, {"sources": {"A": {"status": "ok"}, "B": {"status": "error", "error": "HTTP 503"}}})
    assert "partielle" in msg and "B : HTTP 503" in msg


def test_crash_without_last_run_still_alerts():
    assert "code 2" in alert.build_message(2, {})


def test_alert_posts_to_webhook(tmp_path, monkeypatch):
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "last_run.json").write_text(
        json.dumps({"sources": {"B": {"status": "error", "error": "boom"}}}), encoding="utf-8")
    sent = {}
    monkeypatch.setattr(alert, "DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://hooks.example/x")

    class R:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(alert.requests, "post", lambda url, **kw: sent.update(url=url, **kw) or R())
    assert alert.main(["alert", "1"]) == 0
    body = json.loads(sent["data"])
    assert sent["url"] == "https://hooks.example/x" and "boom" in body["text"] and body["content"] == body["text"]
