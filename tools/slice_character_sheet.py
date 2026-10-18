"""Recorta la hoja de personajes (fondo negro) en PNG individuales con transparencia.

Uso:  python tools/slice_character_sheet.py <hoja.png>

Las cajas de recorte se midieron sobre la hoja `character_cutout_reference_sheet.png`
(1672×941) generada el 18/10/2026. Si se regenera la hoja con otra disposición, ajusta BOXES.
El negro se convierte en alfa con una rampa corta para que la ropa oscura quede opaca.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.paths import IMAGES_DIR  # noqa: E402

OUT_DIR = IMAGES_DIR / "characters"

# nombre -> (x0, y0, x1, y1) en píxeles de la hoja original
BOXES: dict[str, tuple[int, int, int, int]] = {
    "npc_anciana": (0, 0, 407, 405),
    "npc_guardia": (410, 0, 760, 405),
    "npc_mujer": (766, 0, 1097, 405),
    "npc_hombre": (1100, 0, 1440, 405),
    "npc_nino": (1440, 0, 1672, 405),
    "group_familia": (15, 410, 890, 665),
    "group_ninos": (906, 410, 1246, 665),
    "group_ancianas": (1261, 410, 1672, 665),
    "npc_mujer_olla": (0, 670, 282, 941),
    "group_fogata": (304, 670, 812, 941),
    "group_guardia_anciano": (830, 670, 1300, 941),
    "group_espaldas": (1300, 670, 1672, 941),
}


def black_to_alpha(cell: pygame.Surface, solid_from: int = 46, boost: float = 6.5) -> pygame.Surface:
    out = pygame.Surface(cell.get_size(), pygame.SRCALPHA)
    w, h = cell.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, *_ = cell.get_at((x, y))
            lum = max(r, g, b)
            alpha = 0 if lum < 9 else 255 if lum >= solid_from else min(255, int((lum - 8) * boost))
            out.set_at((x, y), (r, g, b, alpha))
    return out


def trim(surface: pygame.Surface, margin: int = 4) -> pygame.Surface:
    rect = surface.get_bounding_rect(min_alpha=8).inflate(margin * 2, margin * 2).clip(surface.get_rect())
    return surface.subsurface(rect).copy()


def main(sheet_path: str) -> int:
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = pygame.image.load(sheet_path).convert_alpha()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (x0, y0, x1, y1) in BOXES.items():
        cell = sheet.subsurface(pygame.Rect(x0, y0, x1 - x0, y1 - y0)).copy()
        sprite = trim(black_to_alpha(cell))
        target = OUT_DIR / f"{name}.png"
        pygame.image.save(sprite, str(target))
        print(f"  {name:<24} {sprite.get_width()}x{sprite.get_height()}")
    print(f"\n{len(BOXES)} personajes en {OUT_DIR}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
