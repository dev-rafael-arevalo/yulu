"""Punto de entrada de YULU: La noche del jaguar.

Ejecutar desde cualquier directorio:
    python main.py            # pantalla completa
    python main.py --windowed # ventana (útil para depurar)
"""
from __future__ import annotations

import argparse
import sys

from yulu.app import run


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YULU: La noche del jaguar")
    parser.add_argument("--windowed", action="store_true", help="Abrir en ventana en lugar de pantalla completa")
    parser.add_argument(
        "--smoke-frames",
        type=int,
        default=0,
        help="Ejecutar N fotogramas y salir (uso interno para pruebas automáticas)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    sys.exit(run(windowed=args.windowed, smoke_frames=args.smoke_frames))
