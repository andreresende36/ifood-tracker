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

# O Chrome tranca o perfil com SingletonLock/Cookie/Socket, gravados no volume.
# Se o container morreu com ele aberto (todo redeploy faz isso), o lock aponta
# para um host que não existe mais e o Chrome seguinte se recusa a subir. No
# boot não há Chrome rodando, então qualquer lock aqui é resto.
find "$DATA_DIR" -maxdepth 3 -name "Singleton*" -print -delete 2>/dev/null || true

# Gate de senha (nginx basic auth) — protege dashboard e VNC
if [ -z "${APP_USER:-}" ] || [ -z "${APP_PASSWORD:-}" ]; then
    echo "FATAL: defina APP_USER e APP_PASSWORD nas variáveis do Railway." >&2
    exit 1
fi
htpasswd -bc /etc/nginx/.htpasswd "$APP_USER" "$APP_PASSWORD" >/dev/null 2>&1

# Usuários extras, formato "nome:senha,nome2:senha2". Todos veem os mesmos
# dados — o gate é de acesso ao app, não de isolamento por perfil.
if [ -n "${APP_EXTRA_USERS:-}" ]; then
    echo "$APP_EXTRA_USERS" | tr ',' '\n' | while IFS=: read -r u p; do
        [ -n "$u" ] && [ -n "$p" ] || continue
        htpasswd -b /etc/nginx/.htpasswd "$u" "$p" >/dev/null 2>&1
        echo "usuário extra registrado: $u"
    done
fi

# Token do socket do VNC — o dashboard lê a mesma variável para montar o link
if [ -z "${VNC_TOKEN:-}" ]; then
    VNC_TOKEN=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')
    echo "VNC_TOKEN não definido; gerando um efêmero para este deploy."
fi
export VNC_TOKEN

envsubst '${PORT} ${VNC_TOKEN}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec supervisord -c /etc/supervisor/supervisord.conf
