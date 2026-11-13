# Contribuer

## Branches

- `main` est toujours deployable : on n'y pousse pas directement.
- Une branche par sujet : `feat/<sujet>`, `fix/<sujet>`, `docs/<sujet>`.
- Une Pull Request par branche, au moins une relecture (meme rapide) avant de merger.
- Merge en "squash" par l'auteur de la PR, une fois la CI verte et la relecture faite. Supprimer la branche apres.

## Commits

Format `type: description courte a l'imperatif ou au passe`, en minuscules : `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `ci:`.
Exemple : `feat: added webhook alert on failed run`.

## Avant d'ouvrir une PR

```
bin/test
```

Lint et tests doivent passer. Un test casse rend la CI rouge, et une CI rouge ne se merge pas.

## Regles du projet

- Uniquement des flux RSS/Atom officiels, pas de scraping HTML.
- Ne conserver que titre, extrait, lien, date (plus source et date de collecte). Pas de texte integral, pas d'auteur, pas de donnees personnelles.
- Aucun secret dans le depot : tout passe par `.env` (ignore par git), documente dans `.env.example`.
- Tout ce qui tourne est decrit dans le depot (Dockerfile, compose, `infra/`), rien d'installe a la main.
- Pas d'em dash dans les textes, docs et commentaires.
- Une source se configure dans `config/sources.csv`, jamais en dur dans le code.

## Reglages GitHub a activer (admin du depot)

Settings > Branches > regle sur `main` : exiger une Pull Request, exiger les statuts "lint + tests" et "build + push image", interdire le push direct. C'est ce reglage qui fait qu'une CI rouge bloque le merge.
