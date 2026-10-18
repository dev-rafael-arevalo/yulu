"""Grabación guiada de la narración y las frases en náhuat con la voz del estudiante.

Uso (con el entorno del juego):
    .venv\\Scripts\\python tools\\record_voice.py                 # todas las líneas pendientes, en orden narrativo
    .venv\\Scripts\\python tools\\record_voice.py --nahuat-only   # solo las frases en náhuat
    .venv\\Scripts\\python tools\\record_voice.py --speaker Narrador
    .venv\\Scripts\\python tools\\record_voice.py --scene s3_puerta
    .venv\\Scripts\\python tools\\record_voice.py --redo          # incluir líneas ya grabadas
    .venv\\Scripts\\python tools\\record_voice.py --list          # ver el plan sin grabar
    .venv\\Scripts\\python tools\\record_voice.py --mic 1         # elegir micrófono (ver --list)

Teclas dentro de la ventana:
    ESPACIO  empezar / detener la grabación
    P        escuchar la toma
    ENTER    aceptar la toma y pasar a la siguiente línea
    R        descartar la toma y volver a grabar
    N        saltar la línea sin grabar
    ESC      salir (lo aceptado ya está guardado)

Cada toma se recorta en silencio al inicio y al final, se normaliza y se guarda como WAV mono
de 16 bits con el nombre exacto que espera el juego (ver yulu/audio/voice.py). El índice
voice/index.json marca la línea como "grabación humana" y tools/generate_narration.py no la
sobrescribe nunca (salvo con --force-human).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yulu import config  # noqa: E402
from yulu.audio.voice import NAHUAT_DIR, is_human_recording_required, voice_filename  # noqa: E402
from yulu.language.lexicon import Lexicon  # noqa: E402
from yulu.narrative.scenes import NARRATOR, SCENES  # noqa: E402
from yulu.narrative.schema import DialogueLine  # noqa: E402
from yulu.paths import AUDIO_DIR  # noqa: E402
from yulu.ui.text import draw_text, get_font  # noqa: E402

VOICE_DIR = AUDIO_DIR / "voice"
INDEX_PATH = VOICE_DIR / "index.json"
LOG_PATH = VOICE_DIR / "recordings.log"
RATE = 44100
HUMAN_LABEL = "grabación humana (estudiante)"
SILENCE_THRESHOLD = 600  # amplitud (0-32767) por debajo de la cual se considera silencio
TARGET_PEAK = 0.9
W, H = 1280, 720


@dataclass
class Item:
    filename: str
    scene_id: str
    speaker: str
    text: str
    nahuat_id: str | None
    kind: str  # "diálogo", "retroalimentación"


# ---------- plan de grabación ----------
def build_items(args) -> list[Item]:
    items: list[Item] = []
    seen: set[str] = set()
    for scene in SCENES.values():
        lines: list[tuple[DialogueLine, str]] = [(line, "diálogo") for line in scene.lines]
        lines += [(DialogueLine(NARRATOR, c.feedback), "retroalimentación") for c in scene.choices if c.feedback]
        for line, kind in lines:
            filename = voice_filename(line)
            if filename in seen:
                continue
            seen.add(filename)
            is_nahuat = is_human_recording_required(line)
            if args.nahuat_only and not is_nahuat:
                continue
            if args.spanish_only and is_nahuat:
                continue
            if args.speaker and line.speaker != args.speaker:
                continue
            if args.scene and scene.id != args.scene:
                continue
            if not args.redo and (VOICE_DIR / filename).exists() and _is_human(filename):
                continue
            items.append(Item(filename, scene.id, line.speaker, line.text, line.nahuat_id, kind))
    return items


def _load_index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8")) if INDEX_PATH.exists() else {}


def _is_human(filename: str) -> bool:
    entry = _load_index().get(filename, {})
    return str(entry.get("voice", "")).startswith("grabación humana")


def _mark_recorded(item: Item, seconds: float) -> None:
    index = _load_index()
    index[item.filename] = {
        "speaker": item.speaker, "text": item.text, "nahuat": item.nahuat_id is not None,
        "voice": HUMAN_LABEL, "status": "grabada", "hash": "human", "seconds": round(seconds, 2),
    }
    pending = index.get("_pending_nahuat", [])
    index["_pending_nahuat"] = [p for p in pending if p.get("file") != item.filename]
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {item.filename}  {item.speaker}  {seconds:.1f}s  {item.text[:60]}\n")


# ---------- procesamiento de audio ----------
def trim_silence(samples: array, threshold: int = SILENCE_THRESHOLD, pad_ms: int = 120) -> array:
    n = len(samples)
    start = next((i for i in range(n) if abs(samples[i]) > threshold), None)
    if start is None:
        return array("h")
    end = next(i for i in range(n - 1, -1, -1) if abs(samples[i]) > threshold)
    pad = int(RATE * pad_ms / 1000)
    return samples[max(0, start - pad): min(n, end + pad)]


def normalize(samples: array, target: float = TARGET_PEAK) -> array:
    peak = max((abs(v) for v in samples), default=0)
    if peak == 0:
        return samples
    gain = min(8.0, target * 32767 / peak)
    return array("h", (max(-32767, min(32767, int(v * gain))) for v in samples))


def save_wav(path: Path, samples: array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(samples.tobytes())


# ---------- captura ----------
class Recorder:
    def __init__(self, device_index: int | None) -> None:
        from pygame._sdl2 import audio as sdl_audio

        self._sdl = sdl_audio
        names = sdl_audio.get_audio_device_names(True)
        if not names:
            raise RuntimeError("No se encontró ningún micrófono.")
        self.device_name = names[device_index if device_index is not None else 0]
        self.chunks: list[bytes] = []
        self.level = 0.0
        self.recording = False
        self._device = None

    def start(self) -> None:
        self.chunks = []
        self._device = self._sdl.AudioDevice(
            devicename=self.device_name, iscapture=True, frequency=RATE, audioformat=self._sdl.AUDIO_S16,
            numchannels=1, chunksize=2048, allowed_changes=0, callback=self._on_chunk,
        )
        self._device.pause(0)
        self.recording = True

    def _on_chunk(self, _device, buffer) -> None:
        data = bytes(buffer)
        self.chunks.append(data)
        samples = array("h", data)
        self.level = (max((abs(v) for v in samples), default=0)) / 32767

    def stop(self) -> array:
        if self._device is not None:
            self._device.pause(1)
            self._device.close()
            self._device = None
        self.recording = False
        self.level = 0.0
        return array("h", b"".join(self.chunks))


# ---------- interfaz ----------
class Session:
    def __init__(self, items: list[Item], recorder: Recorder, lexicon: Lexicon) -> None:
        self.items = items
        self.recorder = recorder
        self.lexicon = lexicon
        self.index = 0
        self.take: array | None = None
        self.message = ""
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("YULU · Grabación de voz")
        self.clock = pygame.time.Clock()
        self.done = 0

    @property
    def current(self) -> Item | None:
        return self.items[self.index] if self.index < len(self.items) else None

    def run(self) -> int:
        while self.current is not None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return self.done
                if event.type == pygame.KEYDOWN and self._handle_key(event.key):
                    return self.done
            if self.current is None:
                break  # se aceptó o saltó la última línea
            self.draw()
            self.clock.tick(30)
        self.draw(final=True)
        pygame.time.wait(1500)
        return self.done

    def _handle_key(self, key: int) -> bool:
        item = self.current
        if key == pygame.K_ESCAPE:
            if self.recorder.recording:
                self.recorder.stop()
            return True
        if key == pygame.K_SPACE:
            if self.recorder.recording:
                raw = self.recorder.stop()
                self.take = normalize(trim_silence(raw))
                seconds = len(self.take) / RATE
                self.message = f"Toma de {seconds:.1f} s. P para escuchar, ENTER para aceptar, R para repetir." if seconds > 0.2 else "No se detectó voz. Pulsa ESPACIO y habla más cerca del micrófono."
            else:
                self.take = None
                self.recorder.start()
                self.message = "Grabando... pulsa ESPACIO al terminar la frase."
        elif key == pygame.K_p and self.take is not None and len(self.take):
            # Se reproduce desde un WAV temporal: así el mezclador respeta la frecuencia y el mono
            # de la toma aunque él mismo trabaje en estéreo (un búfer crudo se interpretaría mal).
            preview = VOICE_DIR / "_preview.wav"
            save_wav(preview, self.take)
            pygame.mixer.Sound(str(preview)).play()
        elif key == pygame.K_RETURN and self.take is not None and len(self.take) > RATE * 0.2:
            save_wav(VOICE_DIR / item.filename, self.take)
            _mark_recorded(item, len(self.take) / RATE)
            self.done += 1
            self.take = None
            self.message = ""
            self.index += 1
        elif key == pygame.K_r:
            self.take = None
            self.message = "Toma descartada. Pulsa ESPACIO para grabar de nuevo."
        elif key == pygame.K_n:
            self.take = None
            self.message = ""
            self.index += 1
        return False

    def draw(self, final: bool = False) -> None:
        s = self.screen
        s.fill((8, 12, 24))
        if final:
            draw_text(s, f"Sesión terminada. Tomas guardadas: {self.done}.", (80, H // 2 - 20), 32, config.AMBER, bold=True)
            pygame.display.flip()
            return
        item = self.current
        draw_text(s, f"Línea {self.index + 1} de {len(self.items)}   ·   {item.kind}   ·   escena {item.scene_id}", (60, 36), 18, config.TEXT_DIM, shadow=False)
        draw_text(s, f"Micrófono: {self.recorder.device_name}", (60, 60), 15, config.TEXT_DIM, shadow=False)
        draw_text(s, item.speaker.upper(), (60, 120), 24, config.AMBER, bold=True, shadow=False)
        if item.nahuat_id:
            expression = self.lexicon.get(item.nahuat_id)
            draw_text(s, item.text, (60, 160), 54, config.TEXT, bold=True, max_width=W - 120)
            y = 260
            y += draw_text(s, "Significado: " + expression.spanish, (60, y), 24, config.TEXT, max_width=W - 120)
            if expression.pronunciation:
                y += draw_text(s, "Pronunciación aproximada: " + expression.pronunciation, (60, y + 6), 22, config.AMBER, max_width=W - 120)
            y += draw_text(s, "Contexto: " + expression.context, (60, y + 10), 19, config.TEXT_DIM, max_width=W - 120)
            draw_text(s, "Di solo la frase en náhuat, sin la traducción. Una pausa breve antes y después.", (60, y + 24), 18, config.TEXT_DIM, max_width=W - 120)
        else:
            size = 34 if len(item.text) <= 140 else 28 if len(item.text) <= 220 else 24
            draw_text(s, item.text, (60, 160), size, config.TEXT, max_width=W - 120)
            hint = {
                NARRATOR: "Voz pausada y grave, con intención de suspense. Respeta las pausas de los puntos.",
                "Tú": "Primera persona, en voz baja, como quien piensa en voz alta.",
            }.get(item.speaker, "Voz natural, clara y cercana al micrófono.")
            draw_text(s, "Indicación: " + hint, (60, 420), 19, config.TEXT_DIM, max_width=W - 120)
        # estado y medidor de nivel
        if self.recorder.recording:
            level = min(1.0, self.recorder.level * 1.5)
            pygame.draw.rect(s, (30, 36, 46), (60, 520, 600, 18), border_radius=6)
            color = config.DANGER if level > 0.95 else config.AMBER
            pygame.draw.rect(s, color, (60, 520, int(600 * level), 18), border_radius=6)
            draw_text(s, "● GRABANDO", (680, 516), 22, config.DANGER, bold=True, shadow=False)
        elif self.take is not None and len(self.take):
            draw_text(s, f"Toma lista ({len(self.take) / RATE:.1f} s)", (60, 516), 22, (90, 170, 120), bold=True, shadow=False)
        draw_text(s, self.message, (60, 556), 20, config.TEXT, max_width=W - 120)
        font = get_font(17)
        keys = "ESPACIO grabar/detener   ·   P escuchar   ·   ENTER aceptar   ·   R repetir   ·   N saltar   ·   ESC salir"
        s.blit(font.render(keys, True, config.TEXT_DIM), (60, H - 50))
        pygame.display.flip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nahuat-only", action="store_true")
    parser.add_argument("--spanish-only", action="store_true")
    parser.add_argument("--speaker")
    parser.add_argument("--scene")
    parser.add_argument("--redo", action="store_true", help="Incluir líneas ya grabadas con voz humana")
    parser.add_argument("--list", action="store_true", help="Mostrar el plan y los micrófonos sin grabar")
    parser.add_argument("--mic", type=int, default=None, help="Índice del micrófono (ver --list)")
    args = parser.parse_args()

    pygame.init()
    items = build_items(args)
    if args.list:
        from pygame._sdl2 import audio as sdl_audio

        for i, name in enumerate(sdl_audio.get_audio_device_names(True)):
            print(f"  micrófono {i}: {name}")
        print(f"\n{len(items)} líneas por grabar:")
        for n, item in enumerate(items, 1):
            tag = "NÁHUAT " if item.nahuat_id else ""
            print(f"  {n:>3}. [{item.speaker}] {tag}{item.text}")
        return 0
    if not items:
        print("No hay líneas pendientes con esos filtros. Usa --redo para regrabar.")
        return 0
    pygame.mixer.quit()
    pygame.mixer.init(frequency=RATE, size=-16, channels=2)
    recorder = Recorder(args.mic)
    session = Session(items, recorder, Lexicon.load())
    done = session.run()
    (VOICE_DIR / "_preview.wav").unlink(missing_ok=True)
    pygame.quit()
    print(f"Tomas guardadas: {done}. Índice: {INDEX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
