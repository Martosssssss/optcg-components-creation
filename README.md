# cartas-ui

Genera un PNG por cada carta de One Piece TCG renderizando un componente de `components/` a partir de una lista de códigos (`generate.txt`) y de la API de One Piece TCG.

## Características

- Lee `generate.txt` con el formato `<cantidad>x<codigo>` (ej: `4xOP15-014`).
- Permite elegir entre varios componentes visuales (`components/*.html`, ej: `card`, `leader`).
- Consulta el nombre e imagen de cada carta a la API definida en `API_CARD` (`.env`).
- Descarga las imágenes a `.cache/` (se reutilizan entre ejecuciones).
- Exporta cada carta a `exports/<codigo>.png` (1948×367 px, fondo transparente).
- Si algún código falla, lo anota en `errors.txt` y continúa con el resto.
- Servidor web con selector de componente y descarga individual o en ZIP.

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
   python3 export_cards.py --component card
   ```

3. El resultado se guarda en `exports/<codigo>.png`.

## Uso (web con Docker)

```bash
docker compose up -d --build
```

Abre `http://localhost:8080`, elige un componente en la primera pantalla y genera cartas pegando el texto o subiendo un `.txt`. La API expone:

- `GET  /api/components` → lista de componentes disponibles.
- `POST /api/generate` → `{ "text": "4xOP15-014", "component": "card" }` → PNG en base64.
- `POST /api/generate/zip` → igual pero devuelve un ZIP con los PNG.
- `GET  /healthz` → estado.

## Estructura del proyecto

| Ruta | Descripción |
|---|---|
| `components/` | Plantillas de los componentes (`card.html`, `leader.html`, …); el degradado del leader usa `card_color` de la API vía `--optcg-c1`/`--optcg-c2` |
| `generator.py` | Núcleo compartido (API → descarga → render → PNG) |
| `export_cards.py` | CLI de exportación (usa `generator.py`) |
| `server.py` | API web (`/api/components`, `/api/generate`, `/api/generate/zip`) |
| `web/` | Frontend estático servido por nginx (selector de componente + generador) |
| `generate.txt` | Lista de cartas a exportar |
| `.env` | Variable `API_CARD` con la URL base de la API |
| `.cache/` | Imágenes y metadatos descargados (caché persistente) |
| `exports/` | PNG generados |
| `errors.txt` | Códigos que fallaron durante la exportación |

## Crear un componente

Cada `components/*.html` es una plantilla independiente. Para que la carta se rellene automáticamente, el componente debe usar estas clases (las que falten se omiten):

- **Nombre** → `.name`
- **Número de serie** → `.code` (opcional)
- **Cantidad** → `.quantity` (opcional, se muestra como `xN`)
- **Imagen del personaje** → `.character` (el generador la pone como `background-image`)

Para que la exportación coincida con lo que ves en el navegador, no cambies las dimensiones del `.card` (1826×294 px a ventana de 1948 px). Si cambias el diseño, ajusta en `generator.py` las constantes `WINDOW_W`, `WINDOW_H`, `PAD_TOP` y `PAD_LEFT`. El `.card` lleva un zoom de 1.05 (`transform: scale(1.05)` desde el centro) y el fondo de la exportación es transparente.