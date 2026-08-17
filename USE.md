# cartas-ui — Exportación de cartas

Genera un PNG por cada carta de `generate.txt` renderizando el componente de `index.html`, consultando el nombre y la imagen de cada carta a la API de One Piece TCG (`API_CARD`).

## Requisitos

- Python 3
- Google Chrome (para la captura headless)

## Configuración

Crea un `.env` con la API que, concatenando el código de carta, devuelve su información:

```
API_CARD=https://www.optcgapi.com/api/sets/card/
```

Ejemplo de petición: `GET https://www.optcgapi.com/api/sets/card/OP15-002` → JSON con `card_name`, `card_set_id` y `card_image`.

## Uso

1. Rellena `generate.txt` con una línea por carta, formato `<cantidad>x<codigo>`:

   ```
   1xOP15-002
   4xOP15-014
   2xOP05-019
   ```

2. Ejecuta:

   ```bash
   python3 export_cards.py
   ```

3. Por cada línea, el script consulta la API, descarga la imagen a `.cache/` y exporta la carta a `exports/<codigo>.png` (tamaño 1948×367 px, fondo transparente).

4. Si algún código falla, se anota en `errors.txt` (código + motivo) y el proceso continúa con el resto. Al terminar se muestra un resumen.

## Editar el componente

El diseño se edita en `index.html`:

- **Nombre** → `.name`
- **Número de serie** → `.code`
- **Cantidad** → `.quantity` (se muestra como `xN`)
- **Imagen del personaje** → `.character` (fondo con `background-image`; `background-size: 110% auto` = zoom centrado)

Para que la exportación coincida con lo que ves en el navegador, no cambies las dimensiones del `.card` (1826×294 px a ventana de 1948 px). Si cambias el diseño, ajusta en `export_cards.py` las constantes `WINDOW_W`, `WINDOW_H`, `PAD_TOP` y `PAD_LEFT`. El `.card` lleva un zoom de 1.05 (`transform: scale(1.05)` desde el centro) y el fondo de la exportación es transparente.
