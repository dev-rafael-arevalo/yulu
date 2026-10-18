"""Motor narrativo: valida el grafo de escenas y aplica decisiones al estado."""
from __future__ import annotations

from dataclasses import dataclass

from yulu.narrative.schema import Choice, Scene
from yulu.state.game_state import GameState


class NarrativeError(Exception):
    """Error en la definición del grafo narrativo."""


class InvalidChoiceError(Exception):
    """La opción no pertenece a la escena actual o no está disponible."""


@dataclass(frozen=True)
class ChoiceResult:
    choice: Choice
    feedback: str
    next_scene: Scene
    learned: tuple[str, ...]  # expresiones nuevas registradas en esta decisión


class NarrativeEngine:
    def __init__(self, scenes: dict[str, Scene], start_scene: str) -> None:
        self._scenes = scenes
        self._start = start_scene
        self._validate()

    # ---------- validación del grafo ----------
    def _validate(self) -> None:
        if self._start not in self._scenes:
            raise NarrativeError(f"Escena inicial desconocida: {self._start}")
        for scene in self._scenes.values():
            if scene.is_ending and scene.choices:
                raise NarrativeError(f"La escena final {scene.id} no puede tener opciones")
            if not scene.is_ending and not scene.choices:
                raise NarrativeError(f"La escena {scene.id} no tiene opciones ni es final")
            if scene.timer_seconds is not None and scene.timeout_choice is None:
                raise NarrativeError(f"La escena {scene.id} tiene temporizador sin opción por defecto")
            ids = [c.id for c in scene.choices]
            if len(ids) != len(set(ids)):
                raise NarrativeError(f"Opciones duplicadas en {scene.id}")
            if scene.timeout_choice is not None and scene.timeout_choice not in ids:
                raise NarrativeError(f"timeout_choice inválido en {scene.id}")
            for choice in scene.choices:
                if choice.next_scene not in self._scenes:
                    raise NarrativeError(
                        f"{scene.id}/{choice.id} apunta a escena inexistente {choice.next_scene}"
                    )
        unreachable = set(self._scenes) - self._reachable()
        if unreachable:
            raise NarrativeError(f"Escenas inalcanzables: {sorted(unreachable)}")

    def _reachable(self) -> set[str]:
        seen: set[str] = set()
        stack = [self._start]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(c.next_scene for c in self._scenes[current].choices)
        return seen

    # ---------- consultas ----------
    @property
    def start_scene(self) -> str:
        return self._start

    def new_state(self) -> GameState:
        return GameState(scene_id=self._start)

    def scene(self, scene_id: str) -> Scene:
        try:
            return self._scenes[scene_id]
        except KeyError as exc:
            raise NarrativeError(f"Escena desconocida: {scene_id}") from exc

    def current_scene(self, state: GameState) -> Scene:
        return self.scene(state.scene_id)

    def available_choices(self, state: GameState) -> list[Choice]:
        scene = self.current_scene(state)
        return [c for c in scene.choices if c.requires_flag is None or state.has_flag(c.requires_flag)]

    def endings(self) -> set[str]:
        return {s.ending for s in self._scenes.values() if s.ending}

    # ---------- transiciones ----------
    def apply_choice(self, state: GameState, choice_id: str) -> ChoiceResult:
        if state.is_finished:
            raise InvalidChoiceError("La partida ya terminó")
        scene = self.current_scene(state)
        choice = next((c for c in self.available_choices(state) if c.id == choice_id), None)
        if choice is None:
            raise InvalidChoiceError(f"Opción {choice_id} no disponible en {scene.id}")

        effect = choice.effect
        state.add_threat(effect.threat)
        state.add_trust(effect.trust)
        learned = tuple(e for e in effect.learn if state.learn(e))
        if choice.nahuat_id:
            state.learn(choice.nahuat_id)
        state.flags.update(effect.flags)
        state.record(scene.id, choice.id)

        next_scene = self.scene(choice.next_scene)
        state.scene_id = next_scene.id
        if next_scene.is_ending:
            state.ending = next_scene.ending
        return ChoiceResult(choice=choice, feedback=choice.feedback, next_scene=next_scene, learned=learned)

    def apply_timeout(self, state: GameState) -> ChoiceResult:
        scene = self.current_scene(state)
        if scene.timeout_choice is None:
            raise InvalidChoiceError(f"La escena {scene.id} no tiene temporizador")
        return self.apply_choice(state, scene.timeout_choice)

    def restart(self) -> GameState:
        """Devuelve un estado nuevo desde la escena inicial."""
        return self.new_state()
