#!/usr/bin/env python3
"""Exporta el componente de index.html como PNG por cada carta de generate.txt.

Uso:
    python3 export_cards.py

generate.txt tiene una línea por carta con el formato <cantidad>x<codigo>
(ej: 4xOP15-014). Por cada código consulta la API definida en API_CARD (.env),
descarga la imagen y exporta el componente a exports/<codigo>.png.

Los códigos que fallan se registran en errors.txt. Requiere Google Chrome.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "exports"
CACHE_DIR = BASE_DIR / ".cache"
GENERATE_FILE = BASE_DIR / "generate.txt"
ERRORS_FILE = BASE_DIR / "errors.txt"
INDEX_HTML = BASE_DIR / "index.html"
ENV_FILE = BASE_DIR / ".env"

WINDOW_W, WINDOW_H = 1948, 367
PAD_TOP = 50   # para que el badge xN (top:-31px) entre tras el zoom 1.05
PAD_LEFT = 61  # margen izquierdo tras el zoom 1.05 desde el centro

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

USER_AGENT = "cartas-ui/1.0"
LINE_RE = re.compile(r"^\s*(\d+)\s*x\s*([A-Za-z0-9-]+)\s*$")


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if os.path.isfile(path):
            return path
    shutil_which = shutil.which("google-chrome") or shutil.which("chromium")
    if shutil_which:
        return shutil_which
    sys.exit("No se encontró Google Chrome. Instálalo o ajusta CHROME_CANDIDATES.")


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


def read_generate() -> list[tuple[str, str]]:
    if not GENERATE_FILE.is_file():
        sys.exit(f"No se encontró {GENERATE_FILE}.")
    entries: list[tuple[str, str]] = []
    for num, line in enumerate(
        GENERATE_FILE.read_text(encoding="utf-8").splitlines(), 1
    ):
        match = LINE_RE.match(line)
        if not match:
            print(f"  (ignorada línea {num}: {line!r})")
            continue
        entries.append((match.group(2).upper(), match.group(1)))
    if not entries:
        sys.exit(f"{GENERATE_FILE} no tiene cartas válidas.")
    return entries


def fetch_card(api_base: str, code: str) -> dict:
    url = f"{api_base.rstrip('/')}/{code}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("la API no devolvió datos")
    base = next(
        (
            c for c in data
            if c.get("card_image_id") == c.get("card_set_id")
        ),
        data[0],
    )
    return base


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
      document.querySelector(".character img").src = {image_abs!r};
    </script>
  </body>
"""
    return html.replace("</body>", override)


def screenshot(chrome: str, html_path: Path, out_path: Path) -> None:
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--default-background-color=00000000",
        f"--window-size={WINDOW_W},{WINDOW_H}",
        "--virtual-time-budget=2000",
        f"--screenshot={out_path}",
        html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main() -> None:
    chrome = find_chrome()
    env = load_env()
    api_base = env.get("API_CARD")
    if not api_base:
        sys.exit(f"Falta la variable API_CARD en {ENV_FILE}.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    entries = read_generate()
    errors: list[str] = []

    print(f"Chrome: {os.path.basename(chrome)}")
    print(f"API: {api_base}")
    print(f"Exportando {len(entries)} carta(s) a {OUTPUT_DIR}\n")

    for idx, (code, qty) in enumerate(entries, 1):
        qty_label = f"x{qty}" if not qty.startswith("x") else qty
        print(f"[{idx}/{len(entries)}] {code} ({qty_label})")
        try:
            card = fetch_card(api_base, code)
            name = card.get("card_name") or code
            image_url = card.get("card_image")
            if not image_url:
                raise ValueError("la API no devolvió card_image")

            ext = Path(urlparse(image_url).path).suffix or ".img"
            image_path = download_image(image_url, CACHE_DIR / f"{code}{ext}")

            out_path = OUTPUT_DIR / f"{code}.png"
            with tempfile.NamedTemporaryFile(
                "w", suffix=".html", dir=BASE_DIR, delete=False, encoding="utf-8"
            ) as f:
                f.write(build_export_html(name, code, qty_label, image_path.resolve().as_posix()))
                tmp_html = Path(f.name)

            try:
                screenshot(chrome, tmp_html, out_path)
                print(f"  → {out_path.name} ({out_path.stat().st_size} bytes)")
            finally:
                tmp_html.unlink(missing_ok=True)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{code}: {exc}")
            print(f"  ✗ error: {exc}")

    if errors:
        ERRORS_FILE.write_text("\n".join(errors) + "\n", encoding="utf-8")
        print(f"\n{len(errors)} error(es). Revisa {ERRORS_FILE.name}.")
    else:
        ERRORS_FILE.unlink(missing_ok=True)
        print("\nSin errores.")

    ok_count = len(entries) - len(errors)
    print(f"Listo: {ok_count}/{len(entries)} cartas exportadas.")


if __name__ == "__main__":
    main()
