"""Correspondencia estable entre líneas de diálogo y archivos de narración pregenerados."""
from __future__ import annotations

import hashlib

from yulu.narrative.schema import DialogueLine

VOICE_EXTENSION = ".wav"


def voice_key(speaker: str, text: str) -> str:
    """Clave corta y determinista derivada del locutor y el texto."""
    digest = hashlib.sha1(f"{speaker}\n{text}".encode("utf-8")).hexdigest()
    return digest[:12]


def voice_filename(line: DialogueLine) -> str:
    if line.voice_file:
        return line.voice_file
    return voice_key(line.speaker, line.text) + VOICE_EXTENSION
