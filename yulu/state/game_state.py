"""Estado de la partida, separado por completo de la presentación."""
from __future__ import annotations

from dataclasses import dataclass, field

from yulu import config


def clamp(value: int, low: int = config.METER_MIN, high: int = config.METER_MAX) -> int:
    return max(low, min(high, value))


@dataclass
class Decision:
    scene_id: str
    choice_id: str


@dataclass
class GameState:
    scene_id: str
    threat: int = config.THREAT_START
    trust: int = config.TRUST_START
    vocabulary: list[str] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    ending: str | None = None

    def add_threat(self, delta: int) -> None:
        self.threat = clamp(self.threat + delta)

    def add_trust(self, delta: int) -> None:
        self.trust = clamp(self.trust + delta)

    def learn(self, expression_id: str) -> bool:
        """Registra una expresión aprendida. Devuelve True si es nueva."""
        if expression_id in self.vocabulary:
            return False
        self.vocabulary.append(expression_id)
        return True

    def knows(self, expression_id: str) -> bool:
        return expression_id in self.vocabulary

    def record(self, scene_id: str, choice_id: str) -> None:
        self.decisions.append(Decision(scene_id, choice_id))

    def has_flag(self, flag: str) -> bool:
        return flag in self.flags

    @property
    def is_finished(self) -> bool:
        return self.ending is not None

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "threat": self.threat,
            "trust": self.trust,
            "vocabulary": list(self.vocabulary),
            "decisions": [(d.scene_id, d.choice_id) for d in self.decisions],
            "flags": sorted(self.flags),
            "ending": self.ending,
        }
