"""Alerte par webhook (sans SMTP) : python -m collector.alert <code_de_sortie_de_collect>

Poste un message JSON sur ALERT_WEBHOOK_URL si le run a echoue ou si au moins une source est en erreur.
Le corps contient "text" (Slack, Mattermost, Teams) et "content" (Discord).
Sans ALERT_WEBHOOK_URL, ne fait rien.
"""
import json
import os
import sys
from pathlib import Path

import requests

DATA_DIR = os.environ.get("DATA_DIR", "data")


def build_message(exit_code, last_run):
    failed = {n: s.get("error") or f"HTTP {s.get('http_code')}"
              for n, s in last_run.get("sources", {}).items() if s.get("status") == "error"}
    if exit_code == 0 and not failed:
        return None
    lines = ["Gazette : collecte en echec" if exit_code else "Gazette : collecte partielle"]
    lines += [f"- {name} : {err}" for name, err in failed.items()]
    if exit_code and not failed:
        lines.append(f"- le script s'est termine avec le code {exit_code} (voir les logs Cronicle)")
    return "\n".join(lines)


def main(argv):
    exit_code = int(argv[1]) if len(argv) > 1 else 0
    try:
        last_run = json.loads((Path(DATA_DIR) / "state" / "last_run.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        last_run = {}
    message = build_message(exit_code, last_run)
    if message is None:
        return 0
    print(message)
    url = os.environ.get("ALERT_WEBHOOK_URL")
    if not url:
        print("ALERT_WEBHOOK_URL non defini : alerte non envoyee")
        return 0
    try:
        requests.post(url, data=json.dumps({"text": message, "content": message}),
                      headers={"Content-Type": "application/json"}, timeout=10).raise_for_status()
    except requests.RequestException as exc:
        print(f"envoi de l'alerte impossible : {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
