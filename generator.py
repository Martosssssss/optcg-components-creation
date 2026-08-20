"""Núcleo de generación de cartas: API → descarga de imagen → render → PNG.

Compartido por la CLI (export_cards.py) y la API web (server.py).
"""

import email.utils
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".cache"
COMPONENTS_DIR = BASE_DIR / "components"
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
COMPONENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Intervalo mínimo entre peticiones a la API (segundos), para no superar su
# rate limit (429). Ajustable con OPTCG_MIN_INTERVAL.
MIN_REQUEST_INTERVAL = 1.0
RATE_LOCK = threading.Lock()
_last_request = -MIN_REQUEST_INTERVAL

# Colores de las cartas de One Piece TCG → hex (ajustables).
OPTCG_COLORS: dict[str, str] = {
    "red": "#C8102E",
    "green": "#00A651",
    "blue": "#0057B8",
    "purple": "#7B2D8E",
    "black": "#2E2E2E",
    "yellow": "#FFB800",
}


def card_colors_to_hex(card_color: str | None) -> list[str]:
    """Devuelve los hex de los colores de la carta (1-2) a partir de card_color.

    Si no hay colores reconocidos devuelve una lista vacía (el componente usa
    su degradado por defecto).
    """
    hexes: list[str] = []
    for part in re.split(r"\s+", (card_color or "").strip()):
        hex_color = OPTCG_COLORS.get(part.lower())
        if hex_color:
            hexes.append(hex_color)
    return list(dict.fromkeys(hexes))


def clean_name(name: str) -> str:
    """Elimina los grupos de paréntesis del final del nombre (códigos, arte, etc.)."""
    return NAME_PAREN_RE.sub("", name).strip()


def list_components() -> list[str]:
    """Devuelve los nombres de los componentes disponibles (componentes/*.html)."""
    return sorted(p.stem for p in COMPONENTS_DIR.glob("*.html"))


def resolve_component(name: str) -> Path:
    """Valida el nombre de un componente y devuelve su ruta (evita path traversal)."""
    if not COMPONENT_RE.match(name or ""):
        raise ValueError(f"nombre de componente no válido: {name!r}")
    path = COMPONENTS_DIR / f"{name}.html"
    if not path.is_file():
        raise ValueError(f"no existe el componente {name!r}")
    return path


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


def _rate_limit() -> None:
    """Espera lo necesario para respetar el intervalo mínimo entre peticiones."""
    global _last_request
    interval = float(os.environ.get("OPTCG_MIN_INTERVAL", MIN_REQUEST_INTERVAL))
    with RATE_LOCK:
        now = time.monotonic()
        wait = interval - (now - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()


def _retry_after(exc: urllib.error.HTTPError) -> float | None:
    """Segundos indicados por Retry-After (número o fecha HTTP), o None."""
    value = exc.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(value)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def _throttled_open(url: str) -> object:
    """Abre url respetando el rate limit y reintentando ante 429.

    Espera lo que indique Retry-After (con tope OPTCG_MAX_RETRY_WAIT). Si el
    bloqueo es más largo que el tope, avisa con el tiempo restante.
    """
    attempts = 4
    base_backoff = 5.0
    max_wait = float(os.environ.get("OPTCG_MAX_RETRY_WAIT", "600"))
    for attempt in range(attempts):
        _rate_limit()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            return urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt >= attempts - 1:
                raise
            wait = _retry_after(exc) or base_backoff
            if wait > max_wait:
                raise ValueError(
                    "límite de la API (429); espera ~"
                    f"{int(wait / 60)} min y vuelve a intentarlo"
                ) from exc
            time.sleep(wait)
    raise AssertionError("bucle de reintentos sin resolver")


def _atomic_write(path: Path, content: str) -> None:
    """Escribe content en path de forma atómica (evita lecturas parciales)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def fetch_card(api_base: str, code: str) -> dict:
    """Devuelve los datos de una carta, cacheando la respuesta en .cache/meta/."""
    meta_dir = CACHE_DIR / "meta"
    cached = meta_dir / f"{code}.json"
    if cached.is_file():
        return json.loads(cached.read_text(encoding="utf-8"))
    url = f"{api_base.rstrip('/')}/{code}"
    with _throttled_open(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("la API no devolvió datos")
    card = next(
        (c for c in data if c.get("card_image_id") == c.get("card_set_id")),
        data[0],
    )
    meta_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(cached, json.dumps(card, ensure_ascii=False))
    return card


def download_image(url: str, dest: Path) -> Path:
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with _throttled_open(url) as resp:
        data = resp.read()
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return dest


def build_export_html(
    name: str,
    code: str,
    quantity: str,
    image_abs: str,
    template: Path,
    colors: list[str] | None = None,
) -> str:
    html = template.read_text(encoding="utf-8")
    bg_image = f'url("{image_abs}")'
    color_vars = ""
    if colors:
        c1 = colors[0]
        c2 = colors[1] if len(colors) > 1 else colors[0]
        color_vars = f"""
      :root {{
        --optcg-c1: {c1};
        --optcg-c2: {c2};
      }}"""
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
      {color_vars}
    </style>
    <script>
      function setText(sel, val) {{
        const el = document.querySelector(sel);
        if (el) el.textContent = val;
      }}
      function setBg(sel, url) {{
        const el = document.querySelector(sel);
        if (el) el.style.backgroundImage = url;
      }}
      setText(".name", {name!r});
      setText(".code", {code!r});
      setText(".quantity", {quantity!r});
      setBg(".character", {bg_image!r});
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
    component: str = "card",
) -> str:
    """Genera el PNG de una carta y lo escribe en out_path. Devuelve el nombre."""
    template = resolve_component(component)
    card = fetch_card(api_base, code)
    name = clean_name(card.get("card_name") or code)
    image_url = card.get("card_image")
    if not image_url:
        raise ValueError("la API no devolvió card_image")

    ext = Path(urlparse(image_url).path).suffix or ".img"
    image_path = download_image(image_url, image_dir / f"{code}{ext}")
    colors = card_colors_to_hex(card.get("card_color"))
    html_text = build_export_html(
        name, code, qty_label, image_path.resolve().as_posix(), template, colors
    )

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
    component: str = "card",
) -> tuple[list[dict], list[dict]]:
    """Genera varias cartas secuencialmente. Devuelve (ok, errors) con rutas PNG."""
    ok: list[dict] = []
    errors: list[dict] = []
    for code, qty in entries:
        qty_label = f"x{qty}" if not qty.startswith("x") else qty
        out_path = out_dir / f"{code}.png"
        try:
            name = generate_png(
                code, qty_label, api_base, chrome, image_dir, out_path, component
            )
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
