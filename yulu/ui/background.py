"""Escenarios nocturnos procedurales (sustitutos provisionales de ilustraciones).

Cada clave de `Scene.background` produce capas estáticas generadas con una semilla fija,
más niebla y antorchas animadas. En la FASE 4 estas capas se pueden sustituir por
imágenes locales sin tocar el resto de la interfaz.
"""
from __future__ import annotations

import math
import random

import pygame

from yulu import config

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT


def _lerp(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient(top: tuple, bottom: tuple) -> pygame.Surface:
    surface = pygame.Surface((W, H))
    for y in range(H):
        pygame.draw.line(surface, _lerp(top, bottom, y / H), (0, y), (W, y))
    return surface


def _stars(rng: random.Random, count: int) -> pygame.Surface:
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for _ in range(count):
        x, y = rng.randrange(W), rng.randrange(int(H * 0.55))
        alpha = rng.randint(60, 200)
        pygame.draw.circle(layer, (*config.MOON, alpha), (x, y), rng.choice([1, 1, 1, 2]))
    return layer


def _moon(center: tuple[int, int], radius: int) -> pygame.Surface:
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(radius * 3, radius, -2):
        alpha = int(40 * (1 - (r - radius) / (radius * 2)))
        pygame.draw.circle(layer, (*config.MOON, alpha), center, r)
    pygame.draw.circle(layer, config.MOON, center, radius)
    return layer


def _tree_layer(rng: random.Random, base_y: int, color: tuple, density: int, scale: float) -> pygame.Surface:
    """Siluetas de árboles tropicales: troncos, copas irregulares y lianas."""
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(layer, color, (0, base_y, W, H - base_y))
    for _ in range(density):
        x = rng.randrange(-40, W + 40)
        trunk_w = int(rng.randint(10, 26) * scale)
        height = int(rng.randint(220, 420) * scale)
        top = base_y - height
        pygame.draw.polygon(layer, color, [(x - trunk_w, base_y + 10), (x + trunk_w, base_y + 10),
                                           (x + trunk_w // 2, top), (x - trunk_w // 2, top)])
        for _ in range(rng.randint(4, 8)):
            cx = x + rng.randint(-90, 90) * scale
            cy = top + rng.randint(-40, 60) * scale
            pygame.draw.ellipse(layer, color, (cx - 70 * scale, cy - 35 * scale, 140 * scale, 70 * scale))
        for _ in range(rng.randint(0, 3)):
            lx = x + rng.randint(-60, 60) * scale
            pygame.draw.line(layer, color, (lx, top + 40), (lx + rng.randint(-15, 15), base_y - rng.randint(0, 80)), 2)
    return layer


def _palisade(rng: random.Random, base_y: int) -> pygame.Surface:
    """Empalizada de troncos con techos de palma detrás (borde de la aldea)."""
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    roof_color = (26, 20, 14)
    for i in range(5):
        cx = 200 + i * 230 + rng.randint(-30, 30)
        pygame.draw.polygon(layer, roof_color, [(cx - 120, base_y - 60), (cx + 120, base_y - 60), (cx, base_y - 170)])
    wall_color = (30, 22, 14)
    x = 0
    while x < W:
        w = rng.randint(22, 34)
        h = rng.randint(150, 190)
        pygame.draw.rect(layer, wall_color, (x, base_y - h, w, h + 40))
        pygame.draw.polygon(layer, wall_color, [(x, base_y - h), (x + w, base_y - h), (x + w // 2, base_y - h - 18)])
        x += w + 2
    return layer


class Background:
    """Escenario compuesto por capas estáticas y elementos animados."""

    def __init__(self, key: str) -> None:
        self.key = key
        rng = random.Random(hash(key) & 0xFFFF)
        self._rng = rng
        self.layers: list[pygame.Surface] = []
        self.torches: list[tuple[int, int]] = []
        self._build(key, rng)
        self.fog_layers = [self._fog(rng, 60 + i * 25, 0.25 + i * 0.1) for i in range(3)]
        self.fog_offsets = [0.0, 0.0, 0.0]

    def _build(self, key: str, rng: random.Random) -> None:
        ground = int(H * 0.86)
        if key == "village_edge":
            self.layers.append(_gradient(config.NIGHT_TOP, (24, 20, 30)))
            self.layers.append(_stars(rng, 120))
            self.layers.append(_tree_layer(rng, ground - 120, (6, 14, 16), 14, 0.8))
            self.layers.append(_palisade(rng, ground - 90))
            self.torches = [(140 + i * 250, ground - 265) for i in range(5)]
            self.layers.append(pygame.Surface((W, H), pygame.SRCALPHA))
            pygame.draw.rect(self.layers[-1], (18, 14, 10), (0, ground, W, H - ground))
        elif key == "forest_path":
            self.layers.append(_gradient(config.NIGHT_TOP, config.NIGHT_BOTTOM))
            self.layers.append(_stars(rng, 160))
            self.layers.append(_moon((W - 360, 150), 46))
            self.layers.append(_tree_layer(rng, ground - 150, (8, 24, 28), 16, 0.7))
            self.layers.append(_tree_layer(rng, ground - 60, config.DEEP_GREEN, 10, 1.0))
            path = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.polygon(path, (22, 30, 26), [(W * 0.44, ground - 60), (W * 0.56, ground - 60), (W * 0.85, H), (W * 0.15, H)])
            self.layers.append(path)
            self.layers.append(_tree_layer(rng, ground + 30, config.FOREST_DARK, 6, 1.25))
        else:  # forest_dense
            self.layers.append(_gradient(config.NIGHT_TOP, config.NIGHT_BOTTOM))
            self.layers.append(_stars(rng, 90))
            self.layers.append(_moon((W - 400, 120), 36))
            self.layers.append(_tree_layer(rng, ground - 120, (8, 24, 28), 20, 0.8))
            self.layers.append(_tree_layer(rng, ground - 40, config.DEEP_GREEN, 14, 1.0))
            self.layers.append(_tree_layer(rng, ground + 40, config.FOREST_DARK, 9, 1.3))

    @staticmethod
    def _fog(rng: random.Random, blob_size: int, strength: float) -> pygame.Surface:
        """Bancos de niebla: elipses anchas y tenues, en varias pasadas para suavizar bordes."""
        layer = pygame.Surface((W * 2, H), pygame.SRCALPHA)
        for _ in range(70):
            x = rng.randrange(W * 2)
            y = rng.randrange(int(H * 0.5), H)
            w, h = blob_size * rng.randint(5, 9), blob_size
            for ring in range(4, 0, -1):
                alpha = int(255 * strength * 0.18 * rng.uniform(0.6, 1.0))
                inset = ring * 0.12
                pygame.draw.ellipse(layer, (*config.FOG, alpha), (x + w * inset / 2, y + h * inset / 2, w * (1 - inset), h * (1 - inset)))
        return layer

    def update(self, dt: float) -> None:
        speeds = (8, 14, 22)
        for i in range(3):
            self.fog_offsets[i] = (self.fog_offsets[i] + speeds[i] * dt) % W

    def draw(self, surface: pygame.Surface, time_s: float) -> None:
        for layer in self.layers:
            surface.blit(layer, (0, 0))
        for i, fog in enumerate(self.fog_layers):
            x = -self.fog_offsets[i]
            surface.blit(fog, (x, 0))
            surface.blit(fog, (x + W, 0))
        for tx, ty in self.torches:
            self._draw_torch(surface, tx, ty, time_s)

    @staticmethod
    def _draw_torch(surface: pygame.Surface, x: int, y: int, t: float) -> None:
        flicker = 0.75 + 0.25 * math.sin(t * 13 + x) * math.sin(t * 7.3 + x * 0.5)
        # Halo aditivo: BLEND_ADD ignora el alfa, así que se oscurece el color en su lugar.
        glow = pygame.Surface((300, 300))
        for r in range(140, 10, -10):
            k = 0.09 * flicker * (1 - r / 140)
            pygame.draw.circle(glow, tuple(int(c * k) for c in config.AMBER), (150, 150), r)
        surface.blit(glow, (x - 150, y - 150), special_flags=pygame.BLEND_ADD)
        pygame.draw.rect(surface, (40, 26, 14), (x - 3, y, 6, 50))
        flame_h = int(22 * flicker)
        pygame.draw.polygon(surface, config.FIRE, [(x - 8, y + 4), (x + 8, y + 4), (x, y - flame_h)])
        pygame.draw.polygon(surface, config.AMBER, [(x - 4, y + 2), (x + 4, y + 2), (x, y - flame_h // 2)])
