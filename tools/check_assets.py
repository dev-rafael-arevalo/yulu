"""Comprueba qué recursos gráficos declarados en el manifiesto existen en disco.

Uso:  python tools/check_assets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yulu.paths import IMAGES_DIR  # noqa: E402
from yulu.ui.assets import load_manifest  # noqa: E402


def main() -> int:
    manifest = load_manifest()
    expected: list[tuple[str, str]] = []
    for key, spec in manifest.get("backgrounds", {}).items():
        expected.append((f"fondo:{key}", spec.get("file", "")))
    for scene_id, items in manifest.get("cast", {}).items():
        for item in items:
            expected.append((f"reparto:{scene_id}", item["file"]))
    overlays = manifest.get("overlays", {})
    for filename in overlays.get("fog", []):
        expected.append(("niebla", filename))
    if overlays.get("smoke"):
        expected.append(("humo", overlays["smoke"]))

    missing = 0
    print(f"Directorio de imágenes: {IMAGES_DIR}\n")
    for label, filename in expected:
        present = (IMAGES_DIR / filename).is_file()
        missing += 0 if present else 1
        print(f"  [{'OK' if present else '--'}] {label:<22} {filename}")
    print(f"\n{len(expected) - missing}/{len(expected)} recursos presentes.")
    if missing:
        print("Los recursos ausentes se sustituyen por escenarios procedurales provisionales.")
        print("Consulta docs/ART_PROMPTS.md para generarlos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
