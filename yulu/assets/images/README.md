# Imágenes del juego

Todas las imágenes de esta carpeta fueron generadas con ChatGPT ImageGen (OpenAI) el 18 de
octubre de 2026 por el autor del proyecto, a partir de los prompts de `docs/ART_PROMPTS.md`,
y se usan según las condiciones de OpenAI para contenido generado. Son arte conceptual, no
reconstrucciones históricas.

| Archivos | Origen |
|---|---|
| `bg_03` a `bg_06`, `fx_fog_layer_*`, `fx_torch_smoke` | Cuadrícula de recursos, cortada con `tools/slice_asset_grid.py` |
| `bg_07` a `bg_10` | Imágenes íntegras a resolución completa |
| `cast/*.png` | Paquete de personajes y jaguar sobre fondo negro, convertidos a transparencia con `tools/prepare_cutouts.py` |

Las claves que usa el juego están en `../manifest.json`. Comprueba que no falte nada con
`python tools/check_assets.py`.
