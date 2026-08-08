"""
Abre (ou fecha) um Chrome avulso no display virtual, só para login manual.

O scraper sobe o Chrome e o mata ao terminar, então fora de uma coleta o VNC
mostra uma tela vazia. Este script deixa o navegador aberto pelo tempo que a
pessoa precisar para logar no iFood; a sessão fica salva no perfil e a coleta
seguinte já entra logada.
"""

import os
import signal
import subprocess
from pathlib import Path

from scraper import IFOOD_ORDERS_URL, chrome_profile_for

PID_DIR = Path("data")


def _pid_file(profile: str) -> Path:
    return PID_DIR / f"chrome_login_{profile}.pid"


def _chrome_binary() -> str:
    from shutil import which
    for candidate in ("google-chrome", "google-chrome-stable", "chromium"):
        found = which(candidate)
        if found:
            return found
    raise RuntimeError("Chrome não encontrado no container.")


def is_running(profile: str) -> bool:
    pid_file = _pid_file(profile)
    if not pid_file.exists():
        return False
    try:
        os.kill(int(pid_file.read_text()), 0)
        return True
    except (OSError, ValueError):
        pid_file.unlink(missing_ok=True)
        return False


def start(profile: str) -> None:
    """Sobe o Chrome no display virtual com o perfil da pessoa."""
    if is_running(profile):
        return

    profile_path = chrome_profile_for(profile)
    profile_path.mkdir(parents=True, exist_ok=True)
    PID_DIR.mkdir(parents=True, exist_ok=True)

    args = [
        _chrome_binary(),
        *os.environ.get("CHROME_EXTRA_ARGS", "").split(),
        f"--user-data-dir={profile_path}",
        "--no-first-run",
        "--no-default-browser-check",
        "--lang=pt-BR",
        "--window-position=0,0",
        "--window-size=1440,900",
        IFOOD_ORDERS_URL,
    ]
    proc = subprocess.Popen(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _pid_file(profile).write_text(str(proc.pid))


def stop(profile: str) -> None:
    """Fecha o Chrome de login, liberando o perfil para o scraper."""
    pid_file = _pid_file(profile)
    if not pid_file.exists():
        return
    try:
        os.killpg(os.getpgid(int(pid_file.read_text())), signal.SIGTERM)
    except (OSError, ValueError):
        pass
    pid_file.unlink(missing_ok=True)
