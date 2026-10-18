"""Pruebas del capítulo real: finales, ramas automáticas y coherencia con el léxico."""
from __future__ import annotations

import pytest

from yulu.language.lexicon import Lexicon
from yulu.narrative.scenes import SCENES, START_SCENE
from yulu.narrative.schema import Branch, Choice, DialogueLine, Scene
from yulu.state.engine import InvalidChoiceError, NarrativeEngine, NarrativeError

GOOD_ENDING = "amanecer_aldea"
BAD_ENDING = "amanecer_solo"


@pytest.fixture
def engine() -> NarrativeEngine:
    return NarrativeEngine(SCENES, START_SCENE, known_expressions=Lexicon.load().playable_ids())


def play(engine: NarrativeEngine, choices: list[str]):
    """Aplica una secuencia de opciones resolviendo ramas automáticas por el camino."""
    state = engine.new_state()
    for choice_id in choices:
        while engine.current_scene(state).is_automatic:
            engine.resolve_branch(state)
        engine.apply_choice(state, choice_id)
    while not state.is_finished and engine.current_scene(state).is_automatic:
        engine.resolve_branch(state)
    return state


BEST_PATH = ["escuchar", "tambor", "rio", "salir", "acercarse", "repetir", "yek_tayua", "nombre", "tekwani",
             "ninemi_yek", "padiush", "shinechpalewi", "padiush"]
WORST_PATH = ["gritar", "correr", "correr", "antorchas", "acercarse", "gritar", "silencio", "callar", "huir",
              "correr", "tay", "te", "pedir_mas", "esconderse", "esperar"]


def test_chapter_has_exactly_two_endings(engine):
    assert engine.endings() == {GOOD_ENDING, BAD_ENDING}


def test_best_path_reaches_village_ending(engine):
    state = play(engine, BEST_PATH)
    assert state.ending == GOOD_ENDING
    assert state.trust >= 40
    assert len(state.vocabulary) >= 8


def test_worst_path_reaches_lonely_ending(engine):
    state = play(engine, WORST_PATH)
    assert state.ending == BAD_ENDING
    assert state.trust < 40


def test_wrong_answers_still_teach_and_allow_progress(engine):
    state = play(engine, ["escuchar", "tambor", "ceiba", "bajar", "acercarse", "gritar", "yek_tunal", "ninemi"])
    assert state.scene_id == "s3_nombre_otra_vez"
    assert state.knows("ken_mutukay") and state.knows("yek_tayua")
    engine.apply_choice(state, "nombre")
    assert state.scene_id == "s3_tekwani"


def test_timed_scenes_are_only_the_selected_ones(engine):
    timed = {s.id for s in SCENES.values() if s.timer_seconds is not None}
    assert timed == {"s2_persecucion", "s3_tekwani", "s4_alarma"}


def test_every_nahuat_line_uses_known_expression():
    ids = Lexicon.load().playable_ids()
    for scene in SCENES.values():
        for line in scene.lines:
            if line.nahuat_id:
                assert line.nahuat_id in ids, f"{scene.id}: {line.nahuat_id}"


def test_all_expressions_are_learnable_in_chapter():
    learnable: set[str] = set()
    for scene in SCENES.values():
        for choice in scene.choices:
            learnable.update(choice.effect.learn)
            if choice.nahuat_id:
                learnable.add(choice.nahuat_id)
    assert Lexicon.load().playable_ids() <= learnable


def test_unknown_expression_in_scene_is_rejected():
    bad = {
        "a": Scene("a", 1, "A", (DialogueLine("N", "x", nahuat_id="no_existe"),), ending="fin"),
    }
    with pytest.raises(NarrativeError, match="desconocida"):
        NarrativeEngine(bad, "a", known_expressions={"yek_tunal"})


# ---------- ramas automáticas ----------
def _branch_graph(branches: tuple[Branch, ...]) -> dict[str, Scene]:
    return {
        "inicio": Scene("inicio", 1, "I", (DialogueLine("N", "x"),), (Choice("ir", "Ir", "cruce"),)),
        "cruce": Scene("cruce", 5, "C", (DialogueLine("N", "x"),), branches=branches),
        "bueno": Scene("bueno", 5, "B", (DialogueLine("N", "x"),), ending="bueno"),
        "malo": Scene("malo", 5, "M", (DialogueLine("N", "x"),), ending="malo"),
    }


def test_branch_picks_first_matching_condition():
    engine = NarrativeEngine(_branch_graph((Branch("bueno", min_trust=40), Branch("malo"))), "inicio")
    state = engine.new_state()
    engine.apply_choice(state, "ir")
    state.trust = 55
    assert engine.resolve_branch(state).id == "bueno"
    assert state.ending == "bueno"
    low = engine.new_state()
    engine.apply_choice(low, "ir")
    assert engine.resolve_branch(low).id == "malo"


def test_branch_graph_requires_default_branch():
    with pytest.raises(NarrativeError, match="incondicional"):
        NarrativeEngine(_branch_graph((Branch("bueno", min_trust=40),)), "inicio")


def test_resolve_branch_on_choice_scene_raises():
    engine = NarrativeEngine(_branch_graph((Branch("bueno", min_trust=40), Branch("malo"))), "inicio")
    with pytest.raises(InvalidChoiceError):
        engine.resolve_branch(engine.new_state())
