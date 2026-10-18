"""Pruebas del motor narrativo y del estado. No requieren Pygame."""
from __future__ import annotations

import pytest

from yulu import config
from yulu.narrative.schema import Choice, DialogueLine, Effect, Scene
from yulu.narrative.scenes import SCENES, START_SCENE
from yulu.state.engine import InvalidChoiceError, NarrativeEngine, NarrativeError


def _line(text: str = "...") -> tuple[DialogueLine, ...]:
    return (DialogueLine("Narrador", text),)


def _mini_graph() -> dict[str, Scene]:
    return {
        "inicio": Scene(
            id="inicio",
            chapter_step=1,
            title="Inicio",
            lines=_line(),
            timer_seconds=5.0,
            timeout_choice="esperar",
            choices=(
                Choice("hablar", "Hablar", "medio", Effect(trust=10, learn=("yek",)), nahuat_id="yek"),
                Choice("esperar", "Esperar", "medio", Effect(threat=20)),
                Choice("secreto", "Secreto", "bueno", requires_flag="llave"),
                Choice("llave", "Tomar llave", "inicio", Effect(flags=("llave",))),
            ),
        ),
        "medio": Scene(
            id="medio",
            chapter_step=2,
            title="Medio",
            lines=_line(),
            choices=(
                Choice("bien", "Bien", "bueno", Effect(trust=50)),
                Choice("mal", "Mal", "malo", Effect(threat=90)),
            ),
        ),
        "bueno": Scene(id="bueno", chapter_step=5, title="Bueno", lines=_line(), ending="amanecer"),
        "malo": Scene(id="malo", chapter_step=5, title="Malo", lines=_line(), ending="noche"),
    }


@pytest.fixture
def engine() -> NarrativeEngine:
    return NarrativeEngine(_mini_graph(), "inicio")


# ---------- validación ----------
def test_rejects_unknown_start():
    with pytest.raises(NarrativeError):
        NarrativeEngine(_mini_graph(), "nada")


def test_rejects_dangling_choice():
    graph = _mini_graph()
    graph["medio"] = Scene("medio", 2, "Medio", _line(), (Choice("x", "x", "no_existe"),))
    with pytest.raises(NarrativeError, match="inexistente"):
        NarrativeEngine(graph, "inicio")


def test_rejects_unreachable_scene():
    graph = _mini_graph()
    graph["isla"] = Scene("isla", 1, "Isla", _line(), ending="isla")
    with pytest.raises(NarrativeError, match="inalcanzables"):
        NarrativeEngine(graph, "inicio")


def test_rejects_ending_with_choices():
    graph = _mini_graph()
    graph["bueno"] = Scene("bueno", 5, "B", _line(), (Choice("x", "x", "inicio"),), ending="amanecer")
    with pytest.raises(NarrativeError, match="final"):
        NarrativeEngine(graph, "inicio")


def test_rejects_timer_without_timeout_choice():
    graph = _mini_graph()
    graph["medio"] = Scene("medio", 2, "M", _line(), (Choice("x", "x", "bueno"),), timer_seconds=3.0)
    with pytest.raises(NarrativeError, match="temporizador"):
        NarrativeEngine(graph, "inicio")


# ---------- decisiones ----------
def test_apply_choice_updates_state(engine):
    state = engine.new_state()
    result = engine.apply_choice(state, "hablar")
    assert state.scene_id == "medio"
    assert state.trust == config.TRUST_START + 10
    assert state.vocabulary == ["yek"]
    assert result.learned == ("yek",)
    assert [(d.scene_id, d.choice_id) for d in state.decisions] == [("inicio", "hablar")]


def test_invalid_choice_raises_and_leaves_state_untouched(engine):
    state = engine.new_state()
    with pytest.raises(InvalidChoiceError):
        engine.apply_choice(state, "bien")  # pertenece a otra escena
    assert state.scene_id == "inicio"
    assert state.decisions == []


def test_flag_gated_choice_hidden_until_flag(engine):
    state = engine.new_state()
    assert "secreto" not in [c.id for c in engine.available_choices(state)]
    with pytest.raises(InvalidChoiceError):
        engine.apply_choice(state, "secreto")
    engine.apply_choice(state, "llave")
    assert "secreto" in [c.id for c in engine.available_choices(state)]
    engine.apply_choice(state, "secreto")
    assert state.ending == "amanecer"


def test_meters_are_clamped(engine):
    state = engine.new_state()
    engine.apply_choice(state, "esperar")
    engine.apply_choice(state, "mal")
    assert state.threat == config.METER_MAX


def test_timeout_applies_default_choice(engine):
    state = engine.new_state()
    result = engine.apply_timeout(state)
    assert result.choice.id == "esperar"
    assert state.threat == config.THREAT_START + 20


def test_timeout_on_scene_without_timer_raises(engine):
    state = engine.new_state()
    engine.apply_choice(state, "hablar")
    with pytest.raises(InvalidChoiceError):
        engine.apply_timeout(state)


def test_both_endings_reachable(engine):
    good = engine.new_state()
    engine.apply_choice(good, "hablar")
    engine.apply_choice(good, "bien")
    bad = engine.new_state()
    engine.apply_choice(bad, "hablar")
    engine.apply_choice(bad, "mal")
    assert (good.ending, bad.ending) == ("amanecer", "noche")
    assert engine.endings() == {"amanecer", "noche"}


def test_no_choices_after_ending(engine):
    state = engine.new_state()
    engine.apply_choice(state, "hablar")
    engine.apply_choice(state, "bien")
    with pytest.raises(InvalidChoiceError):
        engine.apply_choice(state, "bien")


def test_restart_gives_fresh_state(engine):
    state = engine.new_state()
    engine.apply_choice(state, "hablar")
    fresh = engine.restart()
    assert fresh.scene_id == "inicio"
    assert fresh.vocabulary == [] and fresh.decisions == [] and fresh.ending is None
    assert fresh is not state


def test_learn_is_idempotent(engine):
    state = engine.new_state()
    assert state.learn("yek") is True
    assert state.learn("yek") is False
    assert state.vocabulary == ["yek"]


# ---------- grafo real del capítulo ----------
def test_chapter_graph_is_valid():
    engine = NarrativeEngine(SCENES, START_SCENE)
    assert engine.current_scene(engine.new_state()).chapter_step == 1


def test_chapter_every_path_terminates():
    """Recorre todas las rutas desde el inicio y comprueba que ninguna forma un bucle sin final."""
    engine = NarrativeEngine(SCENES, START_SCENE)
    visited: set[str] = set()
    stack = [START_SCENE]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        scene = engine.scene(current)
        stack.extend(c.next_scene for c in scene.choices)
        stack.extend(b.next_scene for b in scene.branches)
    endings_seen = {engine.scene(s).ending for s in visited if engine.scene(s).is_ending}
    assert endings_seen == engine.endings()
