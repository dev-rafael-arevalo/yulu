"""Modelos de datos puros de la narrativa. No dependen de Pygame."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DialogueLine:
    """Una línea de diálogo o narración con subtítulo y audio opcional."""

    speaker: str
    text: str
    nahuat_id: str | None = None  # expresión del léxico que se muestra o enseña
    voice_file: str | None = None  # nombre de archivo en assets/audio/voice


@dataclass(frozen=True)
class Effect:
    """Consecuencias de una decisión sobre el estado."""

    threat: int = 0
    trust: int = 0
    learn: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Choice:
    id: str
    text: str
    next_scene: str
    effect: Effect = field(default_factory=Effect)
    feedback: str = ""  # retroalimentación mostrada antes de cambiar de escena
    requires_flag: str | None = None  # solo visible si el estado tiene esta bandera
    nahuat_id: str | None = None  # expresión que el jugador pronuncia al elegir


@dataclass(frozen=True)
class Scene:
    id: str
    chapter_step: int  # 1..5, escena del capítulo a la que pertenece el nodo
    title: str
    lines: tuple[DialogueLine, ...]
    choices: tuple[Choice, ...] = ()
    timer_seconds: float | None = None  # presión temporal solo en nodos seleccionados
    timeout_choice: str | None = None  # opción aplicada automáticamente al agotarse el tiempo
    ending: str | None = None  # identificador del final si el nodo es terminal
    background: str = "forest"  # clave de escenario para la presentación
    jaguar_visible: bool = True
    ambient: str = "forest_night"  # clave de ambiente sonoro

    @property
    def is_ending(self) -> bool:
        return self.ending is not None
