#!/usr/bin/env bash
# Prepara o volume persistente, a senha de acesso e sobe o supervisor.
set -euo pipefail

export PORT="${PORT:-8080}"
DATA_DIR=/app/data

mkdir -p "$DATA_DIR" "$DATA_DIR/chrome_profile" "$DATA_DIR/profiles"
chown -R app:app "$DATA_DIR"

# chrome_profile/ e profiles/ vivem no volume — o código os acessa por caminho relativo
for d in chrome_profile profiles; do
    if [ ! -L "/app/$d" ]; then
        rm -rf "/app/$d"
        ln -s "$DATA_DIR/$d" "/app/$d"
    fi
done
chown -h app:app /app/chrome_profile /app/profiles

# Gate de senha (nginx basic auth) — protege dashboard e VNC
if [ -z "${APP_USER:-}" ] || [ -z "${APP_PASSWORD:-}" ]; then
    echo "FATAL: defina APP_USER e APP_PASSWORD nas variáveis do Railway." >&2
    exit 1
fi
htpasswd -bc /etc/nginx/.htpasswd "$APP_USER" "$APP_PASSWORD" >/dev/null 2>&1

envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec supervisord -c /etc/supervisor/supervisord.conf
