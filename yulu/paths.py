"""Resolución de rutas independiente del directorio desde el que se ejecuta el juego."""
from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
ASSETS_DIR = PACKAGE_ROOT / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
AUDIO_DIR = ASSETS_DIR / "audio"
FONTS_DIR = ASSETS_DIR / "fonts"
LANGUAGE_DATA_DIR = PACKAGE_ROOT / "language" / "data"


def asset_path(*parts: str) -> Path:
    """Devuelve la ruta absoluta de un recurso dentro de `yulu/assets`."""
    return ASSETS_DIR.joinpath(*parts)
