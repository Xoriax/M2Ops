"""Stockage bronze/silver. Interface isolee : remplacable par MinIO/SQL sans toucher collect.py."""
import csv
import json
import os
from pathlib import Path

from collector.normalize import COLUMNS


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="")
    os.replace(tmp, path)


def _slug(name):
    return "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")


class FileStorage:
    def __init__(self, root="data"):
        self.root = Path(root)

    def write_bronze(self, day, source_name, payload):
        _atomic_write(self.root / "bronze" / day / f"{_slug(source_name)}.json",
                      json.dumps(payload, ensure_ascii=False, indent=2))

    def known_hashes(self):
        """Tous les url_hash deja presents dans silver (tous les jours)."""
        seen = set()
        for f in (self.root / "silver").glob("*.csv"):
            with f.open(encoding="utf-8", newline="") as fh:
                seen.update(r["url_hash"] for r in csv.DictReader(fh))
        return seen

    def append_silver(self, day, rows):
        """Ajoute les lignes dont url_hash est inconnu. Retourne le nombre ajoute."""
        seen, new = self.known_hashes(), []
        for r in rows:
            if r["url_hash"] not in seen:
                seen.add(r["url_hash"])
                new.append(r)
        if not new:
            return 0
        path = self.root / "silver" / f"{day}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        exists = path.exists()
        with path.open("a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS)
            if not exists:
                w.writeheader()
            w.writerows(new)
        return len(new)

    def read_state(self, name):
        p = self.root / "state" / name
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write_state(self, name, data):
        _atomic_write(self.root / "state" / name, json.dumps(data, ensure_ascii=False, indent=2))
