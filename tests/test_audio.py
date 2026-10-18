"""El audio nunca debe interrumpir la partida: recursos ausentes, mezclador caído y volúmenes."""
from __future__ import annotations

import os
import random

import pygame
import pytest

from yulu.audio.audio_manager import AudioManager
from yulu.audio.soundscape import AMBIENT_PRESETS, Soundscape
from yulu.audio.voice import voice_filename, voice_key
from yulu.narrative.scenes import SCENES
from yulu.narrative.schema import Choice, DialogueLine, Scene
from yulu.state.engine import ChoiceResult


@pytest.fixture(scope="module", autouse=True)
def headless_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def silent_audio(tmp_path) -> AudioManager:
    """Administrador apuntando a un directorio sin ningún archivo."""
    return AudioManager(audio_dir=tmp_path)


def test_missing_files_do_not_raise(silent_audio):
    assert silent_audio.play_sfx("jaguar_roar") is False
    assert silent_audio.play_voice("nada.wav") is False
    assert silent_audio.play_music("night_drone") is False
    silent_audio.set_ambient_layers({"insects": 0.8, "wind": 0.3})
    silent_audio.update(0.5)
    assert silent_audio.ambient_gains() == {}


def test_disabled_manager_is_noop(tmp_path):
    audio = AudioManager(audio_dir=tmp_path, enabled=False)
    assert audio.enabled is False
    assert audio.play_sfx("tick") is False
    audio.set_volume("music", 0.3)
    audio.update(0.1)
    audio.shutdown()


def test_volume_is_clamped_and_independent(silent_audio):
    silent_audio.set_volume("sfx", 1.7)
    silent_audio.set_volume("voice", -2)
    assert silent_audio.volumes["sfx"] == 1.0
    assert silent_audio.volumes["voice"] == 0.0
    assert silent_audio.volumes["music"] == pytest.approx(0.5)
    assert silent_audio.adjust_volume("ambient", -0.2) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        silent_audio.set_volume("otra", 0.5)


def test_real_assets_are_present_and_loadable():
    audio = AudioManager()
    if not audio.enabled:
        pytest.skip("mezclador no disponible")
    for layer in {name for preset in AMBIENT_PRESETS.values() for name in preset}:
        assert audio.has("ambient", layer), f"falta ambient/{layer}"
    for sfx in ("jaguar_roar", "jaguar_growl_1", "ui_confirm", "learn_chime", "tick", "footsteps"):
        assert audio.has("sfx", sfx), f"falta sfx/{sfx}"
    assert audio.play_sfx("ui_confirm")
    assert audio.play_music("night_drone")
    audio.set_ambient_layers({"insects": 1.0})
    audio.update(2.0)
    assert audio.ambient_gains()["insects"] == pytest.approx(1.0)
    audio.set_ambient_layers({})
    audio.update(5.0)
    assert audio.ambient_gains() == {}
    audio.shutdown()


def test_voice_key_is_stable_and_distinct():
    a = voice_key("Narrador", "Hola")
    assert a == voice_key("Narrador", "Hola")
    assert a != voice_key("Guardia", "Hola")
    assert voice_filename(DialogueLine("Narrador", "Hola")) == a + ".wav"
    assert voice_filename(DialogueLine("Narrador", "Hola", voice_file="x.wav")) == "x.wav"


def test_soundscape_layers_follow_threat(silent_audio):
    scape = Soundscape(silent_audio, rng=random.Random(1))
    scene = next(s for s in SCENES.values() if s.ambient == "forest_tense")
    scape.enter_scene(scene, threat=10)
    assert scape.layers_for(10)["tension"] == 0.0
    assert scape.layers_for(85)["tension"] == pytest.approx(1.0)
    safe = Scene("x", 4, "X", (DialogueLine("N", "x"),), ending="fin", ambient="shelter", jaguar_visible=False)
    scape.enter_scene(safe, threat=90)
    assert scape.layers_for(90)["tension"] == 0.0
    assert set(scape.layers_for(90)) >= set(AMBIENT_PRESETS["shelter"])


def test_soundscape_events_never_raise_without_assets(silent_audio):
    scape = Soundscape(silent_audio, rng=random.Random(3))
    scene = SCENES["s2_persecucion"]
    scape.enter_scene(scene, threat=60)
    for _ in range(600):
        scape.update(0.1, threat=90, timer_left=2.5)
    choice = Choice("c", "c", "s2_rio")
    scape.on_choice(ChoiceResult(choice, "", scene, learned=("tekwani",), threat_delta=30))
    scape.on_choice(ChoiceResult(choice, "", scene, learned=(), threat_delta=-15))
    scape.on_transition()
    scape.on_ending(good=True)
    scape.on_ending(good=False)


def test_every_scene_ambient_has_a_preset():
    for scene in SCENES.values():
        assert scene.ambient in AMBIENT_PRESETS, f"{scene.id}: ambiente {scene.ambient} sin preset"
