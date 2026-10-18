"""Escenarios: imagen local si existe en el manifiesto, sustituto procedural si no.

Con imagen: ajuste a 16:9, deriva lenta de cámara, niebla en paralaje y humo de antorchas.
Sin imagen: capas generadas con una semilla fija y la marca `is_provisional = True`,
que la aplicación muestra en pantalla.
"""
from __future__ import annotations

import math
import random

import pygame

from yulu import config
from yulu.ui.assets import ImageStore

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
OVERSCAN = 1.06


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
        pygame.draw.circle(layer, (*config.MOON, rng.randint(60, 200)), (x, y), rng.choice([1, 1, 1, 2]))
    return layer


def _moon(center: tuple[int, int], radius: int) -> pygame.Surface:
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(radius * 3, radius, -2):
        alpha = int(40 * (1 - (r - radius) / (radius * 2)))
        pygame.draw.circle(layer, (*config.MOON, alpha), center, r)
    pygame.draw.circle(layer, config.MOON, center, radius)
    return layer


def _tree_layer(rng: random.Random, base_y: int, color: tuple, density: int, scale: float) -> pygame.Surface:
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(layer, color, (0, base_y, W, H - base_y))
    for _ in range(density):
        x = rng.randrange(-40, W + 40)
        trunk_w = int(rng.randint(10, 26) * scale)
        height = int(rng.randint(220, 420) * scale)
        top = base_y - height
        pygame.draw.polygon(layer, color, [(x - trunk_w, base_y + 10), (x + trunk_w, base_y + 10), (x + trunk_w // 2, top), (x - trunk_w // 2, top)])
        for _ in range(rng.randint(4, 8)):
            cx = x + rng.randint(-90, 90) * scale
            cy = top + rng.randint(-40, 60) * scale
            pygame.draw.ellipse(layer, color, (cx - 70 * scale, cy - 35 * scale, 140 * scale, 70 * scale))
    return layer


def _palisade(rng: random.Random, base_y: int) -> pygame.Surface:
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


def _interior(rng: random.Random) -> list[pygame.Surface]:
    """Refugio provisional: paredes de caña, techo oscuro y resplandor central de hoguera."""
    layers = [_gradient((14, 9, 5), (30, 18, 8))]
    walls = pygame.Surface((W, H), pygame.SRCALPHA)
    for x in range(0, W, 14):
        pygame.draw.line(walls, (40, 26, 12, 120), (x, int(H * 0.2)), (x + rng.randint(-3, 3), int(H * 0.8)), rng.randint(3, 6))
    pygame.draw.polygon(walls, (8, 5, 3), [(0, 0), (W, 0), (W, int(H * 0.22)), (W // 2, int(H * 0.08)), (0, int(H * 0.22))])
    layers.append(walls)
    return layers


def _fog_layer(rng: random.Random, blob_size: int, strength: float) -> pygame.Surface:
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


class Background:
    """Escenario compuesto por una imagen (o capas provisionales) más niebla y antorchas."""

    def __init__(self, key: str, store: ImageStore | None = None) -> None:
        self.key = key
        self.store = store
        rng = random.Random(hash(key) & 0xFFFF)
        self.image: pygame.Surface | None = store.background(key, OVERSCAN) if store else None
        self.is_provisional = self.image is None
        spec = store.background_spec(key) if store else {}
        self.fog_strength = float(spec.get("fog", 1.0))
        self.warmth = float(spec.get("warmth", 0.0))
        self.layers: list[pygame.Surface] = []
        self.torches: list[tuple[int, int]] = []
        self.fire: tuple[int, int] | None = None
        if self.is_provisional:
            self._build_placeholder(key, rng)
        else:
            # Posiciones normalizadas del manifiesto para el resplandor animado sobre la imagen.
            self.torches = [(int(tx * W), int(ty * H)) for tx, ty in spec.get("torches", [])]
            if spec.get("fire"):
                self.fire = (int(spec["fire"][0] * W), int(spec["fire"][1] * H))
        image_fog = store.fog_layers() if store else []
        self.fog_layers = image_fog or [_fog_layer(rng, 60 + i * 25, 0.25 + i * 0.1) for i in range(3)]
        self.fog_offsets = [0.0] * len(self.fog_layers)
        self.smoke = store.smoke() if store else None
        self._tint = pygame.Surface((W, H), pygame.SRCALPHA)

    # ---------- sustitutos provisionales ----------
    def _build_placeholder(self, key: str, rng: random.Random) -> None:
        ground = int(H * 0.86)
        if key in ("village_edge", "village_gate"):
            close = key == "village_gate"
            self.layers.append(_gradient(config.NIGHT_TOP, (24, 20, 30)))
            self.layers.append(_stars(rng, 120))
            self.layers.append(_tree_layer(rng, ground - 120, (6, 14, 16), 14, 0.8))
            self.layers.append(_palisade(rng, ground - (40 if close else 90)))
            ty = ground - (215 if close else 265)
            self.torches = [(W // 2 - 140, ty), (W // 2 + 140, ty)] if close else [(140 + i * 250, ty) for i in range(5)]
        elif key == "shelter":
            self.layers.extend(_interior(rng))
            self.fire = (W // 2, int(H * 0.6))
            self.fog_strength = 0.15
        elif key == "dawn":
            self.layers.append(_gradient((40, 36, 90), (235, 140, 70)))
            self.layers.append(_tree_layer(rng, ground - 120, (30, 24, 40), 14, 0.8))
            self.layers.append(_tree_layer(rng, ground - 40, (18, 20, 30), 10, 1.0))
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
        else:  # forest_dense y cualquier clave desconocida
            self.layers.append(_gradient(config.NIGHT_TOP, config.NIGHT_BOTTOM))
            self.layers.append(_stars(rng, 90))
            self.layers.append(_moon((W - 400, 120), 36))
            self.layers.append(_tree_layer(rng, ground - 120, (8, 24, 28), 20, 0.8))
            self.layers.append(_tree_layer(rng, ground - 40, config.DEEP_GREEN, 14, 1.0))
            self.layers.append(_tree_layer(rng, ground + 40, config.FOREST_DARK, 9, 1.3))

    # ---------- animación ----------
    def update(self, dt: float) -> None:
        speeds = (8, 14, 22)
        for i in range(len(self.fog_layers)):
            self.fog_offsets[i] = (self.fog_offsets[i] + speeds[i % 3] * dt) % W

    def draw(self, surface: pygame.Surface, time_s: float) -> None:
        if self.image is not None:
            self._draw_image_with_drift(surface, time_s)
        else:
            for layer in self.layers:
                surface.blit(layer, (0, 0))
        if self.fire:
            self._draw_fire(surface, *self.fire, time_s)
        for i, fog in enumerate(self.fog_layers):
            fog.set_alpha(int(255 * min(1.0, self.fog_strength)))
            x = -self.fog_offsets[i]
            surface.blit(fog, (x, 0))
            surface.blit(fog, (x + W, 0))
        for tx, ty in self.torches:
            self._draw_torch(surface, tx, ty, time_s)
        if self.warmth > 0:
            self._tint.fill((255, 150, 60, int(28 * self.warmth)))
            surface.blit(self._tint, (0, 0))

    def _draw_image_with_drift(self, surface: pygame.Surface, t: float) -> None:
        """Deriva lenta de cámara (efecto Ken Burns) sobre la imagen con sobrante."""
        assert self.image is not None
        extra_w = self.image.get_width() - W
        extra_h = self.image.get_height() - H
        x = -extra_w / 2 + math.sin(t * 0.045) * extra_w / 2
        y = -extra_h / 2 + math.cos(t * 0.031) * extra_h / 2
        surface.blit(self.image, (int(x), int(y)))

    def _draw_torch(self, surface: pygame.Surface, x: int, y: int, t: float) -> None:
        flicker = 0.75 + 0.25 * math.sin(t * 13 + x) * math.sin(t * 7.3 + x * 0.5)
        # Halo aditivo: BLEND_ADD ignora el alfa, así que se oscurece el color en su lugar.
        glow = pygame.Surface((300, 300))
        for r in range(140, 10, -10):
            k = 0.09 * flicker * (1 - r / 140)
            pygame.draw.circle(glow, tuple(int(c * k) for c in config.AMBER), (150, 150), r)
        surface.blit(glow, (x - 150, y - 150), special_flags=pygame.BLEND_ADD)
        if self.smoke is not None:
            drift = (t * 18 + x) % 60
            smoke = pygame.transform.smoothscale(self.smoke, (90, 180))
            smoke.set_alpha(90)
            surface.blit(smoke, (x - 45 + math.sin(t + x) * 8, y - 190 - drift))
        if self.is_provisional:
            pygame.draw.rect(surface, (40, 26, 14), (x - 3, y, 6, 50))
            flame_h = int(22 * flicker)
            pygame.draw.polygon(surface, config.FIRE, [(x - 8, y + 4), (x + 8, y + 4), (x, y - flame_h)])
            pygame.draw.polygon(surface, config.AMBER, [(x - 4, y + 2), (x + 4, y + 2), (x, y - flame_h // 2)])

    def _draw_fire(self, surface: pygame.Surface, x: int, y: int, t: float) -> None:
        flicker = 0.8 + 0.2 * math.sin(t * 11) * math.cos(t * 5.1)
        glow = pygame.Surface((700, 500))
        strength = 0.12 if self.is_provisional else 0.05
        for r in range(240, 10, -12):
            k = strength * flicker * (1 - r / 240)
            pygame.draw.ellipse(glow, tuple(int(c * k) for c in config.FIRE), (350 - r * 1.4, 250 - r, r * 2.8, r * 2))
        surface.blit(glow, (x - 350, y - 250), special_flags=pygame.BLEND_ADD)
        if not self.is_provisional:
            return
        for i in range(5):
            fx = x - 40 + i * 20 + math.sin(t * 9 + i) * 4
            fh = int((26 + i % 3 * 10) * flicker)
            pygame.draw.polygon(surface, config.FIRE if i % 2 else config.AMBER, [(fx - 8, y), (fx + 8, y), (fx, y - fh)])
