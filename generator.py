"""Núcleo de generación de cartas: API → descarga de imagen → render → PNG.

Compartido por la CLI (export_cards.py) y la API web (server.py).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".cache"
INDEX_HTML = BASE_DIR / "index.html"
ENV_FILE = BASE_DIR / ".env"

WINDOW_W, WINDOW_H = 1948, 367
PAD_TOP = 50   # para que el badge xN (top:-31px) entre tras el zoom 1.05
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


def clean_name(name: str) -> str:
    """Elimina los grupos de paréntesis del final del nombre (códigos, arte, etc.)."""
    return NAME_PAREN_RE.sub("", name).strip()


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


def parse_text(text: str) -> list[tuple[str, str]]:
    """Devuelve [(codigo, cantidad), ...] válidos del texto con formato NxCODIGO."""
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if match:
            entries.append((match.group(2).upper(), match.group(1)))
    return entries


def fetch_card(api_base: str, code: str) -> dict:
    url = f"{api_base.rstrip('/')}/{code}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("la API no devolvió datos")
    return next(
        (c for c in data if c.get("card_image_id") == c.get("card_set_id")),
        data[0],
    )


def download_image(url: str, dest: Path) -> Path:
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return dest


def build_export_html(name: str, code: str, quantity: str, image_abs: str) -> str:
    html = INDEX_HTML.read_text(encoding="utf-8")
    bg_image = f'url("{image_abs}")'
    override = f"""
    <style>
      html {{
        background: transparent;
      }}
      body {{
        display: block;
        margin: 0;
        padding-top: {PAD_TOP}px;
        padding-left: {PAD_LEFT}px;
        background: transparent;
      }}
    </style>
    <script>
      document.querySelector(".name").textContent = {name!r};
      document.querySelector(".code").textContent = {code!r};
      document.querySelector(".quantity").textContent = {quantity!r};
      document.querySelector(".character").style.backgroundImage = {bg_image!r};
    </script>
  </body>
"""
    return html.replace("</body>", override)


# Serializa las capturas: Chrome no puede abrir varios procesos con el mismo
# perfil a la vez (cuelga o lanza error de bloqueo de perfil).
SCREENSHOT_LOCK = threading.Lock()


def screenshot(chrome: str, html_path: Path, out_path: Path) -> None:
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--default-background-color=00000000",
        f"--window-size={WINDOW_W},{WINDOW_H}",
        "--virtual-time-budget=2000",
        f"--screenshot={out_path}",
        html_path.as_uri(),
    ]
    with SCREENSHOT_LOCK:
        subprocess.run(cmd, check=True, capture_output=True)


def generate_png(
    code: str,
    qty_label: str,
    api_base: str,
    chrome: str,
    image_dir: Path,
    out_path: Path,
) -> str:
    """Genera el PNG de una carta y lo escribe en out_path. Devuelve el nombre."""
    card = fetch_card(api_base, code)
    name = clean_name(card.get("card_name") or code)
    image_url = card.get("card_image")
    if not image_url:
        raise ValueError("la API no devolvió card_image")

    ext = Path(urlparse(image_url).path).suffix or ".img"
    image_path = download_image(image_url, image_dir / f"{code}{ext}")
    html_text = build_export_html(name, code, qty_label, image_path.resolve().as_posix())

    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", dir=image_dir, delete=False, encoding="utf-8"
    ) as f:
        f.write(html_text)
        tmp_html = Path(f.name)
    try:
        screenshot(chrome, tmp_html, out_path)
    finally:
        tmp_html.unlink(missing_ok=True)
    return name


def generate_cards(
    entries: list[tuple[str, str]],
    api_base: str,
    chrome: str,
    image_dir: Path,
    out_dir: Path,
) -> tuple[list[dict], list[dict]]:
    """Genera varias cartas secuencialmente. Devuelve (ok, errors) con rutas PNG."""
    ok: list[dict] = []
    errors: list[dict] = []
    for code, qty in entries:
        qty_label = f"x{qty}" if not qty.startswith("x") else qty
        out_path = out_dir / f"{code}.png"
        try:
            name = generate_png(code, qty_label, api_base, chrome, image_dir, out_path)
            ok.append({"code": code, "name": name, "qty": qty, "path": out_path})
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            errors.append({"code": code, "reason": str(exc)})
    return ok, errors


def clear_cache() -> None:
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir(exist_ok=True)


if __name__ == "__main__":
    sys.exit("Este módulo no es ejecutable. Usa export_cards.py o server.py.")
