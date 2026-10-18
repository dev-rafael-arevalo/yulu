"""Corta una cuadrícula de recursos generada por IA en los archivos que espera el manifiesto.

Uso:
    python tools/slice_asset_grid.py "yulu/assets/images/Cinematic Jungle Village Asset Grid.png"

Disposición esperada (de izquierda a derecha, de arriba abajo):
    fila 1: bosque del despertar, sendero de la persecución, sendero hacia la aldea
    fila 2: puerta de la aldea, interior del refugio, amanecer
    fila 3: ojos del jaguar, jaguar acechando, jaguar saltando (fondo negro)
    fila 4: niebla 1, niebla 2, humo (fondo negro)

Las celdas con fondo negro se convierten a PNG con transparencia derivada de la luminancia.
Los separadores claros de la cuadrícula se detectan automáticamente.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.paths import IMAGES_DIR  # noqa: E402
from yulu.ui.assets import load_manifest  # noqa: E402

SEPARATOR_BRIGHTNESS = 150  # media de un píxel (0-255) a partir de la cual se considera línea divisoria
MIN_CELL = 80  # ancho o alto mínimo de una celda en píxeles


def _bright_lines(surface: pygame.Surface, axis: str) -> list[int]:
    """Índices de filas (axis='y') o columnas (axis='x') casi completamente claras."""
    w, h = surface.get_size()
    lines: list[int] = []
    length, span = (h, w) if axis == "y" else (w, h)
    step = max(1, span // 200)
    for i in range(length):
        total = 0
        count = 0
        for j in range(0, span, step):
            r, g, b, *_ = surface.get_at((j, i) if axis == "y" else (i, j))
            total += (r + g + b) // 3
            count += 1
        if total / count > SEPARATOR_BRIGHTNESS:
            lines.append(i)
    return lines


def _segments(length: int, separators: list[int]) -> list[tuple[int, int]]:
    """Convierte posiciones de separadores en intervalos [inicio, fin) de celdas."""
    cuts = [-1, *separators, length]
    segments: list[tuple[int, int]] = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a - 1 >= MIN_CELL:
            segments.append((a + 1, b))
    return segments


def _row_segments(surface: pygame.Surface, y0: int, y1: int) -> list[tuple[int, int]]:
    band = surface.subsurface(pygame.Rect(0, y0, surface.get_width(), y1 - y0))
    return _segments(band.get_width(), _bright_lines(band, "x"))


def _black_to_alpha(cell: pygame.Surface, boost: float, solid_from: int = 255, transparent_below: int = 10) -> pygame.Surface:
    """Alfa derivado de la luminancia: el negro puro se vuelve transparente.

    `boost` escala la rampa; a partir de `solid_from` el píxel es totalmente opaco, lo que
    evita que el pelaje oscuro de un animal quede translúcido.
    """
    out = pygame.Surface(cell.get_size(), pygame.SRCALPHA)
    w, h = cell.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, *_ = cell.get_at((x, y))
            lum = max(r, g, b)
            if lum < transparent_below:
                alpha = 0
            elif lum >= solid_from:
                alpha = 255
            else:
                alpha = min(255, int((lum - transparent_below + 1) * boost))
            out.set_at((x, y), (r, g, b, alpha))
    return out


def _feather_edges(surface: pygame.Surface, fraction: float = 0.12) -> pygame.Surface:
    """Desvanece el alfa hacia los bordes de la celda para que la niebla pintada no deje un recuadro."""
    w, h = surface.get_size()
    mx, my = max(1, int(w * fraction)), max(1, int(h * fraction))
    for y in range(h):
        fy = min(1.0, y / my, (h - 1 - y) / my)
        for x in range(w):
            fx = min(1.0, x / mx, (w - 1 - x) / mx)
            k = min(fx, fy)
            if k < 1.0:
                r, g, b, a = surface.get_at((x, y))
                surface.set_at((x, y), (r, g, b, int(a * k * k)))
    return surface


def _trim(surface: pygame.Surface, margin: int = 6) -> pygame.Surface:
    rect = surface.get_bounding_rect(min_alpha=8)
    rect = rect.inflate(margin * 2, margin * 2).clip(surface.get_rect())
    return surface.subsurface(rect).copy()


def main(grid_path: str) -> int:
    pygame.init()
    pygame.display.set_mode((1, 1))
    grid = pygame.image.load(grid_path).convert_alpha()
    manifest = load_manifest()
    backgrounds = manifest["backgrounds"]
    overlays = manifest["overlays"]

    rows = _segments(grid.get_height(), _bright_lines(grid, "y"))
    if len(rows) != 4:
        print(f"Se esperaban 4 filas y se detectaron {len(rows)}: {rows}")
        return 1

    plan = [
        [(backgrounds[k]["file"], "opaque") for k in ("forest_dense", "forest_path", "village_edge")],
        [(backgrounds[k]["file"], "opaque") for k in ("village_gate", "shelter", "dawn")],
        [],  # fila del jaguar: no se usa (el jaguar del juego viene del paquete de personajes, ver tools/prepare_cutouts.py)
        [(overlays["fog"][0], "fog"), (overlays["fog"][1], "fog"), (overlays["smoke"], "fog")],
    ]
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for (y0, y1), row_plan in zip(rows, plan):
        if not row_plan:
            continue
        cols = _row_segments(grid, y0, y1)
        if len(cols) != len(row_plan):
            print(f"Fila {y0}-{y1}: se esperaban {len(row_plan)} celdas y se detectaron {len(cols)}: {cols}")
            return 1
        for (x0, x1), (filename, kind) in zip(cols, row_plan):
            cell = grid.subsurface(pygame.Rect(x0, y0, x1 - x0, y1 - y0)).copy()
            if kind == "jaguar":
                # El fondo de las celdas del jaguar no es negro puro (gris muy oscuro): todo lo que esté por
                # debajo de 26 se hace transparente para no arrastrar un recuadro gris alrededor del animal.
                cell = _trim(_feather_edges(_black_to_alpha(cell, boost=11.0, solid_from=50, transparent_below=26)))
            elif kind == "fog":
                cell = _black_to_alpha(cell, boost=1.0)
            target = IMAGES_DIR / filename
            pygame.image.save(cell, str(target))
            print(f"  {filename:<34} {cell.get_width()}x{cell.get_height()}  <- celda ({x0},{y0})-({x1},{y1})")
    print("\nListo. Ejecuta tools/check_assets.py para confirmar.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
