"""Glosario consultable de náhuat: expresiones aprendidas con traducción, contexto y fuente."""
from __future__ import annotations

import pygame

from yulu import config
from yulu.language.lexicon import Expression, Lexicon
from yulu.state.game_state import GameState
from yulu.ui.text import draw_text, get_font

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
PANEL = pygame.Rect(80, 60, W - 160, H - 120)
LIST_W = 400
ROW_H = 40


class Glossary:
    def __init__(self, lexicon: Lexicon) -> None:
        self.lexicon = lexicon
        self.selected = 0
        self.visible = False

    def toggle(self) -> None:
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_g):
            self.visible = False
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.lexicon)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.lexicon)

    def draw(self, surface: pygame.Surface, state: GameState) -> None:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))
        panel = pygame.Surface(PANEL.size, pygame.SRCALPHA)
        panel.fill((*config.PANEL, 235))
        pygame.draw.rect(panel, (*config.AMBER, 180), panel.get_rect(), 2, border_radius=6)
        surface.blit(panel, PANEL.topleft)

        expressions = self.lexicon.all()
        known = sum(1 for e in expressions if state.knows(e.id))
        draw_text(surface, "GLOSARIO DE NÁHUAT", (PANEL.x + 24, PANEL.y + 16), 24, config.AMBER, bold=True)
        draw_text(surface, f"{known}/{len(expressions)} expresiones aprendidas   ·   G o Esc: cerrar   ·   Flechas: navegar",
                  (PANEL.x + 24, PANEL.y + 50), 15, config.TEXT_DIM, shadow=False)

        list_top = PANEL.y + 90
        font = get_font(20)
        for i, expression in enumerate(expressions):
            y = list_top + i * ROW_H
            is_known = state.knows(expression.id)
            active = i == self.selected
            if active:
                pygame.draw.rect(surface, (30, 36, 48), (PANEL.x + 16, y - 4, LIST_W, ROW_H - 4), border_radius=4)
            label = expression.nahuat if is_known else "— — —"
            color = (config.TEXT if active else config.TEXT_DIM) if is_known else (70, 76, 86)
            surface.blit(font.render(label, True, color), (PANEL.x + 28, y))
        pygame.draw.line(surface, (60, 70, 80), (PANEL.x + LIST_W + 32, list_top), (PANEL.x + LIST_W + 32, PANEL.bottom - 24))

        self._draw_detail(surface, expressions[self.selected], state.knows(expressions[self.selected].id))

    def _draw_detail(self, surface: pygame.Surface, expression: Expression, is_known: bool) -> None:
        x = PANEL.x + LIST_W + 56
        y = PANEL.y + 90
        width = PANEL.right - x - 24
        if not is_known:
            draw_text(surface, "Aún no has oído esta expresión.", (x, y), 22, config.TEXT_DIM)
            draw_text(surface, "Contexto: " + expression.context, (x, y + 40), 18, (90, 96, 106), max_width=width)
            return
        y += draw_text(surface, expression.nahuat, (x, y), 34, config.AMBER, bold=True) + 2
        y += draw_text(surface, expression.spanish, (x, y), 24, config.TEXT) + 10
        if expression.literal:
            y += draw_text(surface, "Literal: " + expression.literal, (x, y), 17, config.TEXT_DIM, max_width=width) + 6
        if expression.pronunciation:
            y += draw_text(surface, "Pronunciación aproximada: " + expression.pronunciation, (x, y), 17, config.TEXT_DIM, max_width=width) + 6
        y += draw_text(surface, "Uso: " + expression.context, (x, y), 17, config.TEXT, max_width=width) + 14
        status_color = (90, 170, 120) if expression.status == "verificada" else config.AMBER
        y += draw_text(surface, "Estado: " + expression.status_label, (x, y), 16, status_color) + 8
        for source in expression.sources:
            y += draw_text(surface, f"• {source.citation} — {source.locator}", (x, y), 14, config.TEXT_DIM, max_width=width, shadow=False) + 4
