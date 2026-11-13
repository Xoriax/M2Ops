"""Cree (une seule fois) l'evenement Cronicle : collecte quotidienne a 7h Europe/Paris."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:3012/api"
EVENT_ID = "gazettecollect"
EVENT = {
    "id": EVENT_ID,
    "title": "Gazette : collecte quotidienne",
    "enabled": 1,
    "category": "general",
    "plugin": "shellplug",
    "target": "maingrp",
    "timezone": "Europe/Paris",
    "timing": {"hours": [7], "minutes": [0]},
    "catch_up": 1,       # rattrapage : relance les runs rates si la machine etait eteinte
    "max_children": 1,   # jamais deux collectes en parallele
    "retries": 0,
    "timeout": 1800,
    "params": {"script": "#!/bin/sh\ncd /app && exec python -m collector.collect\n",
               "annotate": 1, "json": 0},
}


def call(path, payload=None, params=None):
    url = f"{BASE}/{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def main():
    password = os.environ["CRONICLE_ADMIN_PASSWORD"]
    for _ in range(90):  # Cronicle met jusqu'a ~1 min a devenir primaire
        try:
            res = call("user/login", {"username": "admin", "password": password})
            if res.get("code") == 0:
                break
            # identifiants refuses : on s'arrete (reessayer verrouillerait le compte)
            print(f"[bootstrap] login refuse : {res.get('description')}", file=sys.stderr)
            return 1
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(2)
    else:
        print("[bootstrap] Cronicle injoignable", file=sys.stderr)
        return 1
    sid = res["session_id"]
    for _ in range(60):  # attend d'etre primaire (create_event refuse sinon)
        existing = call("app/get_event/v1", params={"id": EVENT_ID, "session_id": sid})
        if existing.get("code") == 0:
            print("[bootstrap] evenement deja present")
            return 0
        created = call("app/create_event/v1", {**EVENT, "session_id": sid})
        if created.get("code") == 0:
            print("[bootstrap] evenement cree (7h Europe/Paris, catch-up)")
            return 0
        print(f"[bootstrap] attente : {created.get('description')}")
        time.sleep(3)
    return 1


if __name__ == "__main__":
    sys.exit(main())
