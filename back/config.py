"""Configuración y constantes compartidas del backend."""

import os
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".cache"
ART_DIR = CACHE_DIR / "art"
# Imágenes subidas por el usuario al editar; son temporales y se borran tras renderizar.
UPLOAD_DIR = CACHE_DIR / "upload"
COMPONENTS_DIR = BASE_DIR / "components"
ENV_FILE = BASE_DIR / ".env"

# Geometría de la exportación: ventana de captura y márgenes. Deben cuadrar con
# el zoom scale(1.05) del .card y el PAD para que la carta salga centrada.
WINDOW_W, WINDOW_H = 1948, 367
PAD_TOP = 50  # para que el badge xN (top:-31px) entre tras el zoom 1.05
PAD_LEFT = 61  # margen izquierdo tras el zoom 1.05 desde el centro

CHROME_CANDIDATES = [
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

USER_AGENT = "cartas-ui/1.0"
LINE_RE = re.compile(r"^\s*(\d+)\s*x\s*([A-Za-z0-9-]+)\s*$")
NAME_PAREN_RE = re.compile(r"(?:\s*\([^()]*\))+$")
COMPONENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Intervalo mínimo entre peticiones a la API (segundos), para no superar su
# rate limit (429). Ajustable con OPTCG_MIN_INTERVAL. Bajo para agilizar
# generaciones grandes; los 429 se reintentan automáticamente con backoff.
MIN_REQUEST_INTERVAL = 0.3

# Capturas de Chrome en paralelo (cada una con perfil temporal propio).
RENDER_WORKERS = 4

# Colores de las cartas de One Piece TCG → hex (ajustables).
OPTCG_COLORS: dict[str, str] = {
    "red": "#C8102E",
    "green": "#00A651",
    "blue": "#0057B8",
    "purple": "#7B2D8E",
    "black": "#2E2E2E",
    "yellow": "#FFB800",
}


def load_env() -> dict:
    env: dict[str, str] = {}
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def get_api_base() -> str | None:
    value = os.environ.get("API_CARD")
    if value:
        return value.strip()
    return load_env().get("API_CARD")


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if os.path.isfile(path):
            return path
    shutil_which = shutil.which("google-chrome") or shutil.which("chromium")
    if shutil_which:
        return shutil_which
    raise RuntimeError(
        "No se encontró Google Chrome/Chromium. Instálalo o ajusta CHROME_CANDIDATES."
    )