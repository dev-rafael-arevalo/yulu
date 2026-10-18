"""Aplicación y ciclo principal. Orquesta motor, estado y presentación."""
from __future__ import annotations

import logging
import math
import os
from enum import Enum, auto

import pygame

from yulu import config
from yulu.narrative.scenes import NARRATOR, SCENES, START_SCENE
from yulu.narrative.schema import DialogueLine, Scene
from yulu.state.engine import ChoiceResult, NarrativeEngine
from yulu.state.game_state import GameState
from yulu.ui.background import Background
from yulu.ui.choice_menu import ChoiceMenu
from yulu.ui.dialogue_box import DialogueBox
from yulu.ui.hud import draw_hud
from yulu.ui.jaguar import JaguarPresence
from yulu.ui.pause_menu import PauseMenu
from yulu.ui.text import draw_text
from yulu.ui.transitions import Fade, make_vignette

log = logging.getLogger("yulu")
W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT


class Phase(Enum):
    DIALOGUE = auto()
    CHOICES = auto()
    FEEDBACK = auto()
    ENDING = auto()


class Game:
    def __init__(self, windowed: bool = False, smoke_frames: int = 0) -> None:
        self.smoke_frames = smoke_frames
        self.windowed = windowed
        self.screen = self._create_display(windowed)
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()

        self.engine = NarrativeEngine(SCENES, START_SCENE)
        self.state: GameState = self.engine.new_state()
        self.scene: Scene = self.engine.current_scene(self.state)
        self._last_title: str | None = None

        self.dialogue = DialogueBox()
        self.menu = ChoiceMenu()
        self.pause = PauseMenu()
        self.fade = Fade()
        self.jaguar = JaguarPresence()
        self.vignette = make_vignette()
        self._backgrounds: dict[str, Background] = {}
        self.background = self._background_for(self.scene)

        self.phase = Phase.DIALOGUE
        self.paused = False
        self.running = True
        self.time_s = 0.0
        self.line_index = 0
        self.timer_left: float | None = None
        self.pending: ChoiceResult | None = None
        self.title_timer = 0.0
        self._enter_scene(first=True)

    # ---------- configuración de pantalla ----------
    @staticmethod
    def _create_display(windowed: bool) -> pygame.Surface:
        flags = pygame.SCALED
        if not windowed:
            flags |= pygame.FULLSCREEN
        return pygame.display.set_mode((W, H), flags)

    def _toggle_fullscreen(self) -> None:
        self.windowed = not self.windowed
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error as exc:  # pragma: no cover - depende del driver
            log.warning("No se pudo alternar pantalla completa: %s", exc)
            self.screen = self._create_display(self.windowed)

    def _background_for(self, scene: Scene) -> Background:
        if scene.background not in self._backgrounds:
            self._backgrounds[scene.background] = Background(scene.background)
        return self._backgrounds[scene.background]

    # ---------- flujo narrativo ----------
    def _enter_scene(self, first: bool = False) -> None:
        """Sincroniza la presentación con la escena que indica el estado (única fuente de verdad)."""
        scene = self.engine.current_scene(self.state)
        self.scene = scene
        self.background = self._background_for(scene)
        self.line_index = 0
        self.timer_left = None
        self.pending = None
        self.menu.set_choices([])
        self.title_timer = 2.6 if (first or scene.title != self._last_title) else 0.0
        self._last_title = scene.title
        self.phase = Phase.DIALOGUE
        self.dialogue.set_line(scene.lines[0])
        log.info("Escena %s (amenaza=%s, confianza=%s)", scene.id, self.state.threat, self.state.trust)

    def _advance_dialogue(self) -> None:
        if not self.dialogue.finished:
            self.dialogue.skip()
            return
        self.line_index += 1
        if self.line_index < len(self.scene.lines):
            self.dialogue.set_line(self.scene.lines[self.line_index])
            return
        if self.scene.is_ending:
            self.phase = Phase.ENDING
            return
        self.phase = Phase.CHOICES
        self.menu.set_choices(self.engine.available_choices(self.state))
        # La presión temporal empieza solo cuando el jugador ya leyó la escena.
        self.timer_left = self.scene.timer_seconds

    def _resolve(self, result: ChoiceResult) -> None:
        self.pending = result
        self.timer_left = None
        self.menu.set_choices([])
        if result.feedback:
            self.phase = Phase.FEEDBACK
            self.dialogue.set_line(DialogueLine(NARRATOR, result.feedback))
        else:
            self._go_to_pending()

    def _go_to_pending(self) -> None:
        if self.pending is None:
            return
        self.fade.start(on_midpoint=self._enter_scene)

    def _restart(self) -> None:
        self.state = self.engine.restart()
        self.jaguar = JaguarPresence()
        self.fade.start(on_midpoint=lambda: self._enter_scene(first=True))

    # ---------- eventos ----------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self._toggle_fullscreen()
            return
        if self.paused:
            action = self.pause.handle_event(event)
            if action == "continue":
                self.paused = False
            elif action == "restart":
                self.paused = False
                self._restart()
            elif action == "quit":
                self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = True
            return
        if self.fade.active:
            return

        confirm = (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)) or (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        )
        if self.phase == Phase.DIALOGUE and confirm:
            self._advance_dialogue()
        elif self.phase == Phase.CHOICES:
            choice = self.menu.handle_event(event)
            if choice is not None:
                self._resolve(self.engine.apply_choice(self.state, choice.id))
        elif self.phase == Phase.FEEDBACK and confirm:
            if self.dialogue.finished:
                self._go_to_pending()
            else:
                self.dialogue.skip()
        elif self.phase == Phase.ENDING:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self._restart()
            elif confirm and not self.dialogue.finished:
                self.dialogue.skip()

    # ---------- actualización ----------
    def update(self, dt: float) -> None:
        self.fade.update(dt)
        if self.paused:
            return
        self.time_s += dt
        self.background.update(dt)
        self.jaguar.update(dt, self.state.threat, self.scene.jaguar_visible)
        self.dialogue.update(dt)
        self.title_timer = max(0.0, self.title_timer - dt)
        if self.phase == Phase.CHOICES and self.timer_left is not None and not self.fade.active:
            self.timer_left -= dt
            if self.timer_left <= 0:
                self._resolve(self.engine.apply_timeout(self.state))

    # ---------- dibujo ----------
    def draw(self) -> None:
        surface = self.screen
        self.background.draw(surface, self.time_s)
        self.jaguar.draw(surface, self.time_s)
        surface.blit(self.vignette, (0, 0))
        self._draw_threat_tint(surface)

        if self.title_timer > 0:
            self._draw_title(surface)
        draw_hud(surface, self.state, self.scene.chapter_step, self.scene.title, self.timer_left, self.scene.timer_seconds)

        if self.phase == Phase.CHOICES:
            self.menu.draw(surface)
            self.dialogue.draw(surface, hint="Elige con las flechas o los números y Enter, o con el ratón")
        elif self.phase == Phase.ENDING:
            self.dialogue.draw(surface, hint="R: volver a jugar    ·    Esc: menú")
        else:
            self.dialogue.draw(surface)

        self.fade.draw(surface)
        if self.paused:
            self.pause.draw(surface)
        pygame.display.flip()

    def _draw_threat_tint(self, surface: pygame.Surface) -> None:
        if self.state.threat < config.THREAT_HIGH:
            return
        pulse = 0.5 + 0.5 * math.sin(self.time_s * 2.2)
        strength = (self.state.threat - config.THREAT_HIGH) / (config.METER_MAX - config.THREAT_HIGH)
        tint = pygame.Surface((W, H), pygame.SRCALPHA)
        tint.fill((120, 20, 10, int(60 * strength * pulse)))
        surface.blit(tint, (0, 0))

    def _draw_title(self, surface: pygame.Surface) -> None:
        alpha = min(1.0, self.title_timer / 0.8) if self.title_timer < 0.8 else 1.0
        banner = pygame.Surface((W, 90), pygame.SRCALPHA)
        banner.fill((0, 0, 0, int(140 * alpha)))
        draw_text(banner, f"ESCENA {self.scene.chapter_step}", (W // 2 - 50, 14), 16, config.AMBER, bold=True, shadow=False)
        draw_text(banner, self.scene.title.upper(), (W // 2 - len(self.scene.title) * 9, 40), 30, config.TEXT, bold=True, shadow=False)
        banner.set_alpha(int(255 * alpha))
        surface.blit(banner, (0, H // 2 - 120))

    # ---------- bucle ----------
    def run(self) -> int:
        frame = 0
        while self.running:
            dt = min(self.clock.tick(config.FPS) / 1000.0, 0.1)
            if self.smoke_frames:
                self._inject_smoke_events(frame)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            frame += 1
            if self.smoke_frames:
                self._capture_smoke_frame(frame)
                if frame >= self.smoke_frames:
                    self.running = False
        return 0

    def _capture_smoke_frame(self, frame: int) -> None:
        """Guarda capturas periódicas si YULU_SMOKE_DIR está definido (solo pruebas)."""
        out_dir = os.environ.get("YULU_SMOKE_DIR")
        if out_dir and frame % 20 == 0:
            pygame.image.save(self.screen, os.path.join(out_dir, f"frame_{frame:04d}.png"))

    def _inject_smoke_events(self, frame: int) -> None:
        """Prueba automática: avanza el diálogo y elige la primera opción cada pocos fotogramas."""
        if frame % 30 == 0:
            key = pygame.K_r if self.phase == Phase.ENDING else pygame.K_RETURN
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0))


def run(windowed: bool = False, smoke_frames: int = 0) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if smoke_frames:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        game = Game(windowed=windowed, smoke_frames=smoke_frames)
        return game.run()
    except Exception:
        log.exception("Error no controlado en el juego")
        return 1
    finally:
        pygame.quit()
