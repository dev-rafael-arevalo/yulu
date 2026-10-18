"""Menú de pausa. Los controles de volumen se añaden en la FASE 4."""
from __future__ import annotations

import pygame

from yulu import config
from yulu.ui.text import draw_text, get_font

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT

OPTIONS = (("continue", "Continuar"), ("restart", "Volver a empezar"), ("quit", "Salir del juego"))


class PauseMenu:
    def __init__(self) -> None:
        self.selected = 0

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return OPTIONS[self.selected][0]
            elif event.key == pygame.K_ESCAPE:
                return "continue"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))
        draw_text(surface, "PAUSA", (W // 2 - 60, H // 2 - 150), 44, config.AMBER, bold=True)
        font = get_font(28)
        for i, (_, label) in enumerate(OPTIONS):
            active = i == self.selected
            text = font.render(("> " if active else "   ") + label, True, config.TEXT if active else config.TEXT_DIM)
            surface.blit(text, (W // 2 - 120, H // 2 - 60 + i * 50))
        draw_text(surface, "F11: pantalla completa / ventana", (W // 2 - 140, H // 2 + 130), 16, config.TEXT_DIM)
