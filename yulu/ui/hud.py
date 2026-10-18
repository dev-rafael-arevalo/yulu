"""Indicadores discretos: amenaza, confianza, progreso del capítulo y temporizador."""
from __future__ import annotations

import pygame

from yulu import config
from yulu.state.game_state import GameState
from yulu.ui.text import draw_text, get_font

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
TOTAL_STEPS = 5


def _meter(surface: pygame.Surface, x: int, y: int, label: str, value: int, color: tuple) -> None:
    width, height = 180, 8
    draw_text(surface, label, (x, y - 20), 15, config.TEXT_DIM, shadow=False)
    pygame.draw.rect(surface, (20, 24, 30), (x, y, width, height), border_radius=4)
    fill = int(width * value / config.METER_MAX)
    if fill:
        pygame.draw.rect(surface, color, (x, y, fill, height), border_radius=4)
    pygame.draw.rect(surface, (70, 80, 90), (x, y, width, height), 1, border_radius=4)


def draw_hud(surface: pygame.Surface, state: GameState, step: int, title: str, timer_left: float | None, timer_total: float | None) -> None:
    threat_color = config.DANGER if state.threat >= config.THREAT_HIGH else config.AMBER
    _meter(surface, 40, 48, "AMENAZA", state.threat, threat_color)
    _meter(surface, 260, 48, "CONFIANZA", state.trust, (90, 170, 120))

    # Progreso del capítulo: cinco puntos.
    for i in range(TOTAL_STEPS):
        cx = W - 60 - (TOTAL_STEPS - 1 - i) * 22
        filled = i < step
        pygame.draw.circle(surface, config.AMBER if filled else (40, 46, 56), (cx, 44), 6)
        pygame.draw.circle(surface, (90, 90, 90), (cx, 44), 6, 1)
    font = get_font(16)
    label = font.render(f"Escena {step}/{TOTAL_STEPS} · {title}", True, config.TEXT_DIM)
    surface.blit(label, (W - 60 - label.get_width() + 6, 58))

    if timer_left is not None and timer_total:
        frac = max(0.0, timer_left / timer_total)
        bar_w = 320
        x = (W - bar_w) // 2
        pygame.draw.rect(surface, (20, 24, 30), (x, 36, bar_w, 10), border_radius=5)
        color = config.DANGER if frac < 0.35 else config.FIRE
        pygame.draw.rect(surface, color, (x, 36, int(bar_w * frac), 10), border_radius=5)
        draw_text(surface, "El jaguar se acerca", (x + bar_w // 2 - 70, 50), 15, color, shadow=False)
