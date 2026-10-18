"""Pruebas del vocabulario de náhuat y de su archivo de datos."""
from __future__ import annotations

import json

import pytest

from yulu.language.lexicon import DEFAULT_LEXICON_PATH, Lexicon, LexiconError


def test_lexicon_loads_between_8_and_12_expressions():
    lexicon = Lexicon.load()
    assert 8 <= len(lexicon) <= 12


def test_every_expression_has_required_fields_and_sources():
    for expression in Lexicon.load().all():
        assert expression.nahuat and expression.spanish and expression.context
        assert expression.status in ("verificada", "compuesta", "provisional")
        assert expression.sources, f"{expression.id} sin fuente"
        for source in expression.sources:
            assert source.citation and source.locator


def test_no_provisional_expressions_are_shipped():
    lexicon = Lexicon.load()
    assert lexicon.playable_ids() == {e.id for e in lexicon.all()}


def test_unknown_id_raises():
    with pytest.raises(LexiconError):
        Lexicon.load().get("no_existe")


def test_missing_field_is_rejected(tmp_path):
    raw = json.loads(DEFAULT_LEXICON_PATH.read_text(encoding="utf-8"))
    del raw["expressions"][0]["spanish"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(LexiconError, match="sin campos"):
        Lexicon.load(path)


def test_undeclared_source_is_rejected(tmp_path):
    raw = json.loads(DEFAULT_LEXICON_PATH.read_text(encoding="utf-8"))
    raw["expressions"][0]["sources"] = [{"ref": "INVENTADA", "locator": "p. 1"}]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(LexiconError, match="no está declarada"):
        Lexicon.load(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(LexiconError):
        Lexicon.load(tmp_path / "nada.json")
