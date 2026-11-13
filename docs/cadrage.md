# Cadrage technique : La Gazette

## Architecture de la tache 1

Un seul conteneur Docker (`cronicle`) embarque Python (collecteur) et Cronicle (planificateur, https://cronicle.net). Au premier demarrage, `entrypoint.sh` initialise Cronicle et `docker/bootstrap_event.py` cree l'evenement **Gazette : collecte quotidienne** : tous les jours a 7h Europe/Paris, commande `python -m collector.collect`, un seul run a la fois (`max_children: 1`), 0 relance cote Cronicle (les relances sont dans `fetch.py`).

Le script lit `config/sources.yaml`, telecharge les flux RSS, ecrit bronze (JSON brut utile), silver (CSV deduplique sur `url_hash`) et `data/state/last_run.json`.

Interface web : http://localhost:3012 (publiee sur 127.0.0.1 uniquement), compte `admin`, mot de passe `CRONICLE_ADMIN_PASSWORD` du fichier `.env`. Elle donne l'historique et les logs de chaque run.

## Rattrapage

L'evenement a l'option Cronicle **Run All (Catch-Up)** : si la machine etait eteinte a 7h, Cronicle relance les runs rates au redemarrage. Comme la collecte est idempotente (deduplication sur `url_hash`), plusieurs runs de rattrapage ne creent pas de doublons.

## Risques

- **Pas de socket Docker** : contrairement a une solution de type Ofelia, Cronicle tourne dans le meme conteneur que le collecteur et n'a pas besoin d'acceder a `/var/run/docker.sock`. C'est le principal avantage de ce choix. Rien a faire valider cote admin EFREI sur ce point (partie 6).
- **Interface web Cronicle** : protegee par mot de passe, mais a ne pas exposer au-dela de `127.0.0.1` sans HTTPS. Le mot de passe par defaut `admin/admin` est remplace au premier demarrage ; `.env` n'est pas versionne.
- **Version epinglee** : Cronicle 0.9.145 (argument de build `CRONICLE_VERSION`). Projet a un seul mainteneur principal : surveiller les mises a jour de securite.
- **Donnees Cronicle** : planning et historique sont dans le volume `cronicle_data`. Le supprimer (`docker compose down -v`) recree l'evenement au prochain demarrage, mais perd l'historique.
- **Flux RSS** : les URLs peuvent changer ou devenir perimees ; `check_feeds` sert a le detecter. Respect des conditions des editeurs : usage non commercial, User-Agent clair, pause de 1 s entre sources.
