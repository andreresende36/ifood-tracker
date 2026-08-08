"""
Rotina diária de coleta (roda dentro do container, sob supervisor).

Dorme até a próxima meia-noite local e roda o scraper em --auto para cada
perfil existente, um de cada vez (o Chrome usa uma porta CDP fixa).

Se a sessão do iFood tiver expirado, o scraper fica preso na tela de login e
encerra por timeout — o log diz isso e o login precisa ser refeito via VNC.
"""

import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, "/app")
from database import list_profiles  # noqa: E402

SCRAPE_TIMEOUT = 30 * 60  # segundos por perfil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] cron: %(message)s",
)
log = logging.getLogger(__name__)


def seconds_until_midnight() -> float:
    now = datetime.now()
    nxt = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (nxt - now).total_seconds()


def scrape(profile: str) -> None:
    log_path = Path(f"data/scrape_{profile}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "scraper.py", "--profile-name", profile, "--auto"]
    log.info(f"coletando perfil '{profile}'…")
    try:
        with open(log_path, "w", encoding="utf-8") as logf:
            proc = subprocess.run(
                cmd, stdout=logf, stderr=subprocess.STDOUT,
                cwd="/app", timeout=SCRAPE_TIMEOUT,
            )
        ok = proc.returncode == 0 and "FIM_SCRAPER_OK" in log_path.read_text(
            encoding="utf-8", errors="ignore"
        )
        log.info(f"perfil '{profile}': {'ok' if ok else 'terminou com avisos'}")
    except subprocess.TimeoutExpired:
        log.warning(
            f"perfil '{profile}': timeout de {SCRAPE_TIMEOUT}s. "
            "A sessão do iFood provavelmente expirou — refaça o login pelo VNC."
        )


def main() -> None:
    while True:
        wait = seconds_until_midnight()
        log.info(f"próxima coleta em {wait / 3600:.1f}h")
        time.sleep(wait)

        profiles = list_profiles()
        if not profiles:
            log.warning("nenhum perfil encontrado, pulando.")
            continue
        for profile in profiles:
            scrape(profile)
        time.sleep(60)  # evita rodar duas vezes se a coleta for instantânea


if __name__ == "__main__":
    main()
