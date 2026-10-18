"""Personajes en pantalla: retrato del locutor actual y grupos de pobladores por escena.

Los retratos y grupos se declaran en `assets/manifest.json` (sección "characters") y se
dibujan sobre el fondo, con fundidos, sin reemplazarlo. Solo aparecen donde la narrativa
lo exige: el retrato cuando ese personaje habla y los grupos en las escenas listadas.

Dos estilos de retrato:
- "cutout": PNG con transparencia (personaje recortado).
- "card": imagen íntegra y opaca (personaje con su propio fondo) mostrada como una
  viñeta con esquinas redondeadas y bordes desvanecidos, sin intentar quitarle el fondo.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from yulu import config
from yulu.ui.assets import ImageStore

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
PORTRAIT_HEIGHT = int(H * 0.50)
CARD_HEIGHT = int(H * 0.60)
PORTRAIT_TOP_MIN = 92  # por debajo del HUD
PORTRAIT_BOTTOM = H - 230 + 24  # apoya sobre la caja de diálogo
CARD_BOTTOM = H - 230 - 12  # la viñeta no se solapa con la caja
FADE_SPEED = 3.0  # unidades de alfa (0-1) por segundo
CARD_FEATHER = 0.08  # fracción del borde con desvanecido


@dataclass
class _Placed:
    surface: pygame.Surface
    x: int
    y: int
    alpha_max: float
    alpha: float = 0.0
    target: float = 1.0


def _card_mask(size: tuple[int, int], feather: float = CARD_FEATHER) -> pygame.Surface:
    """Máscara con esquinas redondeadas y borde desvanecido para imágenes opacas."""
    w, h = size
    mask = pygame.Surface(size, pygame.SRCALPHA)
    steps = max(4, int(min(w, h) * feather))
    radius = int(min(w, h) * 0.08)
    for i in range(steps):
        t = i / steps
        alpha = int(255 * t * t)
        rect = pygame.Rect(i, i, w - 2 * i, h - 2 * i)
        pygame.draw.rect(mask, (255, 255, 255, alpha), rect, border_radius=max(2, radius - i // 2))
    pygame.draw.rect(mask, (255, 255, 255, 255), pygame.Rect(steps, steps, w - 2 * steps, h - 2 * steps), border_radius=max(2, radius - steps // 2))
    return mask


def _apply_card_mask(image: pygame.Surface) -> pygame.Surface:
    card = image.convert_alpha()
    mask = _card_mask(card.get_size())
    card.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    frame = pygame.Surface(card.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(frame, (*config.AMBER, 110), frame.get_rect(), 2, border_radius=int(min(card.get_size()) * 0.08))
    card.blit(frame, (0, 0))
    return card


class CharacterLayer:
    def __init__(self, store: ImageStore) -> None:
        self.store = store
        spec = store.manifest.get("characters", {})
        self._portraits: dict[str, dict] = {
            name: (value if isinstance(value, dict) else {"file": value, "style": "cutout"}) for name, value in spec.get("portraits", {}).items()
        }
        self._scene_specs: dict[str, list[dict]] = spec.get("scenes", {})
        self._cache: dict[tuple[str, int, str], pygame.Surface] = {}
        self._portrait: _Placed | None = None
        self._portrait_name: str | None = None
        self._groups: list[_Placed] = []

    # ---------- carga ----------
    def _scaled(self, filename: str, height: int, style: str = "cutout") -> pygame.Surface | None:
        key = (filename, height, style)
        if key not in self._cache:
            raw = self.store.character(filename)
            if raw is None:
                return None
            ratio = raw.get_width() / raw.get_height()
            scaled = pygame.transform.smoothscale(raw, (max(1, int(height * ratio)), height))
            self._cache[key] = _apply_card_mask(scaled) if style == "card" else scaled
        return self._cache[key]

    # ---------- estado ----------
    def set_scene(self, scene_id: str) -> None:
        for group in self._groups:
            group.target = 0.0
        for spec in self._scene_specs.get(scene_id, []):
            surface = self._scaled(spec["file"], int(spec.get("height", 0.4) * H))
            if surface is None:
                continue
            x = max(0, min(W - surface.get_width(), int(spec.get("x", 0.05) * W)))
            y = max(PORTRAIT_TOP_MIN, int(spec.get("bottom", 0.7) * H) - surface.get_height())
            self._groups.append(_Placed(surface, x, y, float(spec.get("alpha", 0.9))))
        self.set_speaker(None)

    def set_speaker(self, speaker: str | None) -> None:
        spec = self._portraits.get(speaker or "")
        if spec is None:
            if self._portrait is not None:
                self._portrait.target = 0.0
            self._portrait_name = None
            return
        if speaker == self._portrait_name and self._portrait is not None:
            self._portrait.target = 1.0
            return
        style = spec.get("style", "cutout")
        height = CARD_HEIGHT if style == "card" else PORTRAIT_HEIGHT
        surface = self._scaled(spec["file"], height, style)
        if surface is None:
            return
        bottom = CARD_BOTTOM if style == "card" else PORTRAIT_BOTTOM
        x = max(0, W - surface.get_width() - 70)
        y = max(PORTRAIT_TOP_MIN, bottom - surface.get_height())
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
