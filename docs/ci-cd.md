# Strategie CI/CD

1. **Declencheurs** : GitHub Actions (`.github/workflows/ci.yml`) sur chaque Pull Request et chaque push sur `main`.
2. **Job `lint + tests`** : installe `requirements-dev.txt`, lance `ruff check .` puis `pytest`. Tests hors ligne uniquement (fixtures), donc deterministes.
3. **Job `build + push image`** : demarre seulement si `lint + tests` est vert. Construit l'image Docker, cible `runtime` (sans outils de test, utilisateur non root).
4. **Publication** : uniquement sur push vers `main`, dans `ghcr.io/<proprietaire>/<depot>` avec le tag `YYYYMMDDHHMMSS-sha` (UTC + 7 premiers caracteres du commit), donc chaque image dit d'ou elle vient.
5. **Pull Request** : l'image est construite pour verifier le Dockerfile, mais pas publiee.
6. **Blocage** : la regle de protection de `main` exige les statuts `lint + tests` et `build + push image` ; une CI rouge empeche le merge (reglage GitHub, voir CONTRIBUTING.md).
7. **Garanties** : ca s'installe, le lint et les tests passent, l'image se construit et porte un tag tracable. Rien de plus.
8. **Hors perimetre** : pas de deploiement automatique (TD 7), pas de matrice de versions, pas de cache de build exotique.
9. **Tests en ligne** (`RUN_LIVE=1`) : volontairement hors CI, car ils dependent des flux des editeurs.
10. **Environnement de dev** : `bin/dev` (compose) decrit l'environnement ; `bin/test` rejoue lint + tests dans le meme conteneur que le dev.
