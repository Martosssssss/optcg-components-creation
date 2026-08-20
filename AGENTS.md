# AGENTS.md

Guía para agentes que trabajan en este repositorio.

## Skills

Carga **todas** las skills disponibles en `.opencode/skills/*` (cada carpeta tiene un `SKILL.md`) y aplícalas cuando la tarea coincida con su descripción:

- `.opencode/skills/clean-code` — principios de Clean Code para escribir/refactorizar código.
- `.opencode/skills/minimalist-ui` — interfaces UI minimalistas y editoriales (paleta monocromática cálida, tipografía con contraste, sin gradientes ni sombras pesadas).
- `.opencode/skills/web-design-guidelines` — revisión de UI/UX accesibilidad y buenas prácticas web.

## Resumen del proyecto

Genera un PNG por carta de One Piece TCG a partir de `generate.txt` (`<cantidad>x<codigo>`, ej: `4xOP15-014`) consultando la API de One Piece TCG (`API_CARD` en `.env`) y capturando un componente de `components/` con Chrome headless.

## Comandos

- **Exportar cartas**: `python3 export_cards.py --component card` (lee `generate.txt`, descarga imágenes a `.cache/`, escribe PNG en `exports/<codigo>.png` y errores en `errors.txt`). `--component` elige la plantilla de `components/`.
- **Web (Docker)**: `docker compose up -d --build` y abrir `http://localhost:8080` (selector de componente → pegar texto → generar).
- **Vista previa de un componente**: abrir `components/<nombre>.html` en el navegador.

## Estructura

| Ruta | Descripción |
|---|---|
| `components/` | Plantillas de componentes (`card.html`, `leader.html`, …); cada una define su propio diseño con las clases `.name`, `.code` (opc.), `.quantity` (opc.) y `.character`. Opcionalmente pueden consumir las variables CSS `--optcg-c1`/`--optcg-c2` (colores de la carta según `card_color`, ver `OPTCG_COLORS` en `generator.py`) con fallback para vista previa directa |
| `generator.py` | Núcleo compartido: `.env` → API → descarga imágenes → Chrome headless → PNG. Constantes de encuadre `WINDOW_W`, `WINDOW_H`, `PAD_TOP`, `PAD_LEFT`. Las peticiones a la API se espacian (`OPTCG_MIN_INTERVAL`, por defecto 1 s) y se reintentan ante 429, y `card_color` se mapea vía `OPTCG_COLORS` |
| `export_cards.py` | CLI que usa `generator.py` |
| `server.py` | API web: `GET /api/components`, `POST /api/generate`, `POST /api/generate/zip`, `GET /healthz` |
| `web/` | Frontend estático (nginx): selector de componentes con preview + generador |
| `generate.txt` | Lista de cartas a exportar (formato `<cantidad>x<codigo>`) |
| `.env` | `API_CARD` = URL base de la API de cartas |
| `.cache/` | Imágenes y metadatos descargados (caché persistente; se reutiliza entre ejecuciones para no golpear la API) |
| `exports/` | PNG generados (1948×367 px, fondo transparente) |
| `errors.txt` | Códigos que fallaron (código + motivo) |
| `generate.example.txt` | Ejemplo del formato de `generate.txt` |

## Convenciones

- **Idioma**: comentarios, mensajes de la CLI y documentación en español.
- **Sin dependencias de terceros en Python**: solo stdlib (`urllib`, `json`, `subprocess`, etc.). Si se necesita una librería, confirmar antes.
- **Solo Python 3**; no usar `functools`/sintaxis anterior a la versión actual de forma innecesaria.
- **Archivos de trabajo**: `.env`, `.cache/`, `exports/`, `errors.txt` y `cartas/` están en `.gitignore`; no commitearlos.
- **Componentes**: cada `components/*.html` debe ser autónomo (CSS inline). El generador inyecta en las clases `.name`, `.code`, `.quantity` y `.character` (las que falten se omiten); `generator.py` valida el nombre con `resolve_component()` para evitar path traversal.
- **Verificación**: tras modificar un componente, comprobar que la exportación sigue saliendo a 1948×367 px con transparencia. Los constantes de encuadre (`WINDOW_W`, `WINDOW_H`, `PAD_TOP`, `PAD_LEFT`) están en `generator.py` y deben cuadrar con el zoom `scale(1.05)` del `.card` y el `background-position`/`background-size` de `.character` en el componente.
- **Commits**: mensajes concisos en español.