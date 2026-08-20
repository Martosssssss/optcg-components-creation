# cartas-ui

Genera un PNG por cada carta de One Piece TCG renderizando un componente de `back/components/` a partir de una lista de códigos (`generate.txt`) y de la API de One Piece TCG.

## Características

- Lee `generate.txt` con el formato `<cantidad>x<codigo>` (ej: `4xOP15-014`).
- Permite elegir entre varios componentes visuales (`back/components/*.html`, ej: `card`, `leader`).
- Consulta el nombre e imagen de cada carta a la API definida en `API_CARD` (`.env`).
- Descarga las imágenes a `.cache/art/` (se reutilizan entre ejecuciones y se sirven para el editor vía `/api/art`).
- Exporta cada carta a `exports/<codigo>.png` (1948×367 px, fondo transparente).
- Si algún código falla, lo anota en `errors.txt` y continúa con el resto.
- Web en React (Vite + TypeScript + Tailwind + shadcn/ui) con selector de componente, generador y editor con vista previa en tiempo real.
- Cada carta generada es editable (nombre, código, cantidad, colores, imagen y su posición/zoom) y se re-renderiza sin volver a consultar la API. El componente `card` usa su color sólido por defecto (naranja); el `leader` aplica el degradado con los colores de la API.
- Los componentes de carta se escriben una vez en React (`web/src/cards/`) y se exportan a `back/components/*.html` mediante SSR (`npm run build:components`), manteniendo una única fuente de verdad.
- El backend está dividido en módulos (sin dependencias de terceros): `config.py`, `optcg_client.py`, `render.py`, `generator.py`, `server.py` y la CLI `export_cards.py`.

## Requisitos

- Python 3
- Google Chrome (para la captura headless)

## Configuración

Crea un archivo `.env` con la API que, concatenando el código de carta, devuelve su información:

```
API_CARD=https://www.optcgapi.com/api/sets/card/
```

## Uso (CLI)

1. Rellena `generate.txt` con una línea por carta (ver `generate.example.txt`):

   ```
   1xOP15-002
   4xOP15-014
   2xOP05-019
   ```

2. Ejecuta (elige el componente con `--component`; por defecto `card`):

   ```bash
   python3 back/export_cards.py --component card
   ```

3. El resultado se guarda en `exports/<codigo>.png`.

## Uso (web con Docker)

```bash
docker compose up -d --build
```

Abre `http://localhost:8080`, elige un componente en la primera pantalla y genera cartas pegando el texto o subiendo un `.txt`. La API expone:

- `GET  /api/components` → lista de componentes disponibles.
- `POST /api/generate` → `{ "text": "4xOP15-014", "component": "card" }` → PNG en base64 (por carta: `name`, `code`, `qty`, `colors` y `png_b64`).
- `POST /api/generate/zip` → igual pero devuelve un ZIP con los PNG.
- `GET  /api/art?code=X` → arte original de una carta en base64 (desde `.cache/art/`).
- `POST /api/render` → re-render de una carta editada sin tocar la API de cartas (nombre, código, cantidad, imagen en base64, colores y `bg.position`/`bg.size`). Devuelve `{ "png_b64": … }`.
- `POST /api/zip` → `{ "files": [{ "filename", "png_b64" }] }` → ZIP con las imágenes **actuales** del cliente (sin regenerar, conserva las ediciones).
- `GET  /healthz` → estado.

### Editar una carta generada

Cada carta del resultado tiene un botón **Editar** que abre un editor con vista previa en tiempo real donde puedes cambiar:

- **Nombre, código y cantidad**.
- **Colores** (color de la carta o del degradado del líder).
- **Imagen**: sube otra desde tu equipo o restablece el arte original.
- **Posición de la imagen**: zoom (%) y posición horizontal/vertical (%).

El editor re-renderiza la carta en local (no vuelve a consultar la API de cartas) y actualiza el resultado. El botón **Descargar** baja siempre la versión actual, y **Descargar todas (ZIP)** empaqueta las cartas tal y como están en pantalla (con tus modificaciones) sin regenerar nada.

> Nota: en Docker, `.cache/` (metadatos, arte y PNG) vive dentro del contenedor de la API, sin volumen: se conserva entre ejecuciones del mismo contenedor pero se pierde al recrearlo. El flujo de edición no depende de él: usa el arte recuperado vía `/api/art` o la imagen que subas.

## Estructura del proyecto

| Ruta | Descripción |
|---|---|
| `back/` | Backend (Python, solo stdlib): `config.py` (constantes y entorno), `optcg_client.py` (API de cartas con throttling/caché), `render.py` (HTML de exportación + captura Chrome), `generator.py` (orquestación), `server.py` (API web) y `export_cards.py` (CLI) |
| `back/components/` | Plantillas `*.html` de los componentes (generadas por SSR desde `web/src/cards/`; no se editan a mano) |
| `back/Dockerfile` | Imagen de la API (Python + Chromium) |
| `web/src/cards/` | Componentes de carta en React (`Card.tsx`, `Leader.tsx`, `cards.css`) — única fuente de verdad |
| `web/` | Frontend React (Vite + TypeScript + Tailwind + shadcn/ui) |
| `web/src/lib/` | Helpers compartidos (`helpers.ts`, `utils.ts` con `cn`) |
| `web/src/hooks/` | `useDeck.ts` (estado del resultado) y `useCardEditor.ts` (estado del editor de cartas) |
| `web/src/components/editor/` | Editor de cartas: `CardEditorDialog` + subcomponentes (`ColorControls`, `SliderControls`, `ImageControls`, `PreviewPane`) |
| `generate.txt` | Lista de cartas a exportar |
| `.env` | Variable `API_CARD` con la URL base de la API |
| `.cache/` | Imágenes (`.cache/art/`), metadatos y PNG (caché persistente) |
| `exports/` | PNG generados |
| `errors.txt` | Códigos que fallaron durante la exportación |

## Crear o modificar un componente

Los componentes se definen en React (`web/src/cards/`) y se exportan a `back/components/*.html` para que el generador (Python, sin Node) los consuma:

```bash
cd web
npm run build:components   # regenera back/components/card.html, back/components/leader.html, …
npm run dev                # desarrollo: abre http://localhost:5173 (proxy al API en :8080)
npm run build              # tsc + bundle de producción en web/dist
```

Cada componente React usa clases `.name`, `.code`, `.quantity` y `.character` (las que falten se omiten), y puede consumir las variables CSS `--optcg-c1`/`--optcg-c2` (colores de la carta según `card_color`) con fallback para vista previa. El CSS compartido está en `web/src/cards/cards.css`.

Para que la exportación coincida con lo que ves en el navegador, no cambies las dimensiones del `.card` (1826×294 px a ventana de 1948 px). Si cambias el diseño, ajusta en `back/config.py` las constantes `WINDOW_W`, `WINDOW_H`, `PAD_TOP` y `PAD_LEFT`. El `.card` lleva un zoom de 1.05 (`transform: scale(1.05)` desde el centro) y el fondo de la exportación es transparente. Tras tocar un componente, regenera los `back/components/*.html` y comprueba que la exportación sigue saliendo a 1948×367 px con transparencia.