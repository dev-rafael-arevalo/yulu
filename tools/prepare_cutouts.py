"""Convierte los recortes sobre fondo NEGRO del paquete de personajes y jaguares en PNG con
transparencia revisada, y genera una hoja de control sobre damero para verificar bordes.

Uso:  python tools/prepare_cutouts.py <carpeta_del_paquete/assets/images> [--check <salida.png>]

Reglas de la conversión (ver yulu/assets/images/README.md):
- El fondo se detecta por relleno desde los bordes sobre píxeles oscuros, de modo que las
  manchas negras interiores (rosetas, pelo, sombras) quedan opacas.
- Solo se conserva la figura conectada más grande: los fragmentos del personaje vecino que
  arrastran algunos recortes desaparecen.
- SOURCES admite un recorte previo en píxeles por archivo si hiciera falta.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.paths import IMAGES_DIR  # noqa: E402

OUT_DIR = IMAGES_DIR / "cast"

# nombre de salida -> (archivo de origen, (recorte izquierda, arriba, derecha, abajo) en px)
SOURCES: dict[str, tuple[str, tuple[int, int, int, int]]] = {
    "anciana": ("npc_anciana_fondo_negro.png", (0, 0, 0, 0)),
    "anciano": ("npc_anciano_fondo_negro.png", (0, 0, 18, 0)),
    "guardia_lider": ("npc_guardia_lider_fondo_negro.png", (0, 0, 0, 0)),
    "joven_guardia": ("npc_joven_guardia_fondo_negro.png", (14, 0, 0, 0)),
    "hombre": ("npc_hombre_fondo_negro.png", (0, 0, 0, 0)),
    "mujer": ("npc_mujer_fondo_negro.png", (0, 0, 36, 0)),
    "mujer_joven": ("npc_mujer_joven_fondo_negro.png", (0, 0, 22, 0)),
    "nino": ("npc_nino_fondo_negro.png", (0, 0, 42, 0)),
    "jaguar_acecho": ("jaguar_acecho_fondo_negro.png", (0, 0, 0, 0)),
    "jaguar_acecho_alt": ("jaguar_acecho_alternativo_fondo_negro.png", (30, 0, 0, 0)),
    "jaguar_ataque": ("jaguar_ataque_fondo_negro.png", (0, 0, 0, 0)),
    "jaguar_retrato": ("jaguar_retrato_fondo_negro.png", (0, 0, 0, 0)),
}
SOLID_FROM = 34  # luminancia máxima del fondo negro conectado con el borde


def _lum_grid(cell: pygame.Surface) -> list[list[int]]:
    w, h = cell.get_size()
    return [[max(cell.get_at((x, y))[:3]) for x in range(w)] for y in range(h)]


def _flood_background(lum: list[list[int]], threshold: int) -> list[list[bool]]:
    """Marca como fondo los píxeles oscuros conectados con el borde de la imagen.

    Las manchas oscuras interiores (rosetas del jaguar, pelo, sombras de la ropa) no tocan
    el borde a través de fondo oscuro continuo, así que permanecen opacas.
    """
    h, w = len(lum), len(lum[0])
    background = [[False] * w for _ in range(h)]
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h) or background[y][x] or lum[y][x] >= threshold:
            continue
        background[y][x] = True
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return background


def _largest_component(opaque: list[list[bool]]) -> list[list[bool]]:
    """Conserva solo el grupo conectado de píxeles opacos más grande (la figura principal)."""
    h, w = len(opaque), len(opaque[0])
    seen = [[False] * w for _ in range(h)]
    best: list[tuple[int, int]] = []
    for sy in range(h):
        for sx in range(w):
            if opaque[sy][sx] and not seen[sy][sx]:
                comp, stack = [], [(sx, sy)]
                seen[sy][sx] = True
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and opaque[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                if len(comp) > len(best):
                    best = comp
    keep = [[False] * w for _ in range(h)]
    for x, y in best:
        keep[y][x] = True
    return keep


def black_to_alpha(cell: pygame.Surface) -> pygame.Surface:
    """Fondo por relleno desde los bordes + figura principal + borde suavizado de 1 px."""
    w, h = cell.get_size()
    lum = _lum_grid(cell)
    background = _flood_background(lum, SOLID_FROM)
    opaque = [[not background[y][x] for x in range(w)] for y in range(h)]
    keep = _largest_component(opaque)
    out = pygame.Surface(cell.get_size(), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            r, g, b, *_ = cell.get_at((x, y))
            if not keep[y][x]:
                alpha = 0
            else:
                edge = any(not keep[ny][nx] for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if 0 <= nx < w and 0 <= ny < h)
                alpha = max(90, min(255, int(255 * lum[y][x] / SOLID_FROM))) if edge else 255
            out.set_at((x, y), (r, g, b, alpha))
    return out


def trim(surface: pygame.Surface, margin: int = 2) -> pygame.Surface:
    rect = surface.get_bounding_rect(min_alpha=8).inflate(margin * 2, margin * 2).clip(surface.get_rect())
    return surface.subsurface(rect).copy()


def checker_sheet(sprites: list[tuple[str, pygame.Surface]], height: int = 360) -> pygame.Surface:
    scaled = [(n, pygame.transform.smoothscale(s, (max(1, int(height * s.get_width() / s.get_height())), height))) for n, s in sprites]
    width = sum(s.get_width() + 12 for _, s in scaled)
    sheet = pygame.Surface((width, height + 24))
    for y in range(0, height + 24, 16):
        for x in range(0, width, 16):
            pygame.draw.rect(sheet, (150, 150, 150) if (x // 16 + y // 16) % 2 else (90, 90, 90), (x, y, 16, 16))
    font = pygame.font.Font(None, 18)
    x = 0
    for name, s in scaled:
        sheet.blit(s, (x, 0))
        sheet.blit(font.render(name, True, (255, 255, 0)), (x, height + 4))
        x += s.get_width() + 12
    return sheet


def main(src_dir: str, check_path: str | None) -> int:
    pygame.init()
    pygame.display.set_mode((1, 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, pygame.Surface]] = []
    for name, (filename, (left, top, right, bottom)) in SOURCES.items():
        path = Path(src_dir) / filename
        if not path.is_file():
            print(f"  FALTA {filename}")
            continue
        raw = pygame.image.load(str(path)).convert_alpha()
        w, h = raw.get_size()
        cell = raw.subsurface(pygame.Rect(left, top, w - left - right, h - top - bottom)).copy()
        sprite = trim(black_to_alpha(cell))
        pygame.image.save(sprite, str(OUT_DIR / f"{name}.png"))
        results.append((name, sprite))
        print(f"  {name:<18} {sprite.get_width()}x{sprite.get_height()}")
    if check_path:
        pygame.image.save(checker_sheet(results), check_path)
        print(f"Hoja de control: {check_path}")
    print(f"\n{len(results)} recortes en {OUT_DIR}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    out = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    raise SystemExit(main(sys.argv[1], out))
