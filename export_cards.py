#!/usr/bin/env python3
"""Exporta un componente de components/ como PNG por cada carta de generate.txt.

Uso:
    python3 export_cards.py [--component card]

generate.txt tiene una línea por carta con el formato <cantidad>x<codigo>
(ej: 4xOP15-014). Por cada código consulta la API definida en API_CARD (.env),
descarga la imagen y exporta el componente a exports/<codigo>.png.

Los códigos que fallan se registran en errors.txt. Requiere Google Chrome.
"""

import argparse
import os
import sys
from pathlib import Path

import generator

BASE_DIR = generator.BASE_DIR
OUTPUT_DIR = BASE_DIR / "exports"
GENERATE_FILE = BASE_DIR / "generate.txt"
ERRORS_FILE = BASE_DIR / "errors.txt"


def read_generate() -> list[tuple[str, str]]:
    if not GENERATE_FILE.is_file():
        sys.exit(f"No se encontró {GENERATE_FILE}.")
    entries = generator.parse_text(GENERATE_FILE.read_text(encoding="utf-8"))
    if not entries:
        sys.exit(f"{GENERATE_FILE} no tiene cartas válidas.")
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta cartas a PNG.")
    parser.add_argument(
        "--component",
        default="card",
        help="Componente de components/ a usar (por defecto: card).",
    )
    args = parser.parse_args()

    chrome = generator.find_chrome()
    api_base = generator.get_api_base()
    if not api_base:
        sys.exit("Falta la variable API_CARD en .env o en el entorno.")

    try:
        generator.resolve_component(args.component)
    except ValueError as exc:
        sys.exit(str(exc))

    OUTPUT_DIR.mkdir(exist_ok=True)
    generator.CACHE_DIR.mkdir(exist_ok=True)

    entries = read_generate()

    print(f"Chrome: {os.path.basename(chrome)}")
    print(f"API: {api_base}")
    print(f"Componente: {args.component}")
    print(f"Exportando {len(entries)} carta(s) a {OUTPUT_DIR}\n")

    errors: list[str] = []
    for idx, (code, qty) in enumerate(entries, 1):
        qty_label = f"x{qty}" if not qty.startswith("x") else qty
        print(f"[{idx}/{len(entries)}] {code} ({qty_label})")
        try:
            name = generator.generate_png(
                code, qty_label, api_base, chrome,
                generator.CACHE_DIR, OUTPUT_DIR / f"{code}.png", args.component,
            )
            out_path = OUTPUT_DIR / f"{code}.png"
            print(f"  → {name}: {out_path.name} ({out_path.stat().st_size} bytes)")
        except (OSError, ValueError) as exc:
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
