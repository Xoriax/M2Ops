# Cronicle : ce qui est en place, ce qui manque

## Connexion

http://localhost:3012, utilisateur `admin`, mot de passe = `CRONICLE_ADMIN_PASSWORD` du fichier `.env`.
Le mot de passe est resynchronise avec `.env` a chaque demarrage du conteneur. Si le compte est verrouille (trop d'echecs) : `docker compose restart cronicle`.

## Ce qui est en place

| Element | Valeur |
|---|---|
| Evenement | "Gazette : collecte quotidienne" (id `gazettecollect`) |
| Planning | tous les jours a 7h00, fuseau Europe/Paris |
| Commande | `cd /app && python -m collector.collect` (plugin Shell) |
| Concurrence | 1 run a la fois (`max_children: 1`) |
| Rattrapage | "Run All (Catch-Up)" active : un run rate (machine eteinte) est relance au redemarrage |
| Relances | pas cote Cronicle, elles sont dans `fetch.py` (3 essais par flux) |
| Persistance | volume Docker `cronicle_data` (planning, historique, logs de jobs) ; donnees de la collecte dans `./data` |
| Exposition | `127.0.0.1:3012` uniquement |

Dans l'interface : onglet Schedule (evenement, bouton "Run Now"), Completed (historique et logs de chaque run), Upcoming (prochains declenchements).

## Ce qui manque (volontairement non fait pour la tache 1)

- **Alerte en cas d'echec** : aucune notification n'est configuree (pas d'e-mail ni de webhook). A faire : renseigner `smtp_hostname`/`email_from` ou un Web Hook sur l'evenement ("Notify on failure"). Le code de sortie du script (1 si toutes les sources echouent) est deja ce que Cronicle utilise pour marquer un run en echec.
- **Supervision** : `data/state/last_run.json` n'est pas encore lu par Prometheus/Grafana (partie suivante).
- **HTTPS** : l'interface est en HTTP simple, limitee a localhost. A ajouter derriere un reverse proxy si elle doit etre partagee.
- **Comptes** : un seul compte `admin`. Pas de compte lecture seule pour l'equipe.
- **Sauvegarde** : le volume `cronicle_data` n'est pas sauvegarde. Le perdre fait perdre l'historique ; l'evenement est recree automatiquement.
- **Edition de l'evenement** : `docker/bootstrap_event.py` cree l'evenement une seule fois. Une modification faite dans l'interface (planning par exemple) est conservee ; pour revenir au planning du depot, supprimer l'evenement puis redemarrer le conteneur.
- **Mises a jour** : version epinglee (0.9.145), a surveiller manuellement.

## Tests

- Hors ligne : `python -m pytest` (les tests en ligne sont ignores).
- En ligne, derniere news de chacune des 8 sources via la vraie pipeline : `RUN_LIVE=1 python -m pytest tests/test_live_sources.py -s`.
