"""Construcción del HTML de exportación y captura con Chrome headless."""

import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from config import (
    COMPONENTS_DIR,
    COMPONENT_RE,
    PAD_LEFT,
    PAD_TOP,
    RENDER_WORKERS,
    WINDOW_H,
    WINDOW_W,
)


def list_components() -> list[str]:
    """Devuelve los nombres de los componentes disponibles (components/*.html)."""
    return sorted(p.stem for p in COMPONENTS_DIR.glob("*.html"))


def resolve_component(name: str) -> Path:
    """Valida el nombre de un componente y devuelve su ruta (evita path traversal)."""
    if not COMPONENT_RE.match(name or ""):
        raise ValueError(f"nombre de componente no válido: {name!r}")
    path = COMPONENTS_DIR / f"{name}.html"
    if not path.is_file():
        raise ValueError(f"no existe el componente {name!r}")
    return path


@dataclass
class CardRenderRequest:
    component: str
    name: str
    code: str
    quantity: str
    image_path: Path
    chrome: str
    out_path: Path
    colors: list[str] | None = None
    bg_position: str | None = None
    bg_size: str | None = None


def build_export_html(request: CardRenderRequest, template: Path) -> str:
    image_abs = request.image_path.resolve().as_posix()
    bg_image = f'url("{image_abs}")'
    color_vars = ""
    if request.colors:
        c1 = request.colors[0]
        c2 = request.colors[1] if len(request.colors) > 1 else request.colors[0]
        color_vars = f"""
      :root {{
        --optcg-c1: {c1};
        --optcg-c2: {c2};
      }}"""
    bg_script = ""
    if request.bg_position:
        bg_script += (
            f'\n      setStyle(".character", "backgroundPosition", {request.bg_position!r});'
        )
    if request.bg_size:
        bg_script += f'\n      setStyle(".character", "backgroundSize", {request.bg_size!r});'
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
      function setStyle(sel, prop, val) {{
        const el = document.querySelector(sel);
        if (el) el.style[prop] = val;
      }}
      setText(".name", {request.name!r});
      setText(".code", {request.code!r});
      setText(".quantity", {request.quantity!r});
      setBg(".character", {bg_image!r});{bg_script}
    </script>
  </body>
"""
    return template.read_text(encoding="utf-8").replace("</body>", override)


# Limita las capturas concurrentes: cada una usa su propio perfil temporal
# (--user-data-dir), por lo que varios Chromium pueden correr en paralelo.
SCREENSHOT_SEM = threading.Semaphore(RENDER_WORKERS)


def screenshot(chrome: str, html_path: Path, out_path: Path) -> None:
    profile = tempfile.mkdtemp(prefix="optcg-chrome-")
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--no-first-run",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--default-background-color=00000000",
        f"--window-size={WINDOW_W},{WINDOW_H}",
        "--virtual-time-budget=1000",
        f"--user-data-dir={profile}",
        f"--screenshot={out_path}",
        html_path.as_uri(),
    ]
    with SCREENSHOT_SEM:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        finally:
            shutil.rmtree(profile, ignore_errors=True)


def render_png(request: CardRenderRequest) -> str:
    """Renderiza un componente con datos concretos y escribe el PNG. Devuelve el nombre."""
    template = resolve_component(request.component)
    html_text = build_export_html(request, template)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", dir=request.image_path.parent, delete=False, encoding="utf-8"
    ) as f:
        f.write(html_text)
        tmp_html = Path(f.name)
    try:
        screenshot(request.chrome, tmp_html, request.out_path)
    finally:
        tmp_html.unlink(missing_ok=True)
    return request.name