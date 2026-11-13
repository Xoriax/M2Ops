#!/bin/sh
# Demarre Cronicle (planificateur) et cree l'evenement quotidien de collecte au premier lancement.
set -e
cd /opt/cronicle

SECRET_FILE=data/.secret_key
[ -f "$SECRET_FILE" ] || python -c "import secrets;print(secrets.token_hex(24))" > "$SECRET_FILE"
export CRONICLE_secret_key="$(cat "$SECRET_FILE")"
export CRONICLE_base_app_url="${CRONICLE_base_app_url:-http://localhost:3012}"
export CRONICLE_foreground=true
export CRONICLE_echo=true
export CRONICLE_job_env__TZ="Europe/Paris"

if [ ! -f data/.setup_done ]; then
  echo "[entrypoint] premier demarrage : initialisation de Cronicle"
  node bin/storage-cli.js setup
  touch data/.setup_done
fi

# a chaque demarrage : le mot de passe admin suit .env (remplace admin/admin, et leve un verrouillage)
node bin/storage-cli.js admin admin "${CRONICLE_ADMIN_PASSWORD:?definir CRONICLE_ADMIN_PASSWORD dans .env}"

# cree l'evenement de collecte une fois le serveur pret (en arriere-plan)
python /app/docker/bootstrap_event.py &

exec node lib/main.js
