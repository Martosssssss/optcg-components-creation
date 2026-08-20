"""Orquestación de generación de cartas (CLI y API).

Re-exporta la API pública usada por export_cards.py y server.py.
"""

import shutil
import sys
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

from config import CACHE_DIR, LINE_RE, NAME_PAREN_RE, ART_DIR
from optcg_client import (
    card_colors_to_hex,
    download_image,
    fetch_card,
    write_image_bytes,
)
from render import CardRenderRequest, list_components, render_png, resolve_component

# Re-exports para la CLI y la API.
from config import find_chrome, get_api_base

__all__ = [
    "ART_DIR",
    "CACHE_DIR",
    "card_colors_to_hex",
    "clean_name",
    "clear_cache",
    "download_image",
    "fetch_card",
    "find_art",
    "find_chrome",
    "generate_cards",
    "generate_png",
    "get_api_base",
    "list_components",
    "normalize_qty",
    "parse_text",
    "render_png",
    "resolve_component",
    "write_image_bytes",
]


def clean_name(name: str) -> str:
    """Elimina los grupos de paréntesis del final del nombre (códigos, arte, etc.)."""
    return NAME_PAREN_RE.sub("", name).strip()


def parse_text(text: str) -> list[tuple[str, str]]:
    """Devuelve [(codigo, cantidad), ...] válidos del texto con formato NxCODIGO."""
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if match:
            entries.append((match.group(2).upper(), match.group(1)))
    return entries


def normalize_qty(qty: str) -> str:
    """Devuelve la cantidad en formato 'xN'."""
    return qty if qty.startswith("x") else f"x{qty}"


def find_art(code: str) -> Path:
    """Devuelve el arte cacheado de una carta (PNG/JPEG), o lanza ValueError."""
    matches = sorted(p for p in ART_DIR.glob(f"{code}.*") if p.suffix != ".tmp")
    if not matches:
        raise ValueError(f"no hay imagen cacheada para {code}; sube una imagen")
    return matches[0]


def generate_png(
    code: str,
    qty: str,
    api_base: str,
    chrome: str,
    out_path: Path,
    component: str = "card",
) -> tuple[str, list[str]]:
    """Genera el PNG de una carta y lo escribe en out_path.

    Devuelve (nombre, colores) para que la API pueda re-renderizarla después.
    """
    card = fetch_card(api_base, code)
    name = clean_name(card.get("card_name") or code)
    image_url = card.get("card_image")
    if not image_url:
        raise ValueError("la API no devolvió card_image")

    ext = Path(urlparse(image_url).path).suffix or ".img"
    image_path = download_image(image_url, ART_DIR / f"{code}{ext}")
    # El card usa su color sólido por defecto (naranja); solo el leader aplica
    # el degradado con los colores de la API.
    colors = [] if component == "card" else card_colors_to_hex(card.get("card_color"))
    render_png(
        CardRenderRequest(
            component=component,
            name=name,
            code=code,
            quantity=normalize_qty(qty),
            image_path=image_path,
            chrome=chrome,
            out_path=out_path,
            colors=colors,
        )
    )
    return name, colors


def generate_cards(
    entries: list[tuple[str, str]],
    api_base: str,
    chrome: str,
    out_dir: Path,
    component: str = "card",
) -> tuple[list[dict], list[dict]]:
    """Genera varias cartas secuencialmente. Devuelve (ok, errors) con rutas PNG."""
    ok: list[dict] = []
    errors: list[dict] = []
    for code, qty in entries:
        out_path = out_dir / f"{code}.png"
        try:
            name, _colors = generate_png(
                code, qty, api_base, chrome, out_path, component
            )
            ok.append({"code": code, "name": name, "qty": qty, "path": out_path})
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            OSError,
            ValueError,
        ) as exc:
            errors.append({"code": code, "reason": str(exc)})
    return ok, errors


def clear_cache() -> None:
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir(exist_ok=True)


if __name__ == "__main__":
    sys.exit("Este módulo no es ejecutable. Usa export_cards.py o server.py.")