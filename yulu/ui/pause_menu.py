"""Menú de pausa con controles de volumen independientes por categoría."""
from __future__ import annotations

import pygame

from yulu import config
from yulu.ui.text import draw_text, get_font

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT

VOLUME_PREFIX = "volume:"
VOLUME_ITEMS = (("music", "Música"), ("ambient", "Ambiente"), ("sfx", "Efectos"), ("voice", "Voces"))
ITEMS = (("continue", "Continuar"), *((VOLUME_PREFIX + key, label) for key, label in VOLUME_ITEMS), ("restart", "Volver a empezar"), ("quit", "Salir del juego"))
VOLUME_STEP = 0.1
BAR_W, BAR_H = 220, 10


class PauseMenu:
    def __init__(self, volumes: dict[str, float]) -> None:
        self.selected = 0
        self.volumes = volumes  # referencia compartida con el AudioManager

    def handle_event(self, event: pygame.event.Event) -> tuple[str, str, float] | str | None:
        """Devuelve una acción ('continue', 'restart', 'quit'), una tupla ('volume', categoría, valor) o None."""
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_ESCAPE:
            return "continue"
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(ITEMS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(ITEMS)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
            action = ITEMS[self.selected][0]
            if action.startswith(VOLUME_PREFIX):
                category = action[len(VOLUME_PREFIX):]
                delta = VOLUME_STEP if event.key in (pygame.K_RIGHT, pygame.K_d) else -VOLUME_STEP
                value = max(0.0, min(1.0, round(self.volumes.get(category, 0.0) + delta, 2)))
                return ("volume", category, value)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            action = ITEMS[self.selected][0]
            if not action.startswith(VOLUME_PREFIX):
                return action
        return None

    def draw(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        draw_text(surface, "PAUSA", (W // 2 - 60, H // 2 - 230), 44, config.AMBER, bold=True)
        font = get_font(26)
        x = W // 2 - 220
        for i, (action, label) in enumerate(ITEMS):
            y = H // 2 - 140 + i * 46
            active = i == self.selected
            color = config.TEXT if active else config.TEXT_DIM
            surface.blit(font.render(("> " if active else "   ") + label, True, color), (x, y))
            if action.startswith(VOLUME_PREFIX):
                value = self.volumes.get(action[len(VOLUME_PREFIX):], 0.0)
                bx, by = x + 200, y + 12
                pygame.draw.rect(surface, (30, 36, 46), (bx, by, BAR_W, BAR_H), border_radius=5)
                pygame.draw.rect(surface, config.AMBER if active else (120, 100, 60), (bx, by, int(BAR_W * value), BAR_H), border_radius=5)
                pygame.draw.rect(surface, (90, 90, 90), (bx, by, BAR_W, BAR_H), 1, border_radius=5)
                surface.blit(get_font(16).render(f"{int(value * 100)}%", True, color), (bx + BAR_W + 12, y + 4))
        draw_text(surface, "Flechas izquierda y derecha ajustan el volumen   ·   F11: pantalla completa / ventana   ·   V: repetir la voz", (W // 2 - 330, H // 2 + 200), 15, config.TEXT_DIM)
