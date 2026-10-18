"""Carga de imágenes locales declaradas en `assets/manifest.json`.

Toda carga es tolerante a fallos: si un archivo no existe o está dañado se registra una
advertencia una sola vez y se devuelve None, de modo que la presentación recurra al
escenario procedural provisional sin interrumpir la partida.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pygame

from yulu import config
from yulu.paths import ASSETS_DIR, IMAGES_DIR

log = logging.getLogger("yulu.assets")
W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
MANIFEST_PATH = ASSETS_DIR / "manifest.json"


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("No se pudo leer el manifiesto %s: %s", path, exc)
        return {"backgrounds": {}, "jaguar": {}, "overlays": {}}


def cover_fit(image: pygame.Surface, width: int = W, height: int = H, overscan: float = 1.0) -> pygame.Surface:
    """Escala la imagen para cubrir el área 16:9 conservando proporciones y recorta el sobrante."""
    iw, ih = image.get_size()
    scale = max(width / iw, height / ih) * overscan
    scaled = pygame.transform.smoothscale(image, (max(1, round(iw * scale)), max(1, round(ih * scale))))
    target_w, target_h = round(width * overscan), round(height * overscan)
    x = (scaled.get_width() - target_w) // 2
    y = (scaled.get_height() - target_h) // 2
    return scaled.subsurface(pygame.Rect(x, y, target_w, target_h)).copy()


class ImageStore:
    """Caché de superficies. Una instancia por partida."""

    def __init__(self, manifest: dict | None = None, images_dir: Path = IMAGES_DIR) -> None:
        self.manifest = manifest if manifest is not None else load_manifest()
        self.images_dir = images_dir
        self._cache: dict[str, pygame.Surface | None] = {}
        self._warned: set[str] = set()

    # ---------- carga básica ----------
    def _load(self, filename: str, alpha: bool) -> pygame.Surface | None:
        key = f"{filename}|{alpha}"
        if key in self._cache:
            return self._cache[key]
        path = self.images_dir / filename
        surface: pygame.Surface | None = None
        if path.is_file():
            try:
                loaded = pygame.image.load(str(path))
                surface = loaded.convert_alpha() if alpha else loaded.convert()
            except pygame.error as exc:
                self._warn(filename, f"archivo dañado ({exc})")
        else:
            self._warn(filename, "no encontrado; se usa sustituto provisional")
        self._cache[key] = surface
        return surface

    def _warn(self, filename: str, reason: str) -> None:
        if filename not in self._warned:
            self._warned.add(filename)
            log.warning("Imagen %s: %s", filename, reason)

    # ---------- consultas de alto nivel ----------
    def background_spec(self, key: str) -> dict:
        return self.manifest.get("backgrounds", {}).get(key, {})

    def background(self, key: str, overscan: float = 1.06) -> pygame.Surface | None:
        """Fondo ajustado a pantalla con un pequeño sobrante para el movimiento de cámara."""
        spec = self.background_spec(key)
        filename = spec.get("file")
        if not filename:
            return None
        cache_key = f"bg:{key}:{overscan}"
        if cache_key not in self._cache:
            raw = self._load(filename, alpha=False)
            self._cache[cache_key] = cover_fit(raw, overscan=overscan) if raw else None
        return self._cache[cache_key]

    def jaguar(self, pose: str) -> pygame.Surface | None:
        filename = self.manifest.get("jaguar", {}).get(pose)
        return self._load(filename, alpha=True) if filename else None

    def character(self, filename: str) -> pygame.Surface | None:
        sub = self.manifest.get("characters", {}).get("dir", "characters")
        return self._load(f"{sub}/{filename}", alpha=True)

    def fog_layers(self) -> list[pygame.Surface]:
        files = self.manifest.get("overlays", {}).get("fog", [])
        layers = [self._load(f, alpha=True) for f in files]
        return [cover_fit(s, width=W * 2, height=H) for s in layers if s is not None]

    def smoke(self) -> pygame.Surface | None:
        filename = self.manifest.get("overlays", {}).get("smoke")
        return self._load(filename, alpha=True) if filename else None

    # ---------- diagnóstico ----------
    def expected_files(self) -> list[str]:
        files: list[str] = [spec["file"] for spec in self.manifest.get("backgrounds", {}).values() if "file" in spec]
        files += list(self.manifest.get("jaguar", {}).values())
        overlays = self.manifest.get("overlays", {})
        files += overlays.get("fog", [])
        if overlays.get("smoke"):
            files.append(overlays["smoke"])
        characters = self.manifest.get("characters", {})
        sub = characters.get("dir", "characters")
        names = set(characters.get("portraits", {}).values())
        for specs in characters.get("scenes", {}).values():
            names.update(spec["file"] for spec in specs)
        files += [f"{sub}/{name}" for name in sorted(names)]
        return files

    def missing_files(self) -> list[str]:
        return [f for f in self.expected_files() if not (self.images_dir / f).is_file()]
