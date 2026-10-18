"""Presencia del jaguar fuera de plano: dos ojos ámbar brillantes entre la vegetación.

Cuando el jaguar debe verse de cuerpo entero, la escena usa la imagen íntegra
`bg_07_jaguar_encounter.png` como fondo. Aquí solo se dibuja su mirada, sólida y nítida,
cuya posición y tamaño crecen con la amenaza. No se usan recortes ni transparencias.
"""
from __future__ import annotations

import math

import pygame

from yulu import config

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT


class JaguarPresence:
    def __init__(self, store=None) -> None:  # `store` se conserva por compatibilidad; ya no se usan sprites
        self.intensity = 0.0  # 0..1 suavizado a partir del nivel de amenaza
        self._blink_timer = 0.0
        self._blink = 0.0

    def update(self, dt: float, threat: int, visible: bool) -> None:
        target = (threat / config.METER_MAX) if visible else 0.0
        self.intensity += (target - self.intensity) * min(1.0, dt * 2.5)
        self._blink_timer -= dt
        if self._blink_timer <= 0:
            self._blink_timer = 4.0 + (threat % 5)
            self._blink = 0.14
        self._blink = max(0.0, self._blink - dt)

    def draw(self, surface: pygame.Surface, time_s: float) -> None:
        if self.intensity < 0.03 or self._blink > 0:
            return
        # La mirada se acerca desde la izquierda y baja ligeramente al crecer la amenaza.
        x = W * (0.14 + 0.18 * self.intensity) + math.sin(time_s * 0.7) * 5
        y = H * (0.58 + 0.05 * self.intensity)
        scale = 0.8 + 1.1 * self.intensity
        self._draw_eyes(surface, x, y, scale, time_s)

    def _draw_eyes(self, surface: pygame.Surface, x: float, y: float, scale: float, t: float) -> None:
        gap = 26 * scale
        pulse = 0.85 + 0.15 * math.sin(t * 3)
        eye_w, eye_h = int(20 * scale), int(10 * scale)
        # Halo aditivo: BLEND_ADD ignora el alfa, así que se oscurece el color en su lugar.
        glow = pygame.Surface((int(160 * scale), int(80 * scale)))
        gw, gh = glow.get_size()
        for i in range(6):
            k = 0.07 * pulse * (i + 1) / 6
            color = tuple(int(c * k) for c in config.JAGUAR_EYE)
            inset = i * 0.12
            pygame.draw.ellipse(glow, color, (gw * inset / 2, gh * inset / 2, gw * (1 - inset), gh * (1 - inset)))
        surface.blit(glow, (x - gw / 2, y - gh / 2), special_flags=pygame.BLEND_ADD)
        for ex in (x - gap / 2, x + gap / 2):
            rect = pygame.Rect(0, 0, eye_w, eye_h)
            rect.center = (int(ex), int(y))
            pygame.draw.ellipse(surface, (40, 20, 0), rect.inflate(4, 4))  # contorno oscuro para que destaque
            pygame.draw.ellipse(surface, config.JAGUAR_EYE, rect)
            pygame.draw.ellipse(surface, (255, 240, 180), rect.inflate(-eye_w // 2, -eye_h // 3))
            pygame.draw.ellipse(surface, (20, 10, 0), pygame.Rect(rect.centerx - max(1, eye_w // 10), rect.top, max(2, eye_w // 5), eye_h))  # pupila vertical
