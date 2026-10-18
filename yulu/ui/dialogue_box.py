"""Caja de diálogo con efecto de escritura progresiva y subtítulo."""
from __future__ import annotations

import pygame

from yulu import config
from yulu.narrative.schema import DialogueLine
from yulu.ui.text import draw_text, get_font

W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
BOX_RECT = pygame.Rect(80, H - 230, W - 160, 170)


class DialogueBox:
    def __init__(self) -> None:
        self.line: DialogueLine | None = None
        self._shown_chars = 0.0
        self.hint = "Enter / clic: continuar    ·    Esc: pausa"

    def set_line(self, line: DialogueLine) -> None:
        self.line = line
        self._shown_chars = 0.0

    @property
    def finished(self) -> bool:
        return self.line is None or self._shown_chars >= len(self.line.text)

    def skip(self) -> None:
        if self.line:
            self._shown_chars = len(self.line.text)

    def update(self, dt: float) -> None:
        if self.line and not self.finished:
            self._shown_chars = min(len(self.line.text), self._shown_chars + config.TYPEWRITER_CPS * dt)

    def draw(self, surface: pygame.Surface, hint: str | None = None) -> None:
        if self.line is None:
            return
        panel = pygame.Surface(BOX_RECT.size, pygame.SRCALPHA)
        panel.fill((*config.PANEL, 215))
        pygame.draw.rect(panel, (*config.AMBER, 160), panel.get_rect(), 2, border_radius=6)
        surface.blit(panel, BOX_RECT.topleft)

        speaker_color = config.AMBER if self.line.speaker != "Tú" else config.FOG
        draw_text(surface, self.line.speaker.upper(), (BOX_RECT.x + 24, BOX_RECT.y + 14), 18, speaker_color, bold=True)
        visible = self.line.text[: int(self._shown_chars)]
        draw_text(surface, visible, (BOX_RECT.x + 24, BOX_RECT.y + 48), 26, config.TEXT, max_width=BOX_RECT.w - 48)

        if self.finished:
            font = get_font(16)
            label = font.render(hint or self.hint, True, config.TEXT_DIM)
            surface.blit(label, (BOX_RECT.right - label.get_width() - 20, BOX_RECT.bottom - 26))
