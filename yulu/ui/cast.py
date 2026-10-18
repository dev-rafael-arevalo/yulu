"""Reparto en escena: personajes y jaguar de cuerpo entero integrados sobre el fondo.

Cada escena declara en `assets/manifest.json` ("cast") qué figuras aparecen, dónde pisan y
a qué altura. La capa se encarga de que se vean como parte de la imagen y no como pegatinas:

- sombra de contacto bajo los pies, con la misma dirección de luz de la escena;
- tono de luz tomado del escenario (cálido junto a antorchas y hogueras, frío bajo la luna)
  y un ligero oscurecimiento de las figuras que no hablan;
- el personaje que habla se ilumina, avanza unos píxeles y queda por delante;
- el jaguar escala y se acerca con la amenaza y nunca se dibuja translúcido;
- entradas y salidas con fundido corto.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from yulu import config
from yulu.ui.assets import ImageStore

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
GROUND_Y = H - 230 + 18  # línea de suelo: justo sobre la caja de diálogo
FADE_SPEED = 2.6
DIM_FACTOR = 0.72  # brillo de las figuras que no hablan
WARM_TINT = (255, 226, 196)
COOL_TINT = (200, 216, 240)
TOP_MIN = 84  # ninguna figura sube por encima del HUD


@dataclass
class CastSpec:
    file: str
    x: float  # centro horizontal normalizado (0-1)
    height: float = 0.62  # altura normalizada respecto a la pantalla
    ground: float | None = None  # línea de pies normalizada; None = línea de suelo estándar
    flip: bool = False
    speaker: str | None = None  # nombre del locutor al que representa
    jaguar: bool = False  # escala y se acerca con la amenaza
    threat_scale: tuple[float, float] = (0.7, 1.15)
    dim: float = 1.0  # multiplicador de brillo adicional (figuras lejanas)

    @classmethod
    def from_dict(cls, raw: dict) -> "CastSpec":
        ts = raw.get("threat_scale", (0.7, 1.15))
        return cls(
            file=raw["file"], x=float(raw.get("x", 0.5)), height=float(raw.get("height", 0.62)),
            ground=raw.get("ground"), flip=bool(raw.get("flip", False)), speaker=raw.get("speaker"),
            jaguar=bool(raw.get("jaguar", False)), threat_scale=(float(ts[0]), float(ts[1])), dim=float(raw.get("dim", 1.0)),
        )


@dataclass
class _Actor:
    spec: CastSpec
    base: pygame.Surface  # recorte con tono de escena aplicado, a la altura nominal
    alpha: float = 0.0
    target: float = 1.0
    lit: float = 0.0  # 0 = atenuado, 1 = hablando
    scale: float = 1.0
    cache: dict[tuple[int, int], pygame.Surface] = field(default_factory=dict)


def _tinted(surface: pygame.Surface, tint: tuple[int, int, int], brightness: float) -> pygame.Surface:
    out = surface.copy()
    color = tuple(max(0, min(255, int(c * brightness))) for c in tint)
    out.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def _ground_shadow(width: int) -> pygame.Surface:
    w, h = max(8, int(width * 0.95)), max(4, int(width * 0.16))
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(6, 0, -1):
        k = i / 6
        pygame.draw.ellipse(shadow, (0, 0, 0, int(26 * (1 - k) + 8)), (w * (1 - k) / 2, h * (1 - k) / 2, w * k, h * k))
    return shadow


class CastLayer:
    def __init__(self, store: ImageStore) -> None:
        self.store = store
        self._specs: dict[str, list[CastSpec]] = {
            scene_id: [CastSpec.from_dict(item) for item in items] for scene_id, items in store.manifest.get("cast", {}).items()
        }
        self._warmth: dict[str, float] = {key: float(spec.get("warmth", 0.0)) for key, spec in store.manifest.get("backgrounds", {}).items()}
        self._raw_cache: dict[str, pygame.Surface | None] = {}
        self._actors: list[_Actor] = []
        self._speaker: str | None = None
        self._threat = 0.0

    # ---------- construcción ----------
    def _raw(self, filename: str) -> pygame.Surface | None:
        if filename not in self._raw_cache:
            self._raw_cache[filename] = self.store.character(filename)
        return self._raw_cache[filename]

    def _build_actor(self, spec: CastSpec, warmth: float) -> _Actor | None:
        raw = self._raw(spec.file)
        if raw is None:
            return None
        height = int(spec.height * H)
        width = max(1, int(height * raw.get_width() / raw.get_height()))
        sprite = pygame.transform.smoothscale(raw, (width, height))
        if spec.flip:
            sprite = pygame.transform.flip(sprite, True, False)
        tint = tuple(int(COOL_TINT[i] + (WARM_TINT[i] - COOL_TINT[i]) * warmth) for i in range(3))
        return _Actor(spec=spec, base=_tinted(sprite, tint, spec.dim))

    def set_scene(self, scene_id: str, background_key: str, threat: int) -> None:
        for actor in self._actors:
            actor.target = 0.0
        warmth = self._warmth.get(background_key, 0.0)
        for spec in self._specs.get(scene_id, []):
            actor = self._build_actor(spec, warmth)
            if actor is not None:
                self._actors.append(actor)
        self._threat = threat / config.METER_MAX
        self._speaker = None

    def set_speaker(self, speaker: str | None) -> None:
        self._speaker = speaker

    def has_cast(self, scene_id: str) -> bool:
        return bool(self._specs.get(scene_id))

    # ---------- animación ----------
    def update(self, dt: float, threat: int) -> None:
        self._threat += (threat / config.METER_MAX - self._threat) * min(1.0, dt * 2.0)
        alive: list[_Actor] = []
        for actor in self._actors:
            step = FADE_SPEED * dt
            actor.alpha = min(actor.target, actor.alpha + step) if actor.alpha < actor.target else max(actor.target, actor.alpha - step)
            speaking = actor.spec.speaker is not None and actor.spec.speaker == self._speaker
            goal = 1.0 if speaking or actor.spec.speaker is None else 0.0
            actor.lit += (goal - actor.lit) * min(1.0, dt * 5.0)
            if actor.spec.jaguar:
                lo, hi = actor.spec.threat_scale
                actor.scale = lo + (hi - lo) * self._threat
            if not (actor.target <= 0 and actor.alpha <= 0):
                alive.append(actor)
        self._actors = alive

    # ---------- dibujo ----------
    def _frame(self, actor: _Actor) -> pygame.Surface:
        """Versión escalada e iluminada del recorte, cacheada por (escala, iluminación)."""
        key = (int(actor.scale * 100), int(actor.lit * 10))
        if key not in actor.cache:
            sprite = actor.base
            if abs(actor.scale - 1.0) > 0.01:
                sprite = pygame.transform.smoothscale(sprite, (max(1, int(sprite.get_width() * actor.scale)), max(1, int(sprite.get_height() * actor.scale))))
            brightness = DIM_FACTOR + (1.0 - DIM_FACTOR) * actor.lit
            if brightness < 0.999:
                sprite = _tinted(sprite, (255, 255, 255), brightness)
            actor.cache[key] = sprite
        return actor.cache[key]

    def draw(self, surface: pygame.Surface) -> None:
        # Orden: primero los que no hablan y los más alejados; el que habla, al final (delante).
        ordered = sorted(self._actors, key=lambda a: (a.lit, a.spec.height * a.scale))
        for actor in ordered:
            if actor.alpha <= 0:
                continue
            sprite = self._frame(actor)
            w, h = sprite.get_size()
            ground = int((actor.spec.ground * H) if actor.spec.ground is not None else GROUND_Y)
            if actor.spec.jaguar:
                ground += int(10 * self._threat)
            x = int(actor.spec.x * W - w / 2 + 14 * actor.lit * (1 if actor.spec.x < 0.5 else -1))
            y = max(TOP_MIN, ground - h)
            x = max(-w // 4, min(W - 3 * w // 4, x))
            shadow = _ground_shadow(w)
            shadow.set_alpha(int(255 * actor.alpha))
            surface.blit(shadow, (x + (w - shadow.get_width()) // 2, ground - shadow.get_height() // 2 - 2))
            sprite.set_alpha(int(255 * actor.alpha))
            surface.blit(sprite, (x, y))

    @property
    def speaker_on_stage(self) -> bool:
        return any(a.spec.speaker == self._speaker and a.alpha > 0 for a in self._actors)
