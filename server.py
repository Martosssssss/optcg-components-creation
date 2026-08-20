#!/usr/bin/env python3
"""API web para generar cartas a partir de un texto NxCODIGO.

Endpoints:
    GET  /api/components      → lista de componentes disponibles (components/*.html)
    POST /api/generate        → JSON {text, component} → JSON con PNG en base64 y errores
    POST /api/generate/zip    → JSON {text, component} → ZIP binario con los PNG
    GET  /healthz             → 200 ok

component (opcional, por defecto "card") selecciona la plantilla de components/.
Requiere generator.py (y Chromium disponible). Puerto por defecto: 8000.
"""

import base64
import io
import json
import os
import urllib.error
import zipfile
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import generator

PORT = int(os.environ.get("PORT", "8000"))
MAX_BODY = 1024 * 1024  # 1 MB
MAX_WORKERS = 4
JSON_ERRORS = (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError)


def generate_all(text: str, chrome: str, api_base: str, component: str) -> dict:
    entries = generator.parse_text(text)
    result = {"cards": [], "errors": []}
    if not entries:
        return result

    def run(entry: tuple[str, str]) -> dict:
        code, qty = entry
        qty_label = f"x{qty}" if not qty.startswith("x") else qty
        out_path = generator.CACHE_DIR / f"{code}.png"
        try:
            name = generator.generate_png(
                code, qty_label, api_base, chrome,
                generator.CACHE_DIR, out_path, component,
            )
            return {
                "status": "ok",
                "code": code,
                "name": name,
                "qty": qty,
                "png": base64.b64encode(out_path.read_bytes()).decode("ascii"),
            }
        except JSON_ERRORS as exc:
            return {"status": "error", "code": code, "reason": str(exc)}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for item in pool.map(run, entries):
            if item["status"] == "ok":
                result["cards"].append(
                    {
                        "code": item["code"],
                        "name": item["name"],
                        "qty": item["qty"],
                        "png_b64": item["png"],
                    }
                )
            else:
                result["errors"].append(
                    {"code": item["code"], "reason": item["reason"]}
                )
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "cartas-api/1.0"

    def log_message(self, fmt, *args):  # noqa: N802 - firma de BaseHTTPRequestHandler
        pass

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> tuple[str, str]:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("cuerpo demasiado grande")
        data = self.rfile.read(length)
        try:
            payload = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"JSON inválido: {exc}") from exc
        text = payload.get("text", "")
        if not isinstance(text, str):
            raise ValueError("falta el campo 'text'")
        component = payload.get("component", "card")
        if not isinstance(component, str):
            raise ValueError("el campo 'component' debe ser texto")
        generator.resolve_component(component)
        return text, component

    def do_POST(self):  # noqa: N802 - método HTTP
        if self.path not in ("/api/generate", "/api/generate/zip"):
            self._send_json({"error": "ruta no encontrada"}, 404)
            return
        try:
            text, component = self._read_body()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        chrome = generator.find_chrome()
        api_base = generator.get_api_base()
        if not api_base:
            self._send_json({"error": "falta API_CARD"}, 500)
            return

        if self.path == "/api/generate/zip":
            self._send_zip(text, chrome, api_base, component)
        else:
            result = generate_all(text, chrome, api_base, component)
            self._send_json(result)

    def _send_zip(
        self, text: str, chrome: str, api_base: str, component: str
    ) -> None:
        entries = generator.parse_text(text)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for code, qty in entries:
                qty_label = f"x{qty}" if not qty.startswith("x") else qty
                out_path = generator.CACHE_DIR / f"{code}.png"
                try:
                    generator.generate_png(
                        code, qty_label, api_base, chrome,
                        generator.CACHE_DIR, out_path, component,
                    )
                    zf.write(out_path, arcname=f"{code}.png")
                except JSON_ERRORS:
                    continue
        body = buffer.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", 'attachment; filename="cartas.zip"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - método HTTP
        if self.path == "/healthz":
            self._send_json({"ok": True})
            return
        if self.path == "/api/components":
            self._send_json({"components": generator.list_components()})
            return
        self._send_json({"error": "ruta no encontrada"}, 404)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"API escuchando en http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
