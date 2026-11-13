# Etape 1 : Cronicle (planificateur) construit avec Node
FROM node:22-slim AS cronicle-build
ARG CRONICLE_VERSION=0.9.145
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/cronicle
RUN curl -fsSL https://github.com/jhuckaby/Cronicle/archive/refs/tags/v${CRONICLE_VERSION}.tar.gz \
    | tar xz --strip-components 1 \
    && npm install \
    && node bin/build.js dist \
    && cp sample_conf/config.json conf/config.json

# Etape 2 : Python (collecteur) + Node (pour Cronicle)
FROM python:3.12-slim

ENV TZ=Europe/Paris \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    HOSTNAME=cronicle

COPY --from=cronicle-build /usr/local/bin/node /usr/local/bin/node
COPY --from=cronicle-build /opt/cronicle /opt/cronicle

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config ./config
COPY src ./src
COPY tests ./tests
COPY pytest.ini entrypoint.sh ./
COPY docker/bootstrap_event.py ./docker/bootstrap_event.py
RUN chmod +x entrypoint.sh \
    && useradd --create-home --uid 1000 app \
    && mkdir -p /app/data /opt/cronicle/data /opt/cronicle/logs /opt/cronicle/queue \
    && chown -R app:app /app /opt/cronicle

USER app
EXPOSE 3012
ENTRYPOINT ["./entrypoint.sh"]
