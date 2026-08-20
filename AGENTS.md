# AGENTS.md

Guía para agentes que trabajan en este repositorio.

## Skills

Carga **todas** las skills disponibles en `.opencode/skills/*` (cada carpeta tiene un `SKILL.md`) y aplícalas cuando la tarea coincida con su descripción:

- `.opencode/skills/clean-code` — principios de Clean Code para escribir/refactorizar código.
- `.opencode/skills/minimalist-ui` — interfaces UI minimalistas y editoriales (paleta monocromática cálida, tipografía con contraste, sin gradientes ni sombras pesadas).
- `.opencode/skills/web-design-guidelines` — revisión de UI/UX accesibilidad y buenas prácticas web.
- `.opencode/skills/frontend-ui` — guía para construir la UI del frontend en React.

## Resumen del proyecto

Genera un PNG por carta de One Piece TCG a partir de `generate.txt` (`<cantidad>x<codigo>`, ej: `4xOP15-014`) consultando la API de One Piece TCG (`API_CARD` en `.env`) y capturando un componente de `back/components/` con Chrome headless.

## Comandos

- **Exportar cartas**: `python3 back/export_cards.py --component card` (lee `generate.txt`, descarga imágenes a `.cache/art/`, escribe PNG en `exports/<codigo>.png` y errores en `errors.txt`). `--component` elige la plantilla de `back/components/`.
- **Web (Docker)**: `docker compose up -d --build` y abrir `http://localhost:8080` (selector de componente → pegar texto → generar → editar cartas → descargar todas).
- **Frontend (desarrollo)**: `cd web && npm run dev` (Vite en `:5173` con proxy a `:8080`), `npm run build` (tsc + bundle), `npm run build:components` (regenera `back/components/*.html` desde `web/src/cards/`).
- **Vista previa de un componente**: abrir `back/components/<nombre>.html` en el navegador.

## Estructura

| Ruta | Descripción |
|---|---|
| `back/` | Backend (Python, solo stdlib). Módulos: `config.py` (rutas, constantes de encuadre `WINDOW_W`/`WINDOW_H`/`PAD_TOP`/`PAD_LEFT`, `OPTCG_COLORS`, regexes y helpers de entorno/Chrome), `optcg_client.py` (API de cartas con throttling `OPTCG_MIN_INTERVAL`, reintentos ante 429 y caché en `.cache/meta/` y `.cache/art/`), `render.py` (`list_components`, `resolve_component` contra path traversal, `build_export_html` con overrides nombre/código/cantidad/imagen/colores/`bg_position`/`bg_size`, captura con Chrome), `generator.py` (orquestación y re-exports), `server.py` (API web) y `export_cards.py` (CLI) |
| `back/components/` | Plantillas `*.html` de los componentes (**generadas por SSR** desde `web/src/cards/`; no se editan a mano, se regeneran con `npm run build:components`). Cada una define su propio diseño con las clases `.name`, `.code` (opc.), `.quantity` (opc.) y `.character`. Opcionalmente pueden consumir las variables CSS `--optcg-c1`/`--optcg-c2` (colores de la carta según `card_color`, ver `OPTCG_COLORS` en `back/config.py`) con fallback para vista previa directa |
| `back/Dockerfile` | Imagen de la API (Python + Chromium); contexto de build `./back` |
| `web/src/cards/` | **Única fuente de verdad** de los componentes de carta en React: `Card.tsx`, `Leader.tsx`, `types.ts` (props compartidas y `DEFAULT_BG`/`bgStyle`/`colorVars`), `cards.css` (CSS plano, no Tailwind) y `CardPreview.tsx` (wrapper escalado para previews) |
| `web/src/components/` | UI de la app (React + Tailwind + shadcn/ui): `StepPicker`, `StepInput`, `ResultsGrid`, `editor/CardEditorDialog` (composición) + `editor/` subcomponentes (`ColorControls`, `SliderControls`, `ImageControls`, `PreviewPane`), y `ui/` |
| `web/src/hooks/` | `useDeck.ts` (estado del resultado) y `useCardEditor.ts` (estado del editor de cartas: nombre/código/cantidad/colores/zoom/posición/imagen) |
| `web/src/lib/` | `helpers.ts` (`DEFAULT_BG`, `bgToPositionSize`, `normalizeQty`, `downloadBlob`, `readFileAs*`) y `utils.ts` (`cn`) |
| `web/src/` | `App.tsx` (flujo: picker → input → resultados), `api.ts` (cliente de `/api`), `types.ts` |
| `server.py` → `back/server.py` | API web: `GET /api/components`, `GET /api/art?code=X`, `POST /api/generate`, `POST /api/generate/zip`, `POST /api/render` (re-render local, sin tocar la API de cartas), `POST /api/zip` (ZIP con las PNG del cliente), `GET /healthz`. Límites: `MAX_BODY` 128 MB, imagen ≤ 8 MB (PNG/JPEG por magic bytes) y validaciones de entrada (`CODE_RE`, `COLOR_RE`, `BG_VALUE_RE`, `FILENAME_RE`) contra inyección |
| `web/` | Frontend React (Vite+TS+Tailwind+shadcn). `npm run dev` con proxy a `:8080`; en Docker se construye (`web/Dockerfile` multi-stage: node → nginx) y sirve `web/dist` |
| `generate.txt` | Lista de cartas a exportar (formato `<cantidad>x<codigo>`), leído desde `back/` |
| `.env` | `API_CARD` = URL base de la API de cartas (en `back/.env`) |
| `.cache/` | Imágenes (`.cache/art/`), metadatos y PNG (caché persistente en `back/.cache/`; se reutiliza entre ejecuciones para no golpear la API) |
| `exports/` | PNG generados (1948×367 px, fondo transparente) en `back/exports/` |
| `errors.txt` | Códigos que fallaron (código + motivo) en `back/errors.txt` |
| `generate.example.txt` | Ejemplo del formato de `generate.txt` |

# Frontend

## Stack
- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide React
- Motion when animations are useful

## UI rules
- Prefer shadcn/ui components over custom implementations.
- Use Lucide for icons.
- Use Tailwind for styling.
- Keep interfaces simple and compact.
- Make everything responsive.
- Avoid unnecessary dependencies.
- Don't introduce a new UI library without asking.

## Development
- Run the app after significant changes.
- Check TypeScript errors.
- Keep components small and reusable.

## Notas de desarrollo

- En desarrollo usa `cd web && npm run dev` (Vite en `:5173` con proxy al API en `:8080`); los cambios del frontend se ven al recargar. En Docker el frontend se construye en la imagen (si cambian `web/` o `web/src/cards/`: `docker compose up -d --build web`).
- Si cambian `back/*.py`: `docker compose up -d --build` (reconstruye la imagen de la API).
- Si cambia `nginx.conf`: `docker compose restart web` (la config está montada pero nginx necesita releerla).
- `.cache/` vive **dentro** del contenedor de la API (sin volumen): persiste entre ediciones pero se pierde al recrear el contenedor. El flujo web funciona sin él (el editor usa el arte recuperado vía `/api/art` o la imagen que sube el usuario).
- El frontend guarda cada carta en un `deck[]` (código, nombre, cantidad, colores, arte y PNG actual). Editar = `POST /api/render`; comprimir todas = `POST /api/zip` con el deck; ninguna operación vuelve a consultar la API de cartas.

## Convenciones

- **Idioma**: comentarios, mensajes de la CLI y documentación en español.
- **Sin dependencias de terceros en Python**: solo stdlib (`urllib`, `json`, `subprocess`, etc.). Si se necesita una librería, confirmar antes.
- **Solo Python 3**; no usar `functools`/sintaxis anterior a la versión actual de forma innecesaria.
- **Archivos de trabajo**: `.env`, `.cache/`, `exports/`, `errors.txt` y `cartas/` están en `.gitignore`; no commitearlos.
- **Componentes**: la fuente de verdad son los componentes React en `web/src/cards/`; los `back/components/*.html` se regeneran con `npm run build:components` y deben ser autónomos (CSS inline). El generador inyecta en las clases `.name`, `.code`, `.quantity` y `.character` (las que falten se omiten); `back/render.py` valida el nombre con `resolve_component()` para evitar path traversal. No importar CSS dentro de los componentes React (la app lo carga globalmente en `main.tsx` y el SSR lo inlinea desde `cards.css`).
- **Verificación**: tras modificar un componente, regenerar con `npm run build:components` y comprobar que la exportación sigue saliendo a 1948×367 px con transparencia. Los constantes de encuadre (`WINDOW_W`, `WINDOW_H`, `PAD_TOP`, `PAD_LEFT`) están en `back/config.py` y deben cuadrar con el zoom `scale(1.05)` del `.card` y el `background-position`/`background-size` de `.character` en el componente.
- **Commits**: mensajes concisos en español.