"""Fundidos a negro entre escenas y viñeta de oscuridad."""
from __future__ import annotations

import pygame

from yulu import config

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT


class Fade:
    """Fundido de salida seguido de fundido de entrada. `on_midpoint` se ejecuta en negro total."""

    def __init__(self, duration: float = 0.6) -> None:
        self.duration = duration
        self._t = 0.0
        self.active = False
        self._on_midpoint = None
        self._midpoint_done = False
        self._overlay = pygame.Surface((W, H))
        self._overlay.fill((0, 0, 0))

    def start(self, on_midpoint=None) -> None:
        self.active = True
        self._t = 0.0
        self._on_midpoint = on_midpoint
        self._midpoint_done = False

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self._t += dt
        if not self._midpoint_done and self._t >= self.duration / 2:
            self._midpoint_done = True
            if self._on_midpoint:
                self._on_midpoint()
        if self._t >= self.duration:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        half = self.duration / 2
        alpha = self._t / half if self._t < half else 1 - (self._t - half) / half
        self._overlay.set_alpha(int(255 * max(0.0, min(1.0, alpha))))
        surface.blit(self._overlay, (0, 0))


def make_vignette(strength: int = 160) -> pygame.Surface:
    """Oscurece los bordes para reforzar la sensación de noche. Se genera una sola vez."""
    # pygame.draw sobre una superficie SRCALPHA reemplaza el alfa en lugar de acumularlo,
    # así que cada elipse interior sobrescribe a la anterior con menos oscuridad.
    vignette = pygame.Surface((W, H), pygame.SRCALPHA)
    vignette.fill((0, 0, 0, strength))
    cx, cy = W // 2, H // 2
    steps = 40
    for i in range(steps):
        t = i / steps  # 0 = borde exterior, 1 = centro
        alpha = int(strength * (1 - t) ** 2)
        rw, rh = int(W * (1.7 - 1.1 * t)), int(H * (1.9 - 1.3 * t))
        pygame.draw.ellipse(vignette, (0, 0, 0, alpha), (cx - rw // 2, cy - rh // 2, rw, rh))
    return vignette
