#!/usr/bin/env bash
# Prepara o volume persistente, valida a config de acesso e sobe o supervisor.
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

# O Chrome tranca o perfil com SingletonLock/Cookie/Socket, gravados no volume.
# Se o container morreu com ele aberto (todo redeploy faz isso), o lock aponta
# para um host que não existe mais e o Chrome seguinte se recusa a subir. No
# boot não há Chrome rodando, então qualquer lock aqui é resto.
find "$DATA_DIR" -maxdepth 3 -name "Singleton*" -print -delete 2>/dev/null || true

# O acesso é controlado pelo dashboard (lista de emails em APP_EMAILS), não
# mais por basic auth no nginx.
if [ -z "${APP_EMAILS:-}" ]; then
    echo "FATAL: defina APP_EMAILS (emails separados por vírgula) no Railway." >&2
    exit 1
fi

# Token do socket do VNC — o dashboard lê a mesma variável para montar o link
if [ -z "${VNC_TOKEN:-}" ]; then
    VNC_TOKEN=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')
    echo "VNC_TOKEN não definido; gerando um efêmero para este deploy."
fi
export VNC_TOKEN

envsubst '${PORT} ${VNC_TOKEN}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec supervisord -c /etc/supervisor/supervisord.conf
