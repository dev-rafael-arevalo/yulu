"""Administrador de audio independiente sobre pygame.mixer.

Cuatro categorías con volumen propio: música (bucle, `pygame.mixer.music`), ambiente (capas
en bucle con fundidos, canales reservados), efectos (grupo de canales) y voz (un canal).
Si el mezclador no se puede iniciar o falta un archivo, todo degrada a no-operación con una
advertencia única: la partida nunca se interrumpe por el audio.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from yulu import config
from yulu.paths import AUDIO_DIR

log = logging.getLogger("yulu.audio")

CATEGORIES = ("music", "ambient", "sfx", "voice")
AMBIENT_CHANNELS = 6
VOICE_CHANNEL = AMBIENT_CHANNELS
SFX_CHANNELS = 8
TOTAL_CHANNELS = AMBIENT_CHANNELS + 1 + SFX_CHANNELS
FADE_RATE = 0.8  # cambio de ganancia por segundo en los fundidos de ambiente
EXTENSIONS = (".ogg", ".wav")


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class _AmbientLayer:
    channel: pygame.mixer.Channel
    gain: float = 0.0
    target: float = 0.0


@dataclass
class AudioManager:
    audio_dir: Path = AUDIO_DIR
    volumes: dict[str, float] = field(default_factory=lambda: dict(config.DEFAULT_VOLUMES))
    enabled: bool = True

    def __post_init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._warned: set[str] = set()
        self._layers: dict[str, _AmbientLayer] = {}
        self._free_ambient: list[int] = list(range(AMBIENT_CHANNELS))
        self._music_name: str | None = None
        self._voice_channel: pygame.mixer.Channel | None = None
        if self.enabled:
            self.enabled = self._init_mixer()

    def _init_mixer(self) -> bool:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(TOTAL_CHANNELS)
            pygame.mixer.set_reserved(AMBIENT_CHANNELS + 1)
            self._voice_channel = pygame.mixer.Channel(VOICE_CHANNEL)
            return True
        except pygame.error as exc:
            log.warning("Audio desactivado: no se pudo iniciar el mezclador (%s)", exc)
            return False

    # ---------- carga ----------
    def _resolve(self, category: str, name: str) -> Path | None:
        base = self.audio_dir / category / name
        candidates = [base] if base.suffix else [base.with_suffix(ext) for ext in EXTENSIONS]
        return next((p for p in candidates if p.is_file()), None)

    def _sound(self, category: str, name: str) -> pygame.mixer.Sound | None:
        key = f"{category}/{name}"
        if key in self._sounds:
            return self._sounds[key]
        sound: pygame.mixer.Sound | None = None
        path = self._resolve(category, name)
        if path is None:
            self._warn(key, "no encontrado")
        else:
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                self._warn(key, f"no se pudo cargar ({exc})")
        self._sounds[key] = sound
        return sound

    def _warn(self, key: str, reason: str) -> None:
        if key not in self._warned:
            self._warned.add(key)
            log.warning("Audio %s: %s; la partida continúa sin ese sonido", key, reason)

    def has(self, category: str, name: str) -> bool:
        return self._resolve(category, name) is not None

    # ---------- volúmenes ----------
    def set_volume(self, category: str, value: float) -> None:
        if category not in CATEGORIES:
            raise ValueError(f"Categoría de audio desconocida: {category}")
        self.volumes[category] = clamp01(value)
        if not self.enabled:
            return
        if category == "music":
            pygame.mixer.music.set_volume(self.volumes["music"])
        elif category == "ambient":
            for layer in self._layers.values():
                layer.channel.set_volume(layer.gain * self.volumes["ambient"])
        elif category == "voice" and self._voice_channel is not None:
            self._voice_channel.set_volume(self.volumes["voice"])

    def adjust_volume(self, category: str, delta: float) -> float:
        self.set_volume(category, self.volumes[category] + delta)
        return self.volumes[category]

    # ---------- música ----------
    def play_music(self, name: str, fade_ms: int = 1500) -> bool:
        if not self.enabled or name == self._music_name:
            return False
        path = self._resolve("music", name)
        if path is None:
            self._warn(f"music/{name}", "no encontrado")
            return False
        try:
            if self._music_name is not None:
                pygame.mixer.music.fadeout(fade_ms)
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.volumes["music"])
            pygame.mixer.music.play(loops=-1, fade_ms=fade_ms)
        except pygame.error as exc:
            self._warn(f"music/{name}", f"no se pudo reproducir ({exc})")
            return False
        self._music_name = name
        return True

    def stop_music(self, fade_ms: int = 1000) -> None:
        if self.enabled and self._music_name is not None:
            pygame.mixer.music.fadeout(fade_ms)
        self._music_name = None

    @property
    def current_music(self) -> str | None:
        return self._music_name

    # ---------- ambiente por capas ----------
    def set_ambient_layers(self, targets: dict[str, float]) -> None:
        """Fija la ganancia objetivo de cada capa; las ausentes se funden a silencio."""
        for name, layer in self._layers.items():
            layer.target = clamp01(targets.get(name, 0.0))
        for name, gain in targets.items():
            if name not in self._layers and gain > 0:
                self._start_layer(name, clamp01(gain))

    def _start_layer(self, name: str, target: float) -> None:
        if not self.enabled or not self._free_ambient:
            return
        sound = self._sound("ambient", name)
        if sound is None:
            return
        channel = pygame.mixer.Channel(self._free_ambient.pop(0))
        channel.set_volume(0.0)
        channel.play(sound, loops=-1)
        self._layers[name] = _AmbientLayer(channel=channel, gain=0.0, target=target)

    def ambient_gains(self) -> dict[str, float]:
        return {name: layer.gain for name, layer in self._layers.items()}

    def update(self, dt: float) -> None:
        """Avanza los fundidos de ambiente. Llamar una vez por fotograma."""
        if not self.enabled:
            return
        finished: list[str] = []
        for name, layer in self._layers.items():
            if layer.gain < layer.target:
                layer.gain = min(layer.target, layer.gain + FADE_RATE * dt)
            elif layer.gain > layer.target:
                layer.gain = max(layer.target, layer.gain - FADE_RATE * dt)
            layer.channel.set_volume(layer.gain * self.volumes["ambient"])
            if layer.target <= 0 and layer.gain <= 0:
                finished.append(name)
        for name in finished:
            layer = self._layers.pop(name)
            layer.channel.stop()
            self._free_ambient.append(self._channel_index(layer.channel))
            self._free_ambient.sort()

    @staticmethod
    def _channel_index(channel: pygame.mixer.Channel) -> int:
        for i in range(AMBIENT_CHANNELS):
            if pygame.mixer.Channel(i) == channel:
                return i
        return 0

    # ---------- efectos ----------
    def play_sfx(self, name: str, gain: float = 1.0) -> bool:
        if not self.enabled:
            return False
        sound = self._sound("sfx", name)
        if sound is None:
            return False
        channel = pygame.mixer.find_channel(True)
        if channel is None:
            return False
        channel.set_volume(clamp01(gain) * self.volumes["sfx"])
        channel.play(sound)
        return True

    # ---------- voz ----------
    def play_voice(self, name: str) -> bool:
        if not self.enabled or self._voice_channel is None:
            return False
        sound = self._sound("voice", name)
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
