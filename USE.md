# cartas-ui — Exportación de cartas

Genera un PNG por cada carta del texto `NxCODIGO` renderizando un componente de `components/`, consultando el nombre y la imagen de cada carta a la API de One Piece TCG (`API_CARD`).

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
   python3 export_cards.py --component card
   ```

3. Por cada línea, el script consulta la API, descarga la imagen a `.cache/` y exporta la carta a `exports/<codigo>.png` (tamaño 1948×367 px, fondo transparente).

4. Si algún código falla, se anota en `errors.txt` (código + motivo) y el proceso continúa con el resto. Al terminar se muestra un resumen.

## Uso (web con Docker)

```bash
docker compose up -d --build
```

Abre `http://localhost:8080`. En la primera pantalla elige un componente (con vista previa); después pega el texto o sube un `.txt` y genera las cartas (individual o ZIP).

### Endpoints

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| `GET` | `/api/components` | — | `{"components": ["card", "leader"]}` |
| `POST` | `/api/generate` | `{"text": "4xOP15-014", "component": "card"}` | JSON con `cards` (PNG en base64) y `errors` |
| `POST` | `/api/generate/zip` | igual que `generate` | ZIP binario con los PNG |
| `GET` | `/healthz` | — | `{"ok": true}` |

`component` es opcional (por defecto `card`) y debe ser una plantilla existente en `components/`.

## Crear un componente

Cada `components/*.html` es una plantilla independiente. Para que la carta se rellene automáticamente, el componente debe usar estas clases (las que falten se omiten):

- **Nombre** → `.name`
- **Número de serie** → `.code` (opcional)
- **Cantidad** → `.quantity` (opcional, se muestra como `xN`)
- **Imagen del personaje** → `.character` (el generador la pone como `background-image`)

Para que la exportación coincida con lo que ves en el navegador, no cambies las dimensiones del `.card` (1826×294 px a ventana de 1948 px). Si cambias el diseño, ajusta en `generator.py` las constantes `WINDOW_W`, `WINDOW_H`, `PAD_TOP` y `PAD_LEFT`. El `.card` lleva un zoom de 1.05 (`transform: scale(1.05)` desde el centro) y el fondo de la exportación es transparente.