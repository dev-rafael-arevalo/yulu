"""Presencia del jaguar: sprites si existen, primitivas provisionales si no.

La visibilidad crece con la amenaza: primero solo los ojos entre la vegetación, después la
figura completa acechando desde la izquierda del encuadre.
"""
from __future__ import annotations

import math

import pygame

from yulu import config
from yulu.ui.assets import ImageStore

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
SILHOUETTE_THRESHOLD = 0.35


class JaguarPresence:
    def __init__(self, store: ImageStore | None = None) -> None:
        self.intensity = 0.0  # 0..1 suavizado a partir del nivel de amenaza
        self._blink_timer = 0.0
        self._blink = 0.0
        self._store = store
        self._sprite_cache: dict[tuple[str, int], pygame.Surface] = {}

    def update(self, dt: float, threat: int, visible: bool) -> None:
        target = (threat / config.METER_MAX) if visible else 0.0
        self.intensity += (target - self.intensity) * min(1.0, dt * 1.5)
        self._blink_timer -= dt
        if self._blink_timer <= 0:
            self._blink_timer = 3.0 + (threat % 5)
            self._blink = 0.18
        self._blink = max(0.0, self._blink - dt)

    def draw(self, surface: pygame.Surface, time_s: float) -> None:
        if self.intensity < 0.02:
            return
        # El jaguar se acerca desde la izquierda del encuadre a medida que sube la amenaza.
        base_x = int(W * (0.12 + 0.20 * self.intensity))
        base_y = int(H * (0.62 + 0.06 * self.intensity))
        scale = 0.6 + 1.2 * self.intensity
        sway = math.sin(time_s * 0.8) * 6 * scale

        if self._draw_sprites(surface, base_x + sway, base_y, scale):
            return
        if self.intensity > SILHOUETTE_THRESHOLD:
            self._draw_silhouette(surface, base_x + sway, base_y, scale, (self.intensity - SILHOUETTE_THRESHOLD) / (1 - SILHOUETTE_THRESHOLD))
        if self._blink <= 0:
            self._draw_eyes(surface, base_x + sway, base_y - 36 * scale, scale, time_s)

    # ---------- sprites ----------
    def _sprite(self, pose: str, width: int) -> pygame.Surface | None:
        if self._store is None:
            return None
        key = (pose, width)
        if key not in self._sprite_cache:
            raw = self._store.jaguar(pose)
            if raw is None:
                return None
            ratio = raw.get_height() / raw.get_width()
            self._sprite_cache[key] = pygame.transform.smoothscale(raw, (width, max(1, int(width * ratio))))
        return self._sprite_cache[key]

    def _draw_sprites(self, surface: pygame.Surface, x: float, y: float, scale: float) -> bool:
        """Dibuja con sprites. Devuelve False si no hay sprites disponibles."""
        pose = "stalk" if self.intensity > SILHOUETTE_THRESHOLD else "eyes"
        width = int((430 if pose == "stalk" else 260) * scale)
        sprite = self._sprite(pose, max(40, width // 8 * 8))
        if sprite is None:
            return False
        if pose == "eyes":
            alpha = min(1.0, self.intensity * 1.8)
        else:  # aparece entre la niebla y se vuelve sólido rápidamente al crecer la amenaza
            alpha = min(1.0, 0.45 + (self.intensity - SILHOUETTE_THRESHOLD) / (1 - SILHOUETTE_THRESHOLD) * 1.2)
        if self._blink > 0 and pose == "eyes":
            alpha *= 0.1
        sprite.set_alpha(int(255 * alpha))
        surface.blit(sprite, (x - sprite.get_width() * 0.3, y - sprite.get_height() * 0.55))
        return True

    # ---------- primitivas provisionales ----------
    def _draw_eyes(self, surface: pygame.Surface, x: float, y: float, scale: float, t: float) -> None:
        gap = 22 * scale
        pulse = 0.8 + 0.2 * math.sin(t * 3)
        alpha = int(255 * min(1.0, self.intensity * 1.6) * pulse)
        eye_w, eye_h = int(18 * scale), int(9 * scale)
        # Halo aditivo: BLEND_ADD ignora el alfa, así que se oscurece el color en su lugar.
        glow = pygame.Surface((int(140 * scale), int(70 * scale)))
        gw, gh = glow.get_size()
        for i in range(6):
            k = (alpha / 255) * 0.05 * (i + 1) / 6
            color = tuple(int(c * k) for c in config.JAGUAR_EYE)
            inset = i * 0.12
            pygame.draw.ellipse(glow, color, (gw * inset / 2, gh * inset / 2, gw * (1 - inset), gh * (1 - inset)))
        surface.blit(glow, (x - gw / 2, y - gh / 2), special_flags=pygame.BLEND_ADD)
        for ex in (x - gap / 2, x + gap / 2):
            eye = pygame.Surface((eye_w, eye_h), pygame.SRCALPHA)
            pygame.draw.ellipse(eye, (*config.JAGUAR_EYE, alpha), eye.get_rect())
            pygame.draw.ellipse(eye, (20, 10, 0, alpha), (eye_w * 0.4, 0, eye_w * 0.2, eye_h))
            surface.blit(eye, (ex - eye_w / 2, y - eye_h / 2))

    @staticmethod
    def _draw_silhouette(surface: pygame.Surface, x: float, y: float, scale: float, strength: float) -> None:
        alpha = int(170 * strength)
        color = (2, 4, 6, alpha)
        body = pygame.Surface((int(260 * scale), int(140 * scale)), pygame.SRCALPHA)
        w, h = body.get_size()
        pygame.draw.ellipse(body, color, (w * 0.18, h * 0.35, w * 0.7, h * 0.45))  # cuerpo
        pygame.draw.circle(body, color, (int(w * 0.2), int(h * 0.42)), int(h * 0.22))  # cabeza
        pygame.draw.polygon(body, color, [(w * 0.1, h * 0.25), (w * 0.17, h * 0.1), (w * 0.2, h * 0.28)])  # oreja
        pygame.draw.polygon(body, color, [(w * 0.22, h * 0.25), (w * 0.28, h * 0.1), (w * 0.3, h * 0.28)])
        for lx in (0.3, 0.42, 0.68, 0.8):  # patas
            pygame.draw.rect(body, color, (w * lx, h * 0.65, w * 0.07, h * 0.35))
        pygame.draw.lines(body, color, False, [(w * 0.86, h * 0.5), (w * 0.95, h * 0.3), (w * 0.99, h * 0.45)], int(8 * scale))
        surface.blit(body, (x - w * 0.2, y - h * 0.42))
