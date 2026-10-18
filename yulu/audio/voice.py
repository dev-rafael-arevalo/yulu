"""Correspondencia estable entre líneas de diálogo y archivos de narración pregenerados.

- Líneas en español: `<clave>.wav`, donde la clave deriva del locutor y el texto.
- Líneas en náhuat (`nahuat_id`): `nahuat/<id>.wav`. Ese archivo solo existe si una persona
  competente en la lengua lo grabó y lo colocó ahí; nunca se sintetiza con un modelo español.
"""
from __future__ import annotations

import hashlib

from yulu.narrative.schema import DialogueLine

VOICE_EXTENSION = ".wav"
NAHUAT_DIR = "nahuat"


def voice_key(speaker: str, text: str) -> str:
    """Clave corta y determinista derivada del locutor y el texto."""
    digest = hashlib.sha1(f"{speaker}\n{text}".encode("utf-8")).hexdigest()
    return digest[:12]


def is_human_recording_required(line: DialogueLine) -> bool:
    """Las frases en náhuat solo pueden tener voz grabada por una persona."""
    return line.nahuat_id is not None and not line.voice_file


def voice_filename(line: DialogueLine) -> str:
    if line.voice_file:
        return line.voice_file
    if line.nahuat_id:
        return f"{NAHUAT_DIR}/{line.nahuat_id}{VOICE_EXTENSION}"
    return voice_key(line.speaker, line.text) + VOICE_EXTENSION
