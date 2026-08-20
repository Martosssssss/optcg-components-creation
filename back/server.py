#!/usr/bin/env python3
"""API web para generar cartas a partir de un texto NxCODIGO.

Endpoints:
    GET  /api/components      → lista de componentes disponibles (components/*.html)
    GET  /api/art?code=X      → arte original de una carta en base64 (.cache/art/)
    POST /api/generate        → JSON {text, component} → JSON con PNG en base64 y errores
    POST /api/generate/zip    → JSON {text, component} → ZIP binario con los PNG
    POST /api/render          → re-render de una carta editada (sin tocar la API de cartas)
    POST /api/zip             → ZIP con las PNG actuales del cliente {files:[{filename,png_b64}]}
    GET  /healthz             → 200 ok

component (opcional, por defecto "card") selecciona la plantilla de components/.
Requiere los módulos de back/ (y Chromium disponible). Puerto por defecto: 8000.
"""

import base64
import io
import json
import os
import re
import shutil
import urllib.error
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from config import CACHE_DIR, RENDER_WORKERS, UPLOAD_DIR, find_chrome, get_api_base
from generator import find_art, generate_png, parse_text
from optcg_client import write_image_bytes
from render import CardRenderRequest, list_components, render_png, resolve_component

PORT = int(os.environ.get("PORT", "8000"))
MAX_BODY = 128 * 1024 * 1024  # 128 MB (para /api/zip)
MAX_IMAGE_B64 = 8 * 1024 * 1024  # 8 MB de imagen decodificada en /api/render
JSON_ERRORS = (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError)

CODE_RE = re.compile(r"^[A-Za-z0-9-]{1,16}$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
BG_VALUE_RE = re.compile(
    r"^(?:[0-9]+(?:\.[0-9]+)?%|[A-Za-z]+)(?:\s+(?:[0-9]+(?:\.[0-9]+)?%|[A-Za-z]+))*$"
)
FILENAME_RE = re.compile(r"^[A-Za-z0-9_.-]+\.png$")


# --- Validación -------------------------------------------------------------

def require_str(payload: dict, field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        raise ValueError(f"el campo '{field}' debe ser texto")
    return value


def require_code(payload: dict) -> str:
    code = payload.get("code", "")
    if not isinstance(code, str) or not CODE_RE.match(code):
        raise ValueError("el campo 'code' no es válido")
    return code.upper()


def require_colors(payload: dict) -> list[str]:
    colors = payload.get("colors") or []
    if not isinstance(colors, list) or not all(
        isinstance(c, str) and COLOR_RE.match(c) for c in colors
    ):
        raise ValueError("el campo 'colors' debe ser una lista de hex")
    return list(dict.fromkeys(colors))[:2]


def require_bg(payload: dict) -> tuple[str | None, str | None]:
    bg = payload.get("bg") or {}
    if not isinstance(bg, dict):
        raise ValueError("el campo 'bg' debe ser un objeto")
    position = _bg_value(bg.get("position"), "position")
    size = _bg_value(bg.get("size"), "size")
    return position, size


def _bg_value(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not BG_VALUE_RE.match(value.strip()):
        raise ValueError(f"'bg.{field}' no válido")
    return value.strip()


def decode_image(value: str) -> bytes:
    data = value.split(",", 1)[1] if "," in value else value
    try:
        raw = base64.b64decode(data, validate=True)
    except Exception as exc:
        raise ValueError("imagen base64 no válida") from exc
    if len(raw) > MAX_IMAGE_B64:
        raise ValueError("la imagen supera los 8 MB")
    if not (raw.startswith(b"\x89PNG") or raw.startswith(b"\xff\xd8")):
        raise ValueError("la imagen debe ser PNG o JPEG")
    return raw


# --- Servicios ---------------------------------------------------------------

def generate_all(text: str, chrome: str, api_base: str, component: str) -> dict:
    entries = parse_text(text)
    result: dict = {"cards": [], "errors": []}
    if not entries:
        return result

    def run(entry: tuple[str, str]) -> dict:
        code, qty = entry
        out_path = CACHE_DIR / f"{code}.png"
        try:
            name, colors = generate_png(code, qty, api_base, chrome, out_path, component)
            return {
                "status": "ok",
                "code": code,
                "name": name,
                "qty": qty,
                "colors": colors,
                "png": base64.b64encode(out_path.read_bytes()).decode("ascii"),
            }
        except JSON_ERRORS as exc:
            return {"status": "error", "code": code, "reason": str(exc)}

    with ThreadPoolExecutor(max_workers=RENDER_WORKERS) as pool:
        for item in pool.map(run, entries):
            if item["status"] == "ok":
                result["cards"].append(
                    {
                        "code": item["code"],
                        "name": item["name"],
                        "qty": item["qty"],
                        "colors": item["colors"],
                        "png_b64": item["png"],
                    }
                )
            else:
                result["errors"].append(
                    {"code": item["code"], "reason": item["reason"]}
                )
    return result


def render_card(payload: dict) -> str:
    """Re-render de una carta editada. Devuelve el PNG en base64."""
    component = require_str(payload, "component") if "component" in payload else "card"
    resolve_component(component)

    name = payload.get("name", "")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("falta el campo 'name'")
    name = name.strip()[:80]

    code = require_code(payload)
    quantity = require_str(payload, "quantity").strip()[:8]
    colors = require_colors(payload)
    bg_position, bg_size = require_bg(payload)

    image_path = resolve_image(payload.get("image"), code)
    out_path = CACHE_DIR / f"{code}.render.png"
    try:
        render_png(
            CardRenderRequest(
                component=component,
                name=name,
                code=code,
                quantity=quantity,
                image_path=image_path,
                chrome=find_chrome(),
                out_path=out_path,
                colors=colors,
                bg_position=bg_position,
                bg_size=bg_size,
            )
        )
        return base64.b64encode(out_path.read_bytes()).decode("ascii")
    finally:
        if image_path.parent == UPLOAD_DIR:
            image_path.unlink(missing_ok=True)


def resolve_image(image_b64: object, code: str):
    if not image_b64:
        try:
            return find_art(code)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
    if not isinstance(image_b64, str):
        raise ValueError("el campo 'image' debe ser base64")
    raw = decode_image(image_b64)
    ext = ".png" if raw.startswith(b"\x89PNG") else ".jpg"
    # Se guarda en UPLOAD_DIR con nombre único para no machacar el arte de la API
    # (ART_DIR) y se borra al terminar el render.
    return write_image_bytes(raw, UPLOAD_DIR / f"{code}-{uuid.uuid4().hex}{ext}")


def build_files_zip(files: list) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in files:
            filename = entry.get("filename")
            png_b64 = entry.get("png_b64")
            if not isinstance(filename, str) or not FILENAME_RE.match(filename):
                raise ValueError(f"nombre de archivo no válido: {filename!r}")
            if not isinstance(png_b64, str):
                raise ValueError(f"falta png_b64 para {filename}")
            try:
                data = base64.b64decode(png_b64.split(",", 1)[-1], validate=True)
            except Exception as exc:
                raise ValueError(f"base64 no válido para {filename}") from exc
            zf.writestr(filename, data)
    return buffer.getvalue()


def build_generate_zip(
    text: str, chrome: str, api_base: str, component: str
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for code, qty in parse_text(text):
            out_path = CACHE_DIR / f"{code}.png"
            try:
                generate_png(code, qty, api_base, chrome, out_path, component)
                zf.write(out_path, arcname=f"{code}.png")
            except JSON_ERRORS:
                continue
    return buffer.getvalue()


# --- HTTP Handler -------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "cartas-api/1.0"

    def log_message(self, fmt, *args):  # noqa: N802 - firma de BaseHTTPRequestHandler
        pass

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status=status)

    def _send_bytes(
        self, body: bytes, content_type: str, status: int = 200, filename: str | None = None
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("cuerpo demasiado grande")
        data = self.rfile.read(length)
        try:
            payload = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"JSON inválido: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("el cuerpo debe ser un objeto JSON")
        return payload

    def _read_body(self) -> tuple[str, str]:
        payload = self._read_json()
        text = payload.get("text", "")
        if not isinstance(text, str):
            raise ValueError("falta el campo 'text'")
        component = payload.get("component", "card")
        if not isinstance(component, str):
            raise ValueError("el campo 'component' debe ser texto")
        resolve_component(component)
        return text, component

    def _query_param(self, name: str) -> str:
        query = parse_qs(urlparse(self.path).query)
        values = query.get(name)
        return values[0] if values else ""

    def _handle_render(self) -> None:
        payload = self._read_json()
        self._send_json({"png_b64": render_card(payload)})

    def _handle_zip(self) -> None:
        payload = self._read_json()
        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("falta el campo 'files'")
        self._send_bytes(build_files_zip(files), "application/zip", filename="cartas.zip")

    def _handle_generate(self) -> None:
        text, component = self._read_body()
        api_base = get_api_base()
        if not api_base:
            raise RuntimeError("falta API_CARD")
        chrome = find_chrome()
        if self.path == "/api/generate/zip":
            body = build_generate_zip(text, chrome, api_base, component)
            self._send_bytes(body, "application/zip", filename="cartas.zip")
        else:
            self._send_json(generate_all(text, chrome, api_base, component))

    def do_POST(self):  # noqa: N802 - método HTTP
        if self.path == "/api/render":
            self._run_json(self._handle_render)
            return
        if self.path == "/api/zip":
            self._run_json(self._handle_zip)
            return
        if self.path in ("/api/generate", "/api/generate/zip"):
            try:
                self._handle_generate()
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self._send_json({"error": str(exc)}, 500)
            return
        self._send_json({"error": "ruta no encontrada"}, 404)

    def _run_json(self, handler) -> None:
        try:
            handler()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)

    def do_GET(self):  # noqa: N802 - método HTTP
        if self.path == "/healthz":
            self._send_json({"ok": True})
            return
        if self.path == "/api/components":
            self._send_json({"components": list_components()})
            return
        if self.path.startswith("/api/art"):
            code = self._query_param("code")
            if not code or not CODE_RE.match(code):
                self._send_json({"error": "falta el parámetro 'code'"}, 400)
                return
            try:
                art = find_art(code.upper())
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 404)
                return
            self._send_json(
                {"art_b64": base64.b64encode(art.read_bytes()).decode("ascii")}
            )
            return
        self._send_json({"error": "ruta no encontrada"}, 404)


def main() -> None:
    if UPLOAD_DIR.is_dir():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"API escuchando en http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()