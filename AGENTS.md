# AGENTS.md

Guía para agentes que trabajan en este repositorio.

## Skills

Carga **todas** las skills disponibles en `.opencode/skills/*` (cada carpeta tiene un `SKILL.md`) y aplícalas cuando la tarea coincida con su descripción:

- `.opencode/skills/clean-code` — principios de Clean Code para escribir/refactorizar código.
- `.opencode/skills/minimalist-ui` — interfaces UI minimalistas y editoriales (paleta monocromática cálida, tipografía con contraste, sin gradientes ni sombras pesadas).
- `.opencode/skills/web-design-guidelines` — revisión de UI/UX accesibilidad y buenas prácticas web.

## Resumen del proyecto

Genera un PNG por carta de One Piece TCG a partir de `generate.txt` (`<cantidad>x<codigo>`, ej: `4xOP15-014`) consultando la API de One Piece TCG (`API_CARD` en `.env`) y capturando `index.html` con Chrome headless.

## Comandos

- **Exportar cartas**: `python3 export_cards.py` (lee `generate.txt`, descarga imágenes a `.cache/`, escribe PNG en `exports/<codigo>.png` y errores en `errors.txt`).
- **Vista previa**: abrir `index.html` en el navegador.

## Estructura

| Ruta | Descripción |
|---|---|
| `export_cards.py` | Script principal: `.env` → API → descarga imágenes → Chrome headless → PNG |
| `index.html` | Componente visual de la carta (`.name`, `.code`, `.quantity`, `.character` como fondo) |
| `generate.txt` | Lista de cartas a exportar (formato `<cantidad>x<codigo>`) |
| `.env` | `API_CARD` = URL base de la API de cartas |
| `.cache/` | Imágenes descargadas (se borra en cada ejecución) |
| `exports/` | PNG generados (1948×367 px, fondo transparente) |
| `errors.txt` | Códigos que fallaron (código + motivo) |
| `generate.example.txt` | Ejemplo del formato de `generate.txt` |

## Convenciones

- **Idioma**: comentarios, mensajes de la CLI y documentación en español.
- **Sin dependencias de terceros en Python**: solo stdlib (`urllib`, `json`, `subprocess`, etc.). Si se necesita una librería, confirmar antes.
- **Solo Python 3**; no usar `functools`/sintaxis anterior a la versión actual de forma innecesaria.
- **Archivos de trabajo**: `.env`, `.cache/`, `exports/`, `errors.txt` y `cartas/` están en `.gitignore`; no commitearlos.
- **Verificación**: tras modificar `index.html`, comprobar que la exportación sigue saliendo a 1948×367 px con transparencia. Los constantes de encuadre (`WINDOW_W`, `WINDOW_H`, `PAD_TOP`, `PAD_LEFT`) están en `export_cards.py` y deben cuadrar con el zoom `scale(1.05)` del `.card` y el `background-position`/`background-size` de `.character` en `index.html`.
- **Commits**: mensajes concisos en español.