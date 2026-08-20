"""Cliente HTTP de la API de One Piece TCG.

Throttling, reintentos ante 429 y caché local de respuestas e imágenes.
"""

import email.utils
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from config import (
    ART_DIR,
    CACHE_DIR,
    MIN_REQUEST_INTERVAL,
    OPTCG_COLORS,
    USER_AGENT,
)

RATE_LOCK = threading.Lock()
_last_request = -MIN_REQUEST_INTERVAL


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
    return write_image_bytes(data, dest)


def write_image_bytes(data: bytes, dest: Path) -> Path:
    """Escribe data en dest de forma atómica y devuelve dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return dest