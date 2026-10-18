"""Paisaje sonoro: traduce el estado narrativo (escena, amenaza, decisiones) en capas de
ambiente, música y efectos, evitando repeticiones mecánicas y superposiciones.
"""
from __future__ import annotations

import random

from yulu import config
from yulu.audio.audio_manager import AudioManager
from yulu.narrative.schema import Scene
from yulu.state.engine import ChoiceResult

# Ganancias base de cada capa de ambiente por clave de escena (Scene.ambient).
AMBIENT_PRESETS: dict[str, dict[str, float]] = {
    "forest_night": {"insects": 0.9, "wind": 0.45},
    "forest_tense": {"insects": 0.5, "wind": 0.7, "heartbeat": 0.55},
    "village_distant": {"insects": 0.6, "wind": 0.3, "drum": 0.5, "fire": 0.25},
    "village_gate": {"fire": 0.8, "drum": 0.35, "insects": 0.3},
    "shelter": {"fire": 1.0, "insects": 0.12},
    "shelter_alarm": {"fire": 0.8, "heartbeat": 0.8, "drum": 0.6},
    "dawn": {"birds": 0.9, "wind": 0.35},
}
DEFAULT_PRESET = "forest_night"
MUSIC_FOR_AMBIENT = {"dawn": "dawn_theme"}
DEFAULT_MUSIC = "night_drone"
TENSION_LAYER = "tension"
GROWLS = ("jaguar_growl_1", "jaguar_growl_2")
ROAR = "jaguar_roar"
TIMER_WARNING_SECONDS = 3.0


class Soundscape:
    def __init__(self, audio: AudioManager, rng: random.Random | None = None) -> None:
        self.audio = audio
        self.rng = rng or random.Random()
        self.ambient_key = DEFAULT_PRESET
        self.jaguar_visible = False
        self._cue_timer = self._next_cue_interval(0)
        self._last_tick_second: int | None = None

    # ---------- escena ----------
    def enter_scene(self, scene: Scene, threat: int) -> None:
        self.ambient_key = scene.ambient if scene.ambient in AMBIENT_PRESETS else DEFAULT_PRESET
        self.jaguar_visible = scene.jaguar_visible
        self.audio.set_ambient_layers(self.layers_for(threat))
        self.audio.play_music(MUSIC_FOR_AMBIENT.get(self.ambient_key, DEFAULT_MUSIC))
        self._last_tick_second = None
        self._cue_timer = max(self._cue_timer, 2.0)  # sin rugido inmediato al cambiar de escena

    def layers_for(self, threat: int) -> dict[str, float]:
        layers = dict(AMBIENT_PRESETS[self.ambient_key])
        layers[TENSION_LAYER] = self.tension_gain(threat)
        return layers

    def tension_gain(self, threat: int) -> float:
        if not self.jaguar_visible:
            return 0.0
        return max(0.0, min(1.0, (threat - 25) / 60))

    # ---------- por fotograma ----------
    def update(self, dt: float, threat: int, timer_left: float | None = None) -> None:
        self.audio.set_ambient_layers(self.layers_for(threat))
        self.audio.update(dt)
        self._update_jaguar_cues(dt, threat)
        self._update_timer_ticks(timer_left)

    def _update_jaguar_cues(self, dt: float, threat: int) -> None:
        if not self.jaguar_visible or threat < 20:
            return
        self._cue_timer -= dt
        if self._cue_timer > 0:
            return
        name = ROAR if threat >= config.THREAT_HIGH and self.rng.random() < 0.4 else self.rng.choice(GROWLS)
        self.audio.play_sfx(name, gain=0.35 + 0.65 * threat / config.METER_MAX)
        self._cue_timer = self._next_cue_interval(threat)

    def _next_cue_interval(self, threat: int) -> float:
        """Intervalo aleatorio que se acorta con la amenaza; nunca menor de 6 s."""
        base = self.rng.uniform(16.0, 30.0)
        return max(6.0, base - 14.0 * threat / config.METER_MAX)

    def _update_timer_ticks(self, timer_left: float | None) -> None:
        if timer_left is None or timer_left > TIMER_WARNING_SECONDS:
            self._last_tick_second = None
            return
        second = int(timer_left)
        if second != self._last_tick_second:
            self._last_tick_second = second
            self.audio.play_sfx("tick", gain=0.7)

    # ---------- eventos ----------
    def on_choice(self, result: ChoiceResult) -> None:
        self.audio.play_sfx("ui_confirm", gain=0.6)
        if result.threat_delta >= 15:
            self.audio.play_sfx(ROAR, gain=1.0)
            self._cue_timer = self._next_cue_interval(100)
        elif result.threat_delta <= -10:
            self.audio.play_sfx("branch_snap", gain=0.5)
        if result.learned:
            self.audio.play_sfx("learn_chime", gain=0.8)

    def on_menu_move(self) -> None:
        self.audio.play_sfx("ui_move", gain=0.4)

    def on_transition(self) -> None:
        self.audio.play_sfx("footsteps", gain=0.6)

    def on_ending(self, good: bool) -> None:
        self.audio.play_sfx("dawn_birds" if good else ROAR, gain=0.8 if good else 0.5)
