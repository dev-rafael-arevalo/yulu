"""Aplicación y ciclo principal. Orquesta motor, estado, léxico y presentación."""
from __future__ import annotations

import json
import logging
import math
import os
import random
from enum import Enum, auto

import pygame

from yulu import config
from yulu.audio.audio_manager import AudioManager
from yulu.audio.soundscape import Soundscape
from yulu.audio.voice import voice_filename
from yulu.language.lexicon import Lexicon
from yulu.narrative.scenes import GOOD_ENDING, NARRATOR, SCENES, START_SCENE
from yulu.paths import PROJECT_ROOT
from yulu.narrative.schema import DialogueLine, Scene
from yulu.state.engine import ChoiceResult, NarrativeEngine
from yulu.state.game_state import GameState
from yulu.ui.assets import ImageStore
from yulu.ui.background import Background
from yulu.ui.choice_menu import ChoiceMenu
from yulu.ui.dialogue_box import DialogueBox
from yulu.ui.glossary import Glossary
from yulu.ui.hud import draw_hud
from yulu.ui.jaguar import JaguarPresence
from yulu.ui.pause_menu import PauseMenu
from yulu.ui.text import draw_text
from yulu.ui.transitions import Fade, make_vignette

log = logging.getLogger("yulu")
W, H = config.LOGICAL_WIDTH, config.LOGICAL_HEIGHT
SHAKE_THREAT_DELTA = 15
SHAKE_DURATION = 0.45
SETTINGS_PATH = PROJECT_ROOT / "settings.json"


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
        self.canvas = pygame.Surface((W, H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()

        self.lexicon = Lexicon.load()
        self.engine = NarrativeEngine(SCENES, START_SCENE, known_expressions=self.lexicon.playable_ids())
        self.state: GameState = self.engine.new_state()
        self.scene: Scene = self.engine.current_scene(self.state)
        self._last_title: str | None = None

        self.store = ImageStore()
        missing = self.store.missing_files()
        if missing:
            log.warning("%d recursos gráficos ausentes; se usan escenarios provisionales. Ver docs/ART_PROMPTS.md", len(missing))
        self.audio = AudioManager(volumes=self._load_volumes())
        self.soundscape = Soundscape(self.audio)
        self.dialogue = DialogueBox()
        self.menu = ChoiceMenu()
        self.pause = PauseMenu(self.audio.volumes)
        self.glossary = Glossary(self.lexicon)
        self.fade = Fade()
        self.jaguar = JaguarPresence(self.store)
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
        self.shake_time = 0.0
        self.shake_amp = 0.0
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
            self._backgrounds[scene.background] = Background(scene.background, self.store)
        return self._backgrounds[scene.background]

    # ---------- ajustes persistentes ----------
    @staticmethod
    def _load_volumes() -> dict[str, float]:
        volumes = dict(config.DEFAULT_VOLUMES)
        try:
            saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8")).get("volumes", {})
            volumes.update({k: float(v) for k, v in saved.items() if k in volumes})
        except (OSError, ValueError, AttributeError):
            pass
        return volumes

    def _save_volumes(self) -> None:
        try:
            SETTINGS_PATH.write_text(json.dumps({"volumes": self.audio.volumes}, indent=2), encoding="utf-8")
        except OSError as exc:
            log.warning("No se pudieron guardar los ajustes: %s", exc)

    def _say(self, line: DialogueLine) -> None:
        """Muestra la línea con subtítulo y reproduce su narración pregenerada si existe."""
        self.dialogue.set_line(line)
        self.audio.play_voice(voice_filename(line))

    def _replay_voice(self) -> None:
        if self.dialogue.line is not None:
            self.audio.play_voice(voice_filename(self.dialogue.line))

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
        self.soundscape.enter_scene(scene, self.state.threat)
        self._say(scene.lines[0])
        log.info("Escena %s (amenaza=%s, confianza=%s, vocabulario=%d)", scene.id, self.state.threat, self.state.trust, len(self.state.vocabulary))

    def _advance_dialogue(self) -> None:
        if not self.dialogue.finished:
            self.dialogue.skip()
            return
        self.line_index += 1
        if self.line_index < len(self.scene.lines):
            self._say(self.scene.lines[self.line_index])
            return
        if self.scene.is_ending:
            self.phase = Phase.ENDING
            self.soundscape.on_ending(self.state.ending == GOOD_ENDING)
            return
        if self.scene.is_automatic:
            self.engine.resolve_branch(self.state)
            self.fade.start(on_midpoint=self._enter_scene)
            return
        self.phase = Phase.CHOICES
        self.menu.set_choices(self.engine.available_choices(self.state))
        # La presión temporal empieza solo cuando el jugador ya leyó la escena.
        self.timer_left = self.scene.timer_seconds

    def _resolve(self, result: ChoiceResult) -> None:
        self.pending = result
        self.timer_left = None
        self.menu.set_choices([])
        self.soundscape.on_choice(result)
        if result.threat_delta >= SHAKE_THREAT_DELTA:
            self._shake(6 + result.threat_delta / 5, SHAKE_DURATION)
        if result.feedback:
            self.phase = Phase.FEEDBACK
            self._say(DialogueLine(NARRATOR, result.feedback))
        else:
            self._go_to_pending()

    def _go_to_pending(self) -> None:
        if self.pending is None:
            return
        self.audio.stop_voice()
        self.soundscape.on_transition()
        self.fade.start(on_midpoint=self._enter_scene)

    def _restart(self) -> None:
        self.state = self.engine.restart()
        self.jaguar = JaguarPresence(self.store)
        self.fade.start(on_midpoint=lambda: self._enter_scene(first=True))

    def _shake(self, amplitude: float, duration: float) -> None:
        self.shake_amp = amplitude
        self.shake_time = duration

    # ---------- eventos ----------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self._toggle_fullscreen()
            return
        if self.glossary.visible:
            self.glossary.handle_event(event)
            return
        if self.paused:
            action = self.pause.handle_event(event)
            if isinstance(action, tuple):
                _, category, value = action
                self.audio.set_volume(category, value)
                self._save_volumes()
                if category == "sfx":
                    self.audio.play_sfx("ui_move", gain=0.6)
            elif action == "continue":
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
        if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            self.glossary.toggle()  # consultar el glosario detiene el temporizador (ver update)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_v:
            self._replay_voice()
            return
        if self.fade.active:
            return

        confirm = (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)) or (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        )
        if self.phase == Phase.DIALOGUE and confirm:
            self._advance_dialogue()
        elif self.phase == Phase.CHOICES:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                self.soundscape.on_menu_move()
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
        if self.paused or self.glossary.visible:
            return
        self.time_s += dt
        self.background.update(dt)
        self.jaguar.update(dt, self.state.threat, self.scene.jaguar_visible)
        self.dialogue.update(dt)
        self.title_timer = max(0.0, self.title_timer - dt)
        self.shake_time = max(0.0, self.shake_time - dt)
        self.soundscape.update(dt, self.state.threat, self.timer_left if self.phase == Phase.CHOICES else None)
        if self.phase == Phase.CHOICES and self.timer_left is not None and not self.fade.active:
            self.timer_left -= dt
            if self.timer_left <= 0:
                self._resolve(self.engine.apply_timeout(self.state))

    # ---------- dibujo ----------
    def draw(self) -> None:
        surface = self.canvas
        self.background.draw(surface, self.time_s)
        self.jaguar.draw(surface, self.time_s)
        surface.blit(self.vignette, (0, 0))
        self._draw_threat_tint(surface)

        if self.title_timer > 0 and not self.paused:
            self._draw_title(surface)
        draw_hud(surface, self.state, self.scene.chapter_step, self.scene.title, self.timer_left, self.scene.timer_seconds)
        if self.background.is_provisional:
            draw_text(surface, "ESCENARIO PROVISIONAL", (W - 210, H - 26), 13, (120, 110, 90), shadow=False)

        if self.phase == Phase.CHOICES:
            self.menu.draw(surface)
            self.dialogue.draw(surface, hint="Flechas o números y Enter, o ratón    ·    G: glosario    ·    V: repetir voz")
        elif self.phase == Phase.FEEDBACK:
            self.dialogue.draw(surface)
            self._draw_learned_card(surface)
        elif self.phase == Phase.ENDING:
            self.dialogue.draw(surface, hint="R: volver a jugar    ·    G: glosario    ·    Esc: menú")
            self._draw_ending_summary(surface)
        else:
            self.dialogue.draw(surface, hint="Enter / clic: continuar    ·    V: repetir voz    ·    G: glosario    ·    Esc: pausa")
        self._draw_subtitle_translation(surface)

        self.fade.draw(surface)
        if self.glossary.visible:
            self.glossary.draw(surface, self.state)
        if self.paused:
            self.pause.draw(surface)

        offset = (0, 0)
        if self.shake_time > 0:
            k = self.shake_amp * (self.shake_time / SHAKE_DURATION)
            offset = (int(random.uniform(-k, k)), int(random.uniform(-k, k)))
            self.screen.fill((0, 0, 0))
        self.screen.blit(surface, offset)
        pygame.display.flip()

    def _draw_subtitle_translation(self, surface: pygame.Surface) -> None:
        """Bajo una línea en náhuat: la traducción si ya se aprendió, o un aviso de incomprensión."""
        line = self.dialogue.line
        if line is None or not line.nahuat_id or not self.dialogue.finished or self.phase == Phase.FEEDBACK:
            return
        expression = self.lexicon.get(line.nahuat_id)
        if self.state.knows(expression.id):
            text, color = f"= {expression.spanish}", config.AMBER
        else:
            text, color = "(No entiendes estas palabras... todavía.)", config.TEXT_DIM
        draw_text(surface, text, (104, H - 120), 20, color)

    def _draw_learned_card(self, surface: pygame.Surface) -> None:
        if not self.pending or not self.pending.learned:
            return
        items = [self.lexicon.get(i) for i in self.pending.learned]
        height = 44 + 46 * len(items)
        card = pygame.Rect(W - 480, H - 250 - height, 400, height)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        panel.fill((*config.PANEL, 225))
        pygame.draw.rect(panel, (*config.AMBER, 200), panel.get_rect(), 2, border_radius=6)
        surface.blit(panel, card.topleft)
        draw_text(surface, "NUEVA EXPRESIÓN APRENDIDA", (card.x + 16, card.y + 12), 14, config.AMBER, bold=True, shadow=False)
        for i, expression in enumerate(items):
            y = card.y + 40 + i * 46
            draw_text(surface, expression.nahuat, (card.x + 16, y), 22, config.TEXT, bold=True)
            draw_text(surface, expression.spanish, (card.x + 16, y + 24), 15, config.TEXT_DIM, shadow=False)

    def _draw_ending_summary(self, surface: pygame.Surface) -> None:
        card = pygame.Rect(W // 2 - 300, 120, 600, 150)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        panel.fill((*config.PANEL, 225))
        pygame.draw.rect(panel, (*config.AMBER, 200), panel.get_rect(), 2, border_radius=6)
        surface.blit(panel, card.topleft)
        title = "FINAL: EL AMANECER CON LA ALDEA" if self.state.ending == GOOD_ENDING else "FINAL: EL AMANECER EN SOLEDAD"
        draw_text(surface, title, (card.x + 20, card.y + 14), 20, config.AMBER, bold=True)
        draw_text(surface, f"Expresiones aprendidas: {len(self.state.vocabulary)} de {len(self.lexicon)}   ·   Confianza: {self.state.trust}   ·   Amenaza: {self.state.threat}",
                  (card.x + 20, card.y + 52), 17, config.TEXT)
        draw_text(surface, f"Decisiones tomadas: {len(self.state.decisions)}. Pulsa G para repasar el glosario o R para explorar otras decisiones.",
                  (card.x + 20, card.y + 84), 15, config.TEXT_DIM, max_width=card.w - 40)

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

    def _inject_smoke_events(self, frame: int) -> None:
        """Prueba automática: avanza el diálogo y elige la primera opción cada pocos fotogramas."""
        if frame % 30 == 0:
            key = pygame.K_r if self.phase == Phase.ENDING else pygame.K_RETURN
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0))

    def _capture_smoke_frame(self, frame: int) -> None:
        """Guarda capturas periódicas si YULU_SMOKE_DIR está definido (solo pruebas)."""
        out_dir = os.environ.get("YULU_SMOKE_DIR")
        if out_dir and frame % 20 == 0:
            pygame.image.save(self.screen, os.path.join(out_dir, f"frame_{frame:04d}.png"))


def run(windowed: bool = False, smoke_frames: int = 0) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if smoke_frames:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    game: Game | None = None
    try:
        game = Game(windowed=windowed, smoke_frames=smoke_frames)
        return game.run()
    except Exception:
        log.exception("Error no controlado en el juego")
        return 1
    finally:
        if game is not None:
            game.audio.shutdown()
        pygame.quit()
