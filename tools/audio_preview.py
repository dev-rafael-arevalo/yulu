"""Reproductor de prueba: escucha un sonido del manifiesto o la mezcla de una escena.

Uso:
    python tools/audio_preview.py --list
    python tools/audio_preview.py --id jaguar_sierra
    python tools/audio_preview.py --scene s2_persecucion --threat 70 --seconds 20
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.audio.audio_manager import AudioManager  # noqa: E402
from yulu.audio.soundscape import Soundscape  # noqa: E402
from yulu.narrative.scenes import SCENES  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="Listar identificadores del manifiesto")
    parser.add_argument("--id", help="Reproducir un sonido por identificador")
    parser.add_argument("--scene", help="Reproducir la mezcla de una escena (id de escena)")
    parser.add_argument("--threat", type=int, default=40, help="Nivel de amenaza para la mezcla de escena")
    parser.add_argument("--seconds", type=float, default=12.0, help="Duración de la escucha")
    args = parser.parse_args()

    pygame.init()
    audio = AudioManager()
    if not audio.enabled:
        print("No hay dispositivo de audio disponible.")
        return 1
    if args.list:
        for category in ("ambient", "creatures", "effects", "music", "ui"):
            print(f"{category}: {', '.join(audio.ids(category))}")
        return 0
    if args.id:
        entry = audio.entry(args.id)
        if entry is None:
            print(f"Identificador desconocido: {args.id}")
            return 1
        if entry.category == "music":
            audio.play_music(args.id, fade_ms=500)
        elif entry.loop:
            audio.set_ambient_layers({args.id: 1.0})
        else:
            audio.play_sfx(args.id, vary=False, pan=0.0)
        print(f"Reproduciendo {args.id} ({entry.file}) durante {args.seconds:.0f} s...")
    elif args.scene:
        scene = SCENES.get(args.scene)
        if scene is None:
            print(f"Escena desconocida. Opciones: {', '.join(SCENES)}")
            return 1
        scape = Soundscape(audio)
        scape.enter_scene(scene, args.threat)
        print(f"Mezcla de {scene.id} (ambiente {scene.ambient}, amenaza {args.threat}) durante {args.seconds:.0f} s...")
        print("Capas:", scape.layers_for(args.threat))
    else:
        parser.print_help()
        return 2

    clock = pygame.time.Clock()
    elapsed = 0.0
    while elapsed < args.seconds:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        if args.scene:
            scape.update(dt, args.threat)
        else:
            audio.update(dt)
    audio.shutdown()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
