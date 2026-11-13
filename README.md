# M2Ops : La Gazette

Veille presse quotidienne : chaque matin, collecte de la presse americaine (PQN et PQR) via des flux RSS officiels, puis publication d'un resume des themes abordes. Ce depot contient le socle : collecteur, planificateur (Cronicle), Postgres, CI.

On ne garde que titre, extrait, lien et date. Jamais le texte integral, jamais de donnees personnelles.

## Lancer (deux commandes)

```
git clone https://github.com/Xoriax/M2Ops.git && cd M2Ops
bin/dev
```

`bin/dev` cree `.env` depuis `.env.example` au premier lancement, construit l'image et demarre Cronicle + Postgres. Prerequis : Docker (avec Compose).

- Interface Cronicle : http://localhost:3012 (utilisateur `admin`, mot de passe `CRONICLE_ADMIN_PASSWORD` du `.env`). L'evenement "Gazette : collecte quotidienne" (7h, Europe/Paris) est cree automatiquement ; "Run Now" pour lancer une collecte tout de suite.
- Resultats : `data/bronze/`, `data/silver/` (CSV deduplique), `data/state/last_run.json`.

## Tester

```
bin/test                                   # lint (ruff) + tests, hors ligne
RUN_LIVE=1 bin/test                        # + derniere news des 8 sources, en ligne
```

Sans Docker : `pip install -r requirements-dev.txt && PYTHONPATH=src python -m pytest`.

## Organisation

```
config/sources.csv   catalogue des sources (name, type, region, feed_url)
src/collector/       fetch, normalize, storage, collect, check_feeds, alert
tests/               tests et fixtures (flux RSS/Atom d'exemple)
infra/cronicle/      entrypoint et creation de l'evenement planifie
docs/                cadrage et CI/CD
bin/                 dev, test
```

Commandes utiles : `docker compose exec cronicle python -m collector.check_feeds` (verifie les 8 flux), `docker compose exec cronicle python -m collector.collect` (collecte manuelle).

## Alertes

Renseigner `ALERT_WEBHOOK_URL` dans `.env` (webhook entrant Discord, Slack, Mattermost ou Teams) : un message est envoye si une source echoue ou si la collecte plante. Pas de SMTP.

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md). CI/CD : [docs/ci-cd.md](docs/ci-cd.md).
