"""Valida el manifiesto de audio: archivos presentes, decodificables y con metadatos de licencia.

Uso:  python tools/check_audio.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.audio.soundscape import AMBIENT_PRESETS, ENDING_MUSIC, GROWLS, MOVEMENT, MUSIC_FOR_AMBIENT, ROAR, TENSION_LAYER  # noqa: E402
from yulu.paths import AUDIO_DIR  # noqa: E402

REQUIRED_SOURCE_FIELDS = ("title", "author", "url", "license", "license_url", "attribution_required", "license_verified_on_page", "downloaded", "modifications")


def main() -> int:
    pygame.mixer.init(frequency=44100)
    manifest = json.loads((AUDIO_DIR / "manifest.json").read_text(encoding="utf-8"))
    problems = 0
    ids: set[str] = set()
    print(f"Directorio: {AUDIO_DIR}\n")
    for item in manifest["sounds"]:
        ids.add(item["id"])
        path = AUDIO_DIR / item["file"]
        status = "OK"
        length = 0.0
        if not path.is_file():
            status = "FALTA"
        else:
            try:
                length = pygame.mixer.Sound(str(path)).get_length()
            except pygame.error as exc:
                status = f"NO DECODIFICA ({exc})"
        missing_meta = [f for f in REQUIRED_SOURCE_FIELDS if f not in item.get("source", {})]
        if missing_meta:
            status += f" | metadatos ausentes: {missing_meta}"
        if item["source"].get("attribution_required") and not item["source"].get("license_verified_on_page"):
            status += " | CC BY sin verificar en página"
        if status != "OK":
            problems += 1
        print(f"  [{'OK' if status == 'OK' else '!!'}] {item['id']:<24} {item['file']:<36} {length:6.1f}s  {status}")

    used = set()
    for preset in AMBIENT_PRESETS.values():
        used.update(preset)
    used.update(TENSION_LAYER.values())
    used.update(MUSIC_FOR_AMBIENT.values())
    used.update(ENDING_MUSIC.values())
    used.update(GROWLS)
    used.update({MOVEMENT, ROAR, "ui_move", "ui_confirm", "learn_chime", "tick", "pasos_hojarasca", "exploracion"})
    unknown = sorted(used - ids)
    if unknown:
        problems += len(unknown)
        print(f"\nIdentificadores usados por el código que no están en el manifiesto: {unknown}")
    unused = sorted(ids - used)
    if unused:
        print(f"\nEntradas del manifiesto sin uso en el código (informativo): {unused}")
    print(f"\n{len(ids)} sonidos, {problems} problemas.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
