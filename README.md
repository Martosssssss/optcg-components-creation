# cartas-ui

Genera un PNG por cada carta de One Piece TCG renderizando el componente de `index.html` a partir de una lista de códigos (`generate.txt`) y de la API de One Piece TCG.

## Características

- Lee `generate.txt` con el formato `<cantidad>x<codigo>` (ej: `4xOP15-014`).
- Consulta el nombre e imagen de cada carta a la API definida en `API_CARD` (`.env`).
- Descarga las imágenes a `.cache/` (se reutilizan entre ejecuciones).
- Exporta cada carta a `exports/<codigo>.png` (1948×367 px, fondo transparente).
- Si algún código falla, lo anota en `errors.txt` y continúa con el resto.

## Requisitos

- Python 3
- Google Chrome (para la captura headless)

## Configuración

Crea un archivo `.env` con la API que, concatenando el código de carta, devuelve su información:

```
API_CARD=https://www.optcgapi.com/api/sets/card/
```

## Uso

1. Rellena `generate.txt` con una línea por carta (ver `generate.example.txt`):

   ```
   1xOP15-002
   4xOP15-014
   2xOP05-019
   ```

2. Ejecuta:

   ```bash
   python3 export_cards.py
   ```

3. El resultado se guarda en `exports/<codigo>.png`.

## Despliegue en Vercel

El proyecto se puede desplegar gratis en Vercel (plan Hobby): el frontend es estático y el resto corre en Serverless Functions de Python. Nota: las funciones de Vercel no pueden ejecutar Chrome headless, por lo que el render y la exportación de PNG se realizan en el navegador del usuario.

```bash
npm i -g vercel
vercel
vercel --prod
```

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `index.html` | Componente visual de la carta (se rellena automáticamente por cada carta) |
| `export_cards.py` | Script de exportación (lee `generate.txt`, consulta la API y genera los PNG) |
| `generate.txt` | Lista de cartas a exportar |
| `.env` | Variable `API_CARD` con la URL base de la API |
| `.cache/` | Imágenes descargadas de la API |
| `exports/` | PNG generados |
| `errors.txt` | Códigos que fallaron durante la exportación |

## Editar el componente

El diseño se edita en `index.html`:

- **Nombre** → `.name`
- **Número de serie** → `.code`
- **Cantidad** → `.quantity` (se muestra como `xN`)
- **Imagen del personaje** → `.character img` (se rellena automáticamente con cada carta)

Para que la exportación coincida con lo que ves en el navegador, no cambies las dimensiones del `.card` (1826×294 px a ventana de 1948 px). Si cambias el diseño, ajusta en `export_cards.py` las constantes `WINDOW_W`, `WINDOW_H`, `PAD_TOP` y `PAD_LEFT`. El `.card` lleva un zoom de 1.05 (`transform: scale(1.05)` desde el centro) y el fondo de la exportación es transparente.