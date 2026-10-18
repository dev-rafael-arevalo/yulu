"""Menú de decisiones con teclado y ratón."""
from __future__ import annotations

import pygame

from yulu import config
from yulu.narrative.schema import Choice
from yulu.ui.text import draw_text, get_font

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
ITEM_H = 46
PANEL_X = 80
PANEL_W = W - 160


class ChoiceMenu:
    def __init__(self) -> None:
        self.choices: list[Choice] = []
        self.selected = 0
        self._rects: list[pygame.Rect] = []
        self.prompt = "¿Qué haces?"

    def set_choices(self, choices: list[Choice], prompt: str = "¿Qué haces?") -> None:
        self.choices = choices
        self.selected = 0
        self.prompt = prompt
        total_h = len(choices) * ITEM_H
        top = H - 240 - total_h - 20
        self._rects = [pygame.Rect(PANEL_X, top + i * ITEM_H, PANEL_W, ITEM_H - 6) for i in range(len(choices))]

    def handle_event(self, event: pygame.event.Event) -> Choice | None:
        """Devuelve la opción confirmada o None."""
        if not self.choices:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.choices)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.choices)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.choices[self.selected]
            elif pygame.K_1 <= event.key <= pygame.K_9:
                index = event.key - pygame.K_1
                if index < len(self.choices):
                    self.selected = index
                    return self.choices[index]
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos):
                    return self.choices[i]
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if not self.choices:
            return
        header_y = self._rects[0].y - 40
        draw_text(surface, self.prompt, (PANEL_X + 8, header_y), 20, config.AMBER, bold=True)
        font = get_font(24)
        for i, (choice, rect) in enumerate(zip(self.choices, self._rects)):
            active = i == self.selected
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill((*config.PANEL, 230 if active else 170))
            border = config.AMBER if active else (60, 70, 80)
            pygame.draw.rect(panel, (*border, 255), panel.get_rect(), 2, border_radius=4)
            surface.blit(panel, rect.topleft)
            color = config.TEXT if active else config.TEXT_DIM
            label = font.render(f"{i + 1}.  {choice.text}", True, color)
            surface.blit(label, (rect.x + 18, rect.y + (rect.h - label.get_height()) // 2))
            if active:
                pygame.draw.polygon(surface, config.AMBER, [(rect.x - 14, rect.centery - 7), (rect.x - 14, rect.centery + 7), (rect.x - 4, rect.centery)])
