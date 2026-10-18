"""Paisaje sonoro: traduce el estado narrativo (escena, amenaza, decisiones) en capas de
ambiente, música y efectos, evitando repeticiones mecánicas y superposiciones.

Los identificadores corresponden a `assets/audio/manifest.json`.
"""
from __future__ import annotations

import random

from yulu import config
from yulu.audio.audio_manager import AudioManager
from yulu.narrative.schema import Scene
from yulu.state.engine import ChoiceResult

# Capas de ambiente por clave de escena (Scene.ambient). Ganancias relativas (0-1).
AMBIENT_PRESETS: dict[str, dict[str, float]] = {
    "forest_night": {"jungla_noche_densa": 0.9, "viento_suave": 0.5},
    "forest_tense": {"jungla_noche_abierta": 0.7, "viento_aullante": 0.6, "lluvia_ligera": 0.35},
    "village_distant": {"jungla_noche_abierta": 0.6, "aldea_distante": 0.5, "antorcha": 0.3, "tambor_lento": 0.5},
    "village_gate": {"antorcha": 0.9, "aldea_distante": 0.7, "jungla_noche_abierta": 0.35, "tambor_lento": 0.4},
    "shelter": {"fogata_crepitante": 1.0, "aldea_distante": 0.3, "jungla_noche_densa": 0.15},  # exterior atenuado
    "shelter_alarm": {"fogata_crepitante": 0.8, "aldea_distante": 0.6},
    "dawn": {"amanecer_aves": 0.9, "viento_suave": 0.4},
}
# Capa que crece con la amenaza en cada preset (tambores durante la persecución, viento en el resto).
TENSION_LAYER: dict[str, str] = {
    "forest_night": "viento_aullante",
    "forest_tense": "tambor_persecucion",
    "village_distant": "tambor_persecucion",
    "village_gate": "tambor_persecucion",
    "shelter_alarm": "tambor_persecucion",
}
MUSIC_FOR_AMBIENT: dict[str, str] = {"forest_tense": "persecucion", "shelter_alarm": "persecucion"}
# Ambientes donde el jaguar está presente aunque no se dibuje como sprite (va en el fondo o fuera de plano).
JAGUAR_PRESENT_AMBIENTS = {"forest_tense", "shelter_alarm"}
DEFAULT_PRESET = "forest_night"
DEFAULT_MUSIC = "exploracion"
ENDING_MUSIC = {True: "desenlace_aldea", False: "desenlace_solo"}

GROWLS = ("jaguar_sierra", "felino_grunido")
MOVEMENT = "vegetacion"
ROAR = "felino_rugido_ataque"
TIMER_WARNING_SECONDS = 3.0


class Soundscape:
    def __init__(self, audio: AudioManager, rng: random.Random | None = None) -> None:
        self.audio = audio
        self.rng = rng or random.Random()
        self.ambient_key = DEFAULT_PRESET
        self.jaguar_visible = False
        self._cue_timer = self._next_cue_interval(0)
        self._move_timer = self.rng.uniform(6.0, 12.0)
        self._last_tick_second: int | None = None

    # ---------- escena ----------
    def enter_scene(self, scene: Scene, threat: int) -> None:
        self.ambient_key = scene.ambient if scene.ambient in AMBIENT_PRESETS else DEFAULT_PRESET
        self.jaguar_visible = scene.jaguar_visible or scene.ambient in JAGUAR_PRESENT_AMBIENTS
        self.audio.set_ambient_layers(self.layers_for(threat))
        if not scene.is_ending:
            self.audio.play_music(MUSIC_FOR_AMBIENT.get(self.ambient_key, DEFAULT_MUSIC))
        self._last_tick_second = None
        self._cue_timer = max(self._cue_timer, 3.0)  # sin rugido inmediato al cambiar de escena

    def layers_for(self, threat: int) -> dict[str, float]:
        layers = dict(AMBIENT_PRESETS[self.ambient_key])
        tension = TENSION_LAYER.get(self.ambient_key)
        if tension:
            layers[tension] = max(layers.get(tension, 0.0), self.tension_gain(threat))
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
        self._move_timer -= dt
        if self._move_timer <= 0 and threat >= 35:
            # Movimiento entre la vegetación: siempre desde un lado, nunca centrado.
            self.audio.play_sfx(MOVEMENT, gain=0.3 + 0.4 * threat / config.METER_MAX, pan=self.rng.choice((-0.8, -0.5, 0.5, 0.8)))
            self._move_timer = self.rng.uniform(9.0, 18.0)
        if self._cue_timer > 0:
            return
        if threat >= config.THREAT_HIGH and self.rng.random() < 0.35:
            name = ROAR
        else:
            name = self.rng.choice(GROWLS)
        self.audio.play_sfx(name, gain=0.4 + 0.6 * threat / config.METER_MAX, pan=self.rng.uniform(-0.7, 0.7))
        self._cue_timer = self._next_cue_interval(threat)

    def _next_cue_interval(self, threat: int) -> float:
        """Intervalo aleatorio que se acorta con la amenaza; nunca menor de 7 s."""
        base = self.rng.uniform(18.0, 34.0)
        return max(7.0, base - 16.0 * threat / config.METER_MAX)

    def _update_timer_ticks(self, timer_left: float | None) -> None:
        if timer_left is None or timer_left > TIMER_WARNING_SECONDS:
            self._last_tick_second = None
            return
        second = int(timer_left)
        if second != self._last_tick_second:
            self._last_tick_second = second
            self.audio.play_sfx("tick", gain=0.7, pan=0.0, vary=False)

    # ---------- eventos ----------
    def on_choice(self, result: ChoiceResult) -> None:
        self.audio.play_sfx("ui_confirm", gain=0.6, pan=0.0, vary=False)
        if result.threat_delta >= 15:
            self.audio.play_sfx(ROAR, gain=1.0, pan=self.rng.uniform(-0.4, 0.4))
            self._cue_timer = self._next_cue_interval(100)
        elif result.threat_delta <= -10:
            self.audio.play_sfx(MOVEMENT, gain=0.5)
        if result.learned:
            self.audio.play_sfx("learn_chime", gain=0.8, pan=0.0, vary=False)

    def on_menu_move(self) -> None:
        self.audio.play_sfx("ui_move", gain=0.4, pan=0.0, vary=False)

    def on_transition(self) -> None:
        self.audio.play_sfx("pasos_hojarasca", gain=0.6)

    def on_ending(self, good: bool) -> None:
        self.audio.play_music(ENDING_MUSIC[good], fade_ms=3000)
        if not good:
            self.audio.play_sfx(ROAR, gain=0.45, pan=-0.6)
