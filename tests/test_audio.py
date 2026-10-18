"""El audio nunca debe interrumpir la partida: recursos ausentes, mezclador caído y volúmenes."""
from __future__ import annotations

import json
import os
import random

import pygame
import pytest

from yulu.audio.audio_manager import AudioManager, SoundEntry, load_manifest
from yulu.audio.soundscape import AMBIENT_PRESETS, ENDING_MUSIC, GROWLS, MUSIC_FOR_AMBIENT, ROAR, TENSION_LAYER, Soundscape
from yulu.audio.voice import voice_filename, voice_key
from yulu.narrative.scenes import SCENES
from yulu.narrative.schema import Choice, DialogueLine, Scene
from yulu.paths import AUDIO_DIR
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
    """Manifiesto real, pero directorio sin ningún archivo."""
    return AudioManager(audio_dir=tmp_path, manifest=load_manifest())


def test_missing_files_do_not_raise(silent_audio):
    assert silent_audio.play_sfx(ROAR) is False
    assert silent_audio.play_voice("nada.wav") is False
    assert silent_audio.play_music("exploracion") is False
    silent_audio.set_ambient_layers({"jungla_noche_densa": 0.8})
    silent_audio.update(0.5)
    assert silent_audio.ambient_gains() == {}


def test_unknown_id_and_broken_manifest_are_tolerated(tmp_path):
    audio = AudioManager(audio_dir=tmp_path, manifest={})
    assert audio.play_sfx("inexistente") is False
    (tmp_path / "manifest.json").write_text("{no es json", encoding="utf-8")
    assert load_manifest(tmp_path / "manifest.json") == {}


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
    assert silent_audio.volumes["music"] == pytest.approx(0.35)
    assert silent_audio.adjust_volume("ambient", -0.2) == pytest.approx(0.3)
    with pytest.raises(ValueError):
        silent_audio.set_volume("otra", 0.5)


def test_manifest_entries_have_license_metadata():
    raw = json.loads((AUDIO_DIR / "manifest.json").read_text(encoding="utf-8"))
    for item in raw["sounds"]:
        source = item["source"]
        for field in ("title", "author", "url", "license", "downloaded", "modifications"):
            assert source.get(field) not in (None, ""), f"{item['id']} sin {field}"
        if source["attribution_required"]:
            assert source["license_verified_on_page"], f"{item['id']} es CC BY y no está verificado en la página"


def test_real_assets_are_present_and_loadable():
    audio = AudioManager()
    if not audio.enabled:
        pytest.skip("mezclador no disponible")
    needed = {name for preset in AMBIENT_PRESETS.values() for name in preset}
    needed |= set(TENSION_LAYER.values()) | set(MUSIC_FOR_AMBIENT.values()) | set(ENDING_MUSIC.values()) | set(GROWLS) | {ROAR, "exploracion"}
    for sound_id in needed:
        assert audio.has(sound_id), f"falta {sound_id}"
    assert audio.play_sfx("ui_confirm")
    assert audio.play_music("exploracion")
    audio.set_ambient_layers({"jungla_noche_densa": 1.0})
    audio.update(3.0)
    assert audio.ambient_gains()["jungla_noche_densa"] == pytest.approx(1.0)
    audio.set_ambient_layers({})
    audio.update(5.0)
    assert audio.ambient_gains() == {}
    audio.shutdown()


def test_scene_change_does_not_accumulate_layers():
    audio = AudioManager()
    if not audio.enabled:
        pytest.skip("mezclador no disponible")
    scape = Soundscape(audio, rng=random.Random(5))
    for scene_id in ("s1_despertar", "s2_persecucion", "s2_claro", "s3_puerta", "s4_refugio", "s5_final_aldea"):
        scape.enter_scene(SCENES[scene_id], threat=50)
        for _ in range(80):
            scape.update(0.1, threat=50)
        active = {k for k, g in audio.ambient_gains().items() if g > 0}
        expected = {k for k, g in scape.layers_for(50).items() if g > 0}
        assert active == expected, f"{scene_id}: {active} != {expected}"
    assert audio.current_music == "exploracion"
    scape.on_ending(good=True)
    assert audio.current_music == "desenlace_aldea"
    audio.shutdown()


def test_voice_key_is_stable_and_distinct():
    a = voice_key("Narrador", "Hola")
    assert a == voice_key("Narrador", "Hola")
    assert a != voice_key("Guardia", "Hola")
    assert voice_filename(DialogueLine("Narrador", "Hola")) == a + ".wav"
    assert voice_filename(DialogueLine("Narrador", "Hola", voice_file="x.wav")) == "x.wav"


def test_soundscape_layers_follow_threat(silent_audio):
    scape = Soundscape(silent_audio, rng=random.Random(1))
    scape.enter_scene(SCENES["s2_persecucion"], threat=10)
    assert scape.layers_for(10)["tambor_persecucion"] == 0.0
    assert scape.layers_for(85)["tambor_persecucion"] == pytest.approx(1.0)
    safe = Scene("x", 4, "X", (DialogueLine("N", "x"),), ending="fin", ambient="shelter", jaguar_visible=False)
    scape.enter_scene(safe, threat=90)
    assert "tambor_persecucion" not in scape.layers_for(90)
    assert set(scape.layers_for(90)) == set(AMBIENT_PRESETS["shelter"])


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


def test_sound_entry_defaults():
    entry = SoundEntry("x", "ambient/x.mp3", "ambient")
    assert entry.gain == 1.0
    assert entry.loop is False


# ---------- voces: configuración y náhuat ----------
def test_voices_config_is_consistent():
    config = json.loads((AUDIO_DIR / "voices.json").read_text(encoding="utf-8"))
    speakers = {line.speaker for scene in SCENES.values() for line in scene.lines}
    for speaker in speakers:
        assert speaker in config["characters"], f"{speaker} sin voz configurada"
    for name, char in config["characters"].items():
        assert char["model"] in config["models"], f"{name} usa un modelo no declarado"
    for model in config["models"].values():
        assert model["file"].endswith(".onnx") and model.get("dataset_license")


def test_nahuat_lines_are_never_synthesized():
    from yulu.audio.voice import NAHUAT_DIR, is_human_recording_required

    for scene in SCENES.values():
        for line in scene.lines:
            if line.nahuat_id:
                assert is_human_recording_required(line)
                assert voice_filename(line).startswith(NAHUAT_DIR + "/")
            else:
                assert not is_human_recording_required(line)


def test_missing_optional_voice_is_silent(silent_audio, caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="yulu.audio"):
        assert silent_audio.play_voice("nahuat/yek_tunal.wav", optional=True) is False
        assert silent_audio.has_voice("nahuat/yek_tunal.wav") is False
    assert not [r for r in caplog.records if "nahuat" in r.getMessage()]
