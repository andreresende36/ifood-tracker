# Google Chrome só existe para amd64 no Linux — Railway roda amd64 nativamente.
FROM --platform=linux/amd64 python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    CHROME_EXTRA_ARGS="--no-sandbox --disable-dev-shm-usage --disable-gpu"

# Chrome real (necessário para passar no Cloudflare do iFood) + Xvfb/VNC/noVNC
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg apache2-utils gettext-base \
        xvfb x11vnc novnc websockify supervisor nginx \
        fonts-liberation libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
        libgtk-3-0 libgbm1 libdrm2 xdg-utils \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 app \
    && mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY deploy/nginx.conf.template /etc/nginx/nginx.conf.template
COPY deploy/supervisord.conf /etc/supervisor/supervisord.conf
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R app:app /app

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
