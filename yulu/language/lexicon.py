"""Carga y consulta del vocabulario de náhuat del capítulo 1."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from yulu.paths import LANGUAGE_DATA_DIR

DEFAULT_LEXICON_PATH = LANGUAGE_DATA_DIR / "nahuat_ch1.json"
VALID_STATUSES = {"verificada", "compuesta", "provisional"}
REQUIRED_FIELDS = ("id", "nahuat", "spanish", "context", "status", "sources")


class LexiconError(Exception):
    """El archivo de vocabulario es inválido o incompleto."""


@dataclass(frozen=True)
class Source:
    ref: str
    locator: str
    citation: str


@dataclass(frozen=True)
class Expression:
    id: str
    nahuat: str
    spanish: str
    context: str
    status: str
    sources: tuple[Source, ...]
    literal: str | None = None
    pronunciation: str | None = None

    @property
    def is_playable(self) -> bool:
        """Solo se usan en la partida las expresiones verificadas o compuestas."""
        return self.status in ("verificada", "compuesta")

    @property
    def status_label(self) -> str:
        return {"verificada": "Verificada", "compuesta": "Compuesta de formas atestiguadas", "provisional": "PROVISIONAL"}[self.status]


class Lexicon:
    def __init__(self, expressions: list[Expression], meta: dict) -> None:
        self._by_id = {e.id: e for e in expressions}
        self._order = [e.id for e in expressions]
        self.meta = meta

    @classmethod
    def load(cls, path: Path = DEFAULT_LEXICON_PATH) -> "Lexicon":
        try:
            with path.open(encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise LexiconError(f"No se pudo leer {path}: {exc}") from exc
        meta = raw.get("_meta", {})
        citations: dict[str, str] = meta.get("sources", {})
        expressions = [cls._parse(item, citations) for item in raw.get("expressions", [])]
        ids = [e.id for e in expressions]
        if len(ids) != len(set(ids)):
            raise LexiconError("Identificadores de expresión duplicados")
        return cls(expressions, meta)

    @staticmethod
    def _parse(item: dict, citations: dict[str, str]) -> Expression:
        missing = [f for f in REQUIRED_FIELDS if not item.get(f)]
        if missing:
            raise LexiconError(f"Expresión {item.get('id', '?')} sin campos: {missing}")
        if item["status"] not in VALID_STATUSES:
            raise LexiconError(f"Estado desconocido en {item['id']}: {item['status']}")
        sources = []
        for src in item["sources"]:
            ref = src.get("ref", "")
            if ref not in citations:
                raise LexiconError(f"Fuente {ref!r} de {item['id']} no está declarada en _meta.sources")
            sources.append(Source(ref=ref, locator=src.get("locator", ""), citation=citations[ref]))
        return Expression(
            id=item["id"],
            nahuat=item["nahuat"],
            spanish=item["spanish"],
            context=item["context"],
            status=item["status"],
            sources=tuple(sources),
            literal=item.get("literal"),
            pronunciation=item.get("pronunciation"),
        )

    def __len__(self) -> int:
        return len(self._order)

    def __contains__(self, expression_id: str) -> bool:
        return expression_id in self._by_id

    def get(self, expression_id: str) -> Expression:
        try:
            return self._by_id[expression_id]
        except KeyError as exc:
            raise LexiconError(f"Expresión desconocida: {expression_id}") from exc

    def all(self) -> list[Expression]:
        return [self._by_id[i] for i in self._order]

    def playable_ids(self) -> set[str]:
        return {e.id for e in self.all() if e.is_playable}
