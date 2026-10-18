"""Administrador de audio sobre pygame.mixer, dirigido por `assets/audio/manifest.json`.

Cuatro volúmenes independientes (música, ambiente, efectos, voz). Cada sonido del manifiesto
tiene un identificador estable, una ganancia base y una categoría. La música se atenúa
automáticamente mientras suena una voz. Si el mezclador no arranca o falta un archivo, todo
degrada a no-operación con una advertencia única: la partida nunca se interrumpe por el audio.
"""
from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from yulu import config
from yulu.paths import AUDIO_DIR

log = logging.getLogger("yulu.audio")

CATEGORIES = ("music", "ambient", "sfx", "voice")
# Categoría del manifiesto -> volumen de usuario que la gobierna.
VOLUME_OF = {"ambient": "ambient", "effects": "sfx", "creatures": "sfx", "ui": "sfx", "music": "music"}
AMBIENT_CHANNELS = 8
VOICE_CHANNEL = AMBIENT_CHANNELS
SFX_CHANNELS = 8
TOTAL_CHANNELS = AMBIENT_CHANNELS + 1 + SFX_CHANNELS
FADE_RATE = 0.6  # cambio de ganancia por segundo en los fundidos de ambiente
MUSIC_FADE_RATE = 0.7
DUCK_FACTOR = 0.45  # música mientras habla una voz
MANIFEST_PATH = AUDIO_DIR / "manifest.json"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class SoundEntry:
    id: str
    file: str
    category: str
    gain: float = 1.0
    loop: bool = False


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, SoundEntry]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("No se pudo leer el manifiesto de audio %s: %s", path, exc)
        return {}
    entries: dict[str, SoundEntry] = {}
    for item in raw.get("sounds", []):
        try:
            entries[item["id"]] = SoundEntry(item["id"], item["file"], item["category"], float(item.get("gain", 1.0)), bool(item.get("loop", False)))
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("Entrada de audio inválida %r: %s", item, exc)
    return entries


@dataclass
class _Layer:
    channel: pygame.mixer.Channel
    index: int
    base_gain: float
    gain: float = 0.0
    target: float = 0.0


@dataclass
class AudioManager:
    audio_dir: Path = AUDIO_DIR
    manifest: dict[str, SoundEntry] | None = None
    volumes: dict[str, float] = field(default_factory=lambda: dict(config.DEFAULT_VOLUMES))
    enabled: bool = True
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        if self.manifest is None:
            self.manifest = load_manifest(self.audio_dir / "manifest.json")
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._warned: set[str] = set()
        self._layers: dict[str, _Layer] = {}
        self._free_ambient: list[int] = list(range(AMBIENT_CHANNELS))
        self._music_id: str | None = None
        self._music_gain = 1.0
        self._music_level = 0.0  # nivel actual (0-1) para fundidos y atenuación
        self._voice_channel: pygame.mixer.Channel | None = None
        if self.enabled:
            self.enabled = self._init_mixer()

    def _init_mixer(self) -> bool:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.set_num_channels(TOTAL_CHANNELS)
            pygame.mixer.set_reserved(AMBIENT_CHANNELS + 1)
            self._voice_channel = pygame.mixer.Channel(VOICE_CHANNEL)
            return True
        except pygame.error as exc:
            log.warning("Audio desactivado: no se pudo iniciar el mezclador (%s)", exc)
            return False

    # ---------- resolución y carga ----------
    def entry(self, sound_id: str) -> SoundEntry | None:
        return (self.manifest or {}).get(sound_id)

    def ids(self, category: str | None = None) -> list[str]:
        return [e.id for e in (self.manifest or {}).values() if category is None or e.category == category]

    def path_for(self, sound_id: str) -> Path | None:
        entry = self.entry(sound_id)
        if entry is None:
            self._warn(sound_id, "no está en el manifiesto")
            return None
        path = self.audio_dir / entry.file
        if not path.is_file():
            self._warn(sound_id, f"archivo ausente ({entry.file})")
            return None
        return path

    def has(self, sound_id: str) -> bool:
        entry = self.entry(sound_id)
        return entry is not None and (self.audio_dir / entry.file).is_file()

    def _sound(self, sound_id: str) -> pygame.mixer.Sound | None:
        if sound_id in self._sounds:
            return self._sounds[sound_id]
        sound: pygame.mixer.Sound | None = None
        path = self.path_for(sound_id)
        if path is not None:
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                self._warn(sound_id, f"no se pudo cargar ({exc})")
        self._sounds[sound_id] = sound
        return sound

    def _voice_sound(self, filename: str) -> pygame.mixer.Sound | None:
        key = f"voice/{filename}"
        if key in self._sounds:
            return self._sounds[key]
        path = self.audio_dir / "voice" / filename
        sound: pygame.mixer.Sound | None = None
        if path.is_file():
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                self._warn(key, f"no se pudo cargar ({exc})")
        else:
            self._warn(key, "sin narración pregenerada (tools/generate_narration.py)")
        self._sounds[key] = sound
        return sound

    def _warn(self, key: str, reason: str) -> None:
        if key not in self._warned:
            self._warned.add(key)
            log.warning("Audio %s: %s; la partida continúa", key, reason)

    def _user_volume(self, entry: SoundEntry) -> float:
        return self.volumes[VOLUME_OF.get(entry.category, "sfx")]

    # ---------- volúmenes ----------
    def set_volume(self, category: str, value: float) -> None:
        if category not in CATEGORIES:
            raise ValueError(f"Categoría de audio desconocida: {category}")
        self.volumes[category] = clamp01(value)
        if not self.enabled:
            return
        if category == "ambient":
            for layer in self._layers.values():
                layer.channel.set_volume(layer.gain * layer.base_gain * self.volumes["ambient"])
        elif category == "voice" and self._voice_channel is not None:
            self._voice_channel.set_volume(self.volumes["voice"])
        # La música se aplica en update() porque depende del fundido y de la atenuación.

    def adjust_volume(self, category: str, delta: float) -> float:
        self.set_volume(category, self.volumes[category] + delta)
        return self.volumes[category]

    # ---------- música ----------
    def play_music(self, sound_id: str, fade_ms: int = 2000) -> bool:
        if not self.enabled or sound_id == self._music_id:
            return False
        entry = self.entry(sound_id)
        path = self.path_for(sound_id)
        if entry is None or path is None:
            return False
        try:
            if self._music_id is not None:
                pygame.mixer.music.fadeout(fade_ms)
            pygame.mixer.music.load(str(path))
            self._music_gain = entry.gain
            self._music_level = 0.0
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.play(loops=-1 if entry.loop else 0, fade_ms=fade_ms)
        except pygame.error as exc:
            self._warn(sound_id, f"no se pudo reproducir ({exc})")
            return False
        self._music_id = sound_id
        return True

    def stop_music(self, fade_ms: int = 1500) -> None:
        if self.enabled and self._music_id is not None:
            pygame.mixer.music.fadeout(fade_ms)
        self._music_id = None

    @property
    def current_music(self) -> str | None:
        return self._music_id

    # ---------- ambiente por capas ----------
    def set_ambient_layers(self, targets: dict[str, float]) -> None:
        """Fija la ganancia objetivo de cada capa; las ausentes se funden a silencio."""
        for name, layer in self._layers.items():
            layer.target = clamp01(targets.get(name, 0.0))
        for name, gain in targets.items():
            if name not in self._layers and gain > 0:
                self._start_layer(name, clamp01(gain))

    def _start_layer(self, sound_id: str, target: float) -> None:
        if not self.enabled or not self._free_ambient:
            return
        entry = self.entry(sound_id)
        sound = self._sound(sound_id)
        if entry is None or sound is None:
            return
        index = self._free_ambient.pop(0)
        channel = pygame.mixer.Channel(index)
        channel.set_volume(0.0)
        channel.play(sound, loops=-1, fade_ms=400)
        self._layers[sound_id] = _Layer(channel=channel, index=index, base_gain=entry.gain, gain=0.0, target=target)

    def ambient_gains(self) -> dict[str, float]:
        return {name: layer.gain for name, layer in self._layers.items()}

    def update(self, dt: float) -> None:
        """Avanza fundidos de ambiente, nivel de música y atenuación por voz. Una vez por fotograma."""
        if not self.enabled:
            return
        self._update_layers(dt)
        self._update_music(dt)

    def _update_layers(self, dt: float) -> None:
        finished: list[str] = []
        for name, layer in self._layers.items():
            if layer.gain < layer.target:
                layer.gain = min(layer.target, layer.gain + FADE_RATE * dt)
            elif layer.gain > layer.target:
                layer.gain = max(layer.target, layer.gain - FADE_RATE * dt)
            layer.channel.set_volume(layer.gain * layer.base_gain * self.volumes["ambient"])
            if layer.target <= 0 and layer.gain <= 0:
                finished.append(name)
        for name in finished:
            layer = self._layers.pop(name)
            layer.channel.stop()
            self._free_ambient.append(layer.index)
            self._free_ambient.sort()

    def _update_music(self, dt: float) -> None:
        if self._music_id is None:
            return
        target = DUCK_FACTOR if self.voice_playing() else 1.0
        if self._music_level < target:
            self._music_level = min(target, self._music_level + MUSIC_FADE_RATE * dt)
        elif self._music_level > target:
            self._music_level = max(target, self._music_level - MUSIC_FADE_RATE * 2 * dt)
        try:
            pygame.mixer.music.set_volume(self._music_level * self._music_gain * self.volumes["music"])
        except pygame.error:
            pass

    # ---------- efectos ----------
    def play_sfx(self, sound_id: str, gain: float = 1.0, pan: float | None = None, vary: bool = True) -> bool:
        """Reproduce un efecto. `pan` va de -1 (izquierda) a 1 (derecha); None = ligera variación aleatoria."""
        if not self.enabled:
            return False
        entry = self.entry(sound_id)
        sound = self._sound(sound_id)
        if entry is None or sound is None:
            return False
        channel = pygame.mixer.find_channel(True)
        if channel is None:
            return False
        level = clamp01(gain) * entry.gain * self._user_volume(entry)
        if vary:
            level *= self.rng.uniform(0.85, 1.0)
        if pan is None:
            pan = self.rng.uniform(-0.35, 0.35) if vary else 0.0
        pan = max(-1.0, min(1.0, pan))
        channel.set_volume(level * min(1.0, 1.0 - pan), level * min(1.0, 1.0 + pan))
        channel.play(sound)
        return True

    # ---------- voz ----------
    def play_voice(self, filename: str) -> bool:
        if not self.enabled or self._voice_channel is None:
            return False
        sound = self._voice_sound(filename)
        if sound is None:
            return False
        self._voice_channel.stop()
        self._voice_channel.set_volume(self.volumes["voice"])
        self._voice_channel.play(sound)
        return True

    def stop_voice(self) -> None:
        if self.enabled and self._voice_channel is not None:
            self._voice_channel.stop()

    def voice_playing(self) -> bool:
        return bool(self.enabled and self._voice_channel is not None and self._voice_channel.get_busy())

    # ---------- cierre ----------
    def shutdown(self) -> None:
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.stop()
        except pygame.error:
            pass
