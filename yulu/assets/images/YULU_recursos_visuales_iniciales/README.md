# YULU — paquete inicial de fondos

Contenido en `yulu/assets/images/`:
- `bg_01_forest_awakening.png`
- `bg_02_forest_chase.png`
- `bg_03_path_to_village.png`
- `bg_04_village_gate_torches.png`
- `bg_05_shelter_interior.png`
- `bg_06_dawn_clearing.png`
- `asset_sheet_reference.png` (referencia visual; no usar como fondo)
- `CREDITS.md`

Los seis fondos PNG están en 1920 × 1080. Se han recortado de una hoja de conceptos para esta primera entrega, por lo que son prototipos de fondos y pueden necesitar retoques de encuadre. La hoja incluye una vista de conceptos para jaguar y niebla, pero esos elementos NO están extraídos como PNG con alfa real.

## Integración
Copia la carpeta `yulu/assets/` a la raíz de tu proyecto conservando las rutas. Compara las claves de `manifest.json` con el manifiesto actual del juego antes de sobrescribirlo; si tu manifiesto existente tiene más campos, conserva esos campos y agrega/actualiza solo las rutas de imagen.
