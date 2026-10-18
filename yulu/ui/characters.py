"""Personajes en pantalla: retrato del locutor actual y grupos de pobladores por escena.

Los retratos y grupos se declaran en `assets/manifest.json` (sección "characters") y se
dibujan sobre el fondo, con fundidos, sin reemplazarlo. Solo aparecen donde la narrativa
lo exige: el retrato cuando ese personaje habla y los grupos en las escenas listadas.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from yulu import config
from yulu.ui.assets import ImageStore

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
PORTRAIT_HEIGHT = int(H * 0.56)
PORTRAIT_BOTTOM = H - 230 + 24  # apoya sobre la caja de diálogo
FADE_SPEED = 3.0  # unidades de alfa (0-1) por segundo


@dataclass
class _Placed:
    surface: pygame.Surface
    x: int
    y: int
    alpha_max: float
    alpha: float = 0.0
    target: float = 1.0


class CharacterLayer:
    def __init__(self, store: ImageStore) -> None:
        self.store = store
        spec = store.manifest.get("characters", {})
        self._portrait_files: dict[str, str] = spec.get("portraits", {})
        self._scene_specs: dict[str, list[dict]] = spec.get("scenes", {})
        self._cache: dict[tuple[str, int], pygame.Surface] = {}
        self._portrait: _Placed | None = None
        self._portrait_name: str | None = None
        self._groups: list[_Placed] = []

    # ---------- carga ----------
    def _scaled(self, filename: str, height: int) -> pygame.Surface | None:
        key = (filename, height)
        if key not in self._cache:
            raw = self.store.character(filename)
            if raw is None:
                return None
            ratio = raw.get_width() / raw.get_height()
            self._cache[key] = pygame.transform.smoothscale(raw, (max(1, int(height * ratio)), height))
        return self._cache[key]

    # ---------- estado ----------
    def set_scene(self, scene_id: str) -> None:
        for group in self._groups:
            group.target = 0.0
        for spec in self._scene_specs.get(scene_id, []):
            surface = self._scaled(spec["file"], int(spec.get("height", 0.4) * H))
            if surface is None:
                continue
            x = int(spec.get("x", 0.05) * W)
            y = int(spec.get("bottom", 0.7) * H) - surface.get_height()
            self._groups.append(_Placed(surface, x, y, float(spec.get("alpha", 0.9))))
        self.set_speaker(None)

    def set_speaker(self, speaker: str | None) -> None:
        filename = self._portrait_files.get(speaker or "")
        if filename is None:
            if self._portrait is not None:
                self._portrait.target = 0.0
            self._portrait_name = None
            return
        if speaker == self._portrait_name and self._portrait is not None:
            self._portrait.target = 1.0
            return
        surface = self._scaled(filename, PORTRAIT_HEIGHT)
        if surface is None:
            return
        x = W - surface.get_width() - 70
        y = PORTRAIT_BOTTOM - surface.get_height()
        self._portrait = _Placed(surface, x, y, 1.0)
        self._portrait_name = speaker

    def update(self, dt: float) -> None:
        for placed in [*self._groups, *([self._portrait] if self._portrait else [])]:
            step = FADE_SPEED * dt
            placed.alpha = min(placed.target, placed.alpha + step) if placed.alpha < placed.target else max(placed.target, placed.alpha - step)
        self._groups = [g for g in self._groups if not (g.target <= 0 and g.alpha <= 0)]
        if self._portrait is not None and self._portrait.target <= 0 and self._portrait.alpha <= 0:
            self._portrait = None

    def draw(self, surface: pygame.Surface) -> None:
        for group in self._groups:
            self._blit(surface, group)
        if self._portrait is not None:
            self._blit(surface, self._portrait)

    @staticmethod
    def _blit(surface: pygame.Surface, placed: _Placed) -> None:
        if placed.alpha <= 0:
            return
        placed.surface.set_alpha(int(255 * placed.alpha * placed.alpha_max))
        surface.blit(placed.surface, (placed.x, placed.y))

    @property
    def visible_portrait(self) -> str | None:
        return self._portrait_name if self._portrait and self._portrait.alpha > 0 else None
