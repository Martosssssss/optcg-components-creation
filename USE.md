# cartas-ui — Exportación de cartas

Genera un PNG por cada carta del texto `NxCODIGO` renderizando un componente de `back/components/`, consultando el nombre y la imagen de cada carta a la API de One Piece TCG (`API_CARD`).

## Requisitos

- Python 3
- Google Chrome (para la captura headless)

## Configuración

Crea un `.env` con la API que, concatenando el código de carta, devuelve su información:

```
API_CARD=https://www.optcgapi.com/api/sets/card/
```

Ejemplo de petición: `GET https://www.optcgapi.com/api/sets/card/OP15-002` → JSON con `card_name`, `card_set_id` y `card_image`.

## Uso (CLI)

1. Rellena `generate.txt` con una línea por carta, formato `<cantidad>x<codigo>`:

   ```
   1xOP15-002
   4xOP15-014
   2xOP05-019
   ```

2. Ejecuta (elige el componente con `--component`; por defecto `card`):

   ```bash
   python3 back/export_cards.py --component card
   ```

3. Por cada línea, el script consulta la API, descarga la imagen a `.cache/art/` y exporta la carta a `exports/<codigo>.png` (tamaño 1948×367 px, fondo transparente).

4. Si algún código falla, se anota en `errors.txt` (código + motivo) y el proceso continúa con el resto. Al terminar se muestra un resumen.

## Uso (web con Docker)

```bash
docker compose up -d --build
```

Abre `http://localhost:8080`. En la primera pantalla elige un componente (con vista previa); después pega el texto o sube un `.txt`, genera las cartas y, si quieres, edita cada una antes de descargar (individual o ZIP de todo el resultado).

### Endpoints

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| `GET` | `/api/components` | — | `{"components": ["card", "leader"]}` |
| `GET` | `/api/art?code=X` | — | `{"art_b64": …}` arte original de la carta |
| `POST` | `/api/generate` | `{"text": "4xOP15-014", "component": "card"}` | JSON con `cards` (PNG en base64) y `errors` |
| `POST` | `/api/generate/zip` | igual que `generate` | ZIP binario con los PNG |
| `POST` | `/api/render` | `{"component", "name", "code", "quantity", "colors", "image", "bg": {"position", "size"}}` | `{"png_b64": …}` re-render sin consultar la API |
| `POST` | `/api/zip` | `{"files": [{"filename", "png_b64"}]}` | ZIP binario con las imágenes del cliente |
| `GET` | `/healthz` | — | `{"ok": true}` |

`component` es opcional (por defecto `card`) y debe ser una plantilla existente en `back/components/`.

### Editar una carta generada

Cada carta del resultado tiene un botón **Editar**. El editor (con vista previa en tiempo real) permite cambiar:

- **Nombre, código y cantidad**.
- **Colores** (color de la carta o del degradado del líder).
- **Imagen**: subir otra o restablecer el arte original (recuperado de `.cache/art/`).
- **Posición de la imagen**: zoom (%) y posición horizontal/vertical (%), que se aplican como `background-size` y `background-position` en `.character`.

Al pulsar **Aplicar** la carta se re-renderiza en local vía `/api/render` (sin consultar la API de cartas, por lo que las modificaciones no se pierden) y se actualiza el resultado. El botón **Descargar** de cada carta baja siempre la versión actual, y **Descargar todas (ZIP)** empaqueta las cartas tal cual están en pantalla mediante `/api/zip`, sin regenerar.

> Nota: en Docker, `.cache/` (metadatos, arte y PNG) vive dentro del contenedor de la API, sin volumen: se conserva entre ejecuciones del mismo contenedor pero se pierde al recrearlo. El flujo de edición no depende de él: usa el arte recuperado vía `/api/art` o la imagen que subas.

## Crear o modificar un componente

Los componentes se definen en React (`web/src/cards/`) y se exportan a `back/components/*.html` para que el generador (Python, sin Node) los consuma:

```bash
cd web
npm run build:components   # regenera back/components/card.html, back/components/leader.html, …
npm run dev                # desarrollo: abre http://localhost:5173 (proxy al API en :8080)
```

Cada componente React usa las clases `.name`, `.code`, `.quantity` y `.character` (las que falten se omiten) y puede consumir las variables CSS `--optcg-c1`/`--optcg-c2` (colores de la carta según `card_color`) con fallback para vista previa. El CSS compartido está en `web/src/cards/cards.css`.

Para que la exportación coincida con lo que ves en el navegador, no cambies las dimensiones del `.card` (1826×294 px a ventana de 1948 px). Si cambias el diseño, ajusta en `back/config.py` las constantes `WINDOW_W`, `WINDOW_H`, `PAD_TOP` y `PAD_LEFT`. El `.card` lleva un zoom de 1.05 (`transform: scale(1.05)` desde el centro) y el fondo de la exportación es transparente.