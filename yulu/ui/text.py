"""Fuentes y utilidades de texto con ajuste de línea."""
from __future__ import annotations

import pygame

_FONT_CANDIDATES = ["georgia", "palatinolinotype", "bookantiqua", "dejavuserif", "timesnewroman"]
_cache: dict[tuple[int, bool], pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _cache:
        name = pygame.font.match_font(",".join(_FONT_CANDIDATES), bold=bold)
        _cache[key] = pygame.font.Font(name, size) if name else pygame.font.Font(None, size + 4)
    return _cache[key]


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Divide el texto en líneas que caben en `max_width` píxeles."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_text(
    surface: pygame.Surface,
    text: str,
    pos: tuple[int, int],
    size: int,
    color: tuple[int, int, int],
    *,
    bold: bool = False,
    max_width: int | None = None,
    line_spacing: int = 6,
    shadow: bool = True,
) -> int:
    """Dibuja texto (con ajuste opcional) y devuelve la altura total ocupada."""
    font = get_font(size, bold)
    lines = wrap_text(text, font, max_width) if max_width else [text]
    x, y = pos
    for line in lines:
        if shadow:
            surface.blit(font.render(line, True, (0, 0, 0)), (x + 2, y + 2))
        surface.blit(font.render(line, True, color), (x, y))
        y += font.get_linesize() + line_spacing
    return y - pos[1]
