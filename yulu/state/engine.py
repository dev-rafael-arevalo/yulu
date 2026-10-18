"""Motor narrativo: valida el grafo de escenas y aplica decisiones al estado."""
from __future__ import annotations

from dataclasses import dataclass

from yulu.narrative.schema import Branch, Choice, Scene
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
    threat_delta: int = 0


class NarrativeEngine:
    def __init__(self, scenes: dict[str, Scene], start_scene: str, known_expressions: set[str] | None = None) -> None:
        self._scenes = scenes
        self._start = start_scene
        self._known_expressions = known_expressions
        self._validate()

    # ---------- validación del grafo ----------
    def _validate(self) -> None:
        if self._start not in self._scenes:
            raise NarrativeError(f"Escena inicial desconocida: {self._start}")
        for scene in self._scenes.values():
            self._validate_scene(scene)
        unreachable = set(self._scenes) - self._reachable()
        if unreachable:
            raise NarrativeError(f"Escenas inalcanzables: {sorted(unreachable)}")

    def _validate_scene(self, scene: Scene) -> None:
        if not scene.lines:
            raise NarrativeError(f"La escena {scene.id} no tiene líneas de diálogo")
        kinds = sum(1 for flag in (scene.is_ending, bool(scene.choices), bool(scene.branches)) if flag)
        if kinds != 1:
            raise NarrativeError(f"La escena {scene.id} debe ser final, tener opciones o tener ramas (solo una cosa)")
        if scene.timer_seconds is not None and scene.timeout_choice is None:
            raise NarrativeError(f"La escena {scene.id} tiene temporizador sin opción por defecto")
        ids = [c.id for c in scene.choices]
        if len(ids) != len(set(ids)):
            raise NarrativeError(f"Opciones duplicadas en {scene.id}")
        if scene.timeout_choice is not None and scene.timeout_choice not in ids:
            raise NarrativeError(f"timeout_choice inválido en {scene.id}")
        for choice in scene.choices:
            self._check_target(scene, choice.id, choice.next_scene)
            self._check_expressions(scene, choice.id, (choice.nahuat_id, *choice.effect.learn))
        if scene.branches:
            if not scene.branches[-1].is_default:
                raise NarrativeError(f"La última rama de {scene.id} debe ser incondicional")
            for branch in scene.branches:
                self._check_target(scene, "rama", branch.next_scene)
        for line in scene.lines:
            self._check_expressions(scene, "línea", (line.nahuat_id,))

    def _check_target(self, scene: Scene, origin: str, target: str) -> None:
        if target not in self._scenes:
            raise NarrativeError(f"{scene.id}/{origin} apunta a escena inexistente {target}")

    def _check_expressions(self, scene: Scene, origin: str, ids: tuple[str | None, ...]) -> None:
        if self._known_expressions is None:
            return
        for expression_id in ids:
            if expression_id and expression_id not in self._known_expressions:
                raise NarrativeError(f"{scene.id}/{origin} usa la expresión desconocida {expression_id}")

    def _reachable(self) -> set[str]:
        seen: set[str] = set()
        stack = [self._start]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            scene = self._scenes[current]
            stack.extend(c.next_scene for c in scene.choices)
            stack.extend(b.next_scene for b in scene.branches)
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
        before = state.threat
        state.add_threat(effect.threat)
        state.add_trust(effect.trust)
        learned = tuple(e for e in effect.learn if state.learn(e))
        if choice.nahuat_id and state.learn(choice.nahuat_id):
            learned += (choice.nahuat_id,)
        state.flags.update(effect.flags)
        state.record(scene.id, choice.id)

        next_scene = self._move(state, choice.next_scene)
        return ChoiceResult(
            choice=choice, feedback=choice.feedback, next_scene=next_scene, learned=learned, threat_delta=state.threat - before
        )

    def apply_timeout(self, state: GameState) -> ChoiceResult:
        scene = self.current_scene(state)
        if scene.timeout_choice is None:
            raise InvalidChoiceError(f"La escena {scene.id} no tiene temporizador")
        return self.apply_choice(state, scene.timeout_choice)

    def resolve_branch(self, state: GameState) -> Scene:
        """Aplica la primera rama cuyas condiciones cumple el estado."""
        scene = self.current_scene(state)
        if not scene.branches:
            raise InvalidChoiceError(f"La escena {scene.id} no tiene ramas automáticas")
        branch = next(b for b in scene.branches if self._branch_matches(b, state))
        state.record(scene.id, f"auto:{branch.next_scene}")
        return self._move(state, branch.next_scene)

    @staticmethod
    def _branch_matches(branch: Branch, state: GameState) -> bool:
        if state.trust < branch.min_trust or state.threat > branch.max_threat:
            return False
        return branch.requires_flag is None or state.has_flag(branch.requires_flag)

    def _move(self, state: GameState, scene_id: str) -> Scene:
        next_scene = self.scene(scene_id)
        state.scene_id = next_scene.id
        if next_scene.is_ending:
            state.ending = next_scene.ending
        return next_scene

    def restart(self) -> GameState:
        """Devuelve un estado nuevo desde la escena inicial."""
        return self.new_state()
