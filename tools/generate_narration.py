"""Pregenera la narración y los diálogos en español con Piper TTS (local, sin conexión).

Ejecutar con el entorno de herramientas (Python 3.14 + piper-tts + onnxruntime):

    .venv-tts\\Scripts\\python tools\\generate_narration.py --sample     # 3 frases de prueba
    .venv-tts\\Scripts\\python tools\\generate_narration.py              # solo lo que falta o cambió
    .venv-tts\\Scripts\\python tools\\generate_narration.py --force      # regenerar todo
    .venv-tts\\Scripts\\python tools\\generate_narration.py --engine winrt   # respaldo: voces de Windows

Configuración de voces por personaje: yulu/assets/audio/voices.json.
Salida: yulu/assets/audio/voice/<clave>.wav e index.json (clave -> texto, locutor, modelo, hash).
Las frases en náhuat NO se sintetizan: se registran como pendientes de grabación humana en
yulu/assets/audio/voice/nahuat/ (ver yulu/audio/voice.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yulu.audio.voice import NAHUAT_DIR, is_human_recording_required, voice_filename  # noqa: E402
from yulu.narrative.scenes import NARRATOR, SCENES  # noqa: E402
from yulu.narrative.schema import DialogueLine  # noqa: E402
from yulu.paths import ASSETS_DIR, AUDIO_DIR  # noqa: E402

VOICE_DIR = AUDIO_DIR / "voice"
SAMPLES_DIR = VOICE_DIR / "samples"
CONFIG_PATH = AUDIO_DIR / "voices.json"
INDEX_PATH = VOICE_DIR / "index.json"
ERROR_LOG = VOICE_DIR / "errors.log"
WINRT_SCRIPT = Path(__file__).resolve().parent / "tts_sapi.ps1"
WINRT_VOICE_OF = {NARRATOR: "female", "Anciana": "female", "Guardia": "male", "Tú": "male", "Niño": "male"}


# ---------- datos ----------
def all_lines() -> list[DialogueLine]:
    lines: list[DialogueLine] = []
    for scene in SCENES.values():
        lines.extend(scene.lines)
        for choice in scene.choices:
            if choice.feedback:
                lines.append(DialogueLine(NARRATOR, choice.feedback))
    return lines


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def character_config(config: dict, speaker: str) -> dict:
    characters = config["characters"]
    return characters.get(speaker) or characters[config["default_character"]]


def config_hash(text: str, char_cfg: dict, engine: str) -> str:
    payload = json.dumps({"text": text, "cfg": char_cfg, "engine": engine}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]  # identificador, no criptografía


def prepare_text(text: str) -> str:
    """Ajusta la puntuación para que Piper respire: los puntos suspensivos se vuelven pausa."""
    text = text.replace("…", "...").replace("...", ". ")
    text = text.replace("«", "").replace("»", "")
    return " ".join(text.split())


# ---------- motores ----------
class PiperEngine:
    def __init__(self, config: dict) -> None:
        try:
            from piper import PiperVoice, SynthesisConfig  # type: ignore
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise SystemExit(
                "piper-tts no está instalado en este intérprete. Usa .venv-tts (Python 3.14); ver README, sección Narración."
            ) from exc
        self._PiperVoice = PiperVoice
        self._SynthesisConfig = SynthesisConfig
        self.models_dir = ASSETS_DIR / config["models_dir"]
        self.models_cfg = config["models"]
        self._loaded: dict[str, object] = {}

    def _voice(self, model_id: str):
        if model_id not in self._loaded:
            spec = self.models_cfg[model_id]
            path = self.models_dir / spec["file"]
            if not path.is_file() or not path.with_name(path.name + ".json").is_file():
                raise FileNotFoundError(f"Modelo {model_id} no encontrado en {self.models_dir} (faltan .onnx y/o .onnx.json)")
            self._loaded[model_id] = self._PiperVoice.load(str(path))
        return self._loaded[model_id]

    def synthesize(self, text: str, char_cfg: dict, target: Path, speaker: str = NARRATOR) -> None:
        voice = self._voice(char_cfg["model"])
        syn = self._SynthesisConfig(
            length_scale=float(char_cfg.get("length_scale", 1.0)),
            noise_scale=float(char_cfg.get("noise_scale", 0.667)),
            noise_w_scale=float(char_cfg.get("noise_w_scale", 0.8)),
            volume=float(char_cfg.get("volume", 1.0)),
        )
        silence = float(char_cfg.get("sentence_silence", 0.3))
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp.wav")
        with wave.open(str(tmp), "wb") as wav_file:
            try:
                voice.synthesize_wav(prepare_text(text), wav_file, syn_config=syn, sentence_silence=silence)
            except TypeError:  # versiones sin el parámetro sentence_silence
                voice.synthesize_wav(prepare_text(text), wav_file, syn_config=syn)
        pitch = float(char_cfg.get("pitch_factor", 1.0))
        if abs(pitch - 1.0) > 0.001:
            _apply_pitch_factor(tmp, pitch)
        tmp.replace(target)

    def flush(self) -> None:
        return None


def _apply_pitch_factor(path: Path, factor: float) -> None:
    """Reescribe la cabecera WAV con otra frecuencia de muestreo: < 1 = más grave y lento.

    No altera las muestras; el mezclador del juego remuestrea al reproducir. Es un recurso
    sencillo para diferenciar personajes con un mismo modelo, no una simulación de acento.
    """
    with wave.open(str(path), "rb") as src:
        params = src.getparams()
        frames = src.readframes(src.getnframes())
    with wave.open(str(path), "wb") as dst:
        dst.setparams(params)
        dst.setframerate(max(8000, int(params.framerate * factor)))
        dst.writeframes(frames)


class WinRTEngine:
    """Respaldo con las voces de Windows (Sabina / Raul) a través de tools/tts_sapi.ps1."""

    def __init__(self) -> None:
        self.jobs: list[dict] = []

    def synthesize(self, text: str, char_cfg: dict, target: Path, speaker: str = NARRATOR) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        self.jobs.append({"file": str(target), "text": prepare_text(text), "voice": WINRT_VOICE_OF.get(speaker, "female")})

    def flush(self) -> None:
        if not self.jobs:
            return
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(self.jobs, fh, ensure_ascii=False)
            job_file = fh.name
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(WINRT_SCRIPT), "-JobFile", job_file],
            capture_output=True, text=True,
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        self.jobs.clear()


# ---------- generación ----------
def log_error(message: str) -> None:
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {message}\n")
    print("  ERROR:", message)


def generate_samples(engine, config: dict) -> int:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    for i, sample in enumerate(config["samples"], 1):
        speaker = sample["speaker"]
        cfg = character_config(config, speaker)
        target = SAMPLES_DIR / f"muestra_{i}_{speaker.lower()}_{cfg['model']}.wav"
        try:
            engine.synthesize(sample["text"], cfg, target, speaker=speaker)
            print(f"  {target.name}")
        except Exception as exc:  # noqa: BLE001 - se registra y se continúa
            failures += 1
            log_error(f"muestra {speaker}: {exc}")
    engine.flush()
    print(f"\nMuestras en {SAMPLES_DIR}. Escúchalas antes de generar el resto.")
    return 1 if failures else 0


def generate_all(engine, config: dict, engine_name: str, force: bool) -> int:
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    (VOICE_DIR / NAHUAT_DIR).mkdir(exist_ok=True)
    old_index = json.loads(INDEX_PATH.read_text(encoding="utf-8")) if INDEX_PATH.exists() else {}
    index: dict[str, dict] = {}
    pending_nahuat: list[dict] = []
    todo: list[tuple[DialogueLine, str, dict]] = []
    for line in all_lines():
        filename = voice_filename(line)
        if filename in index:
            continue
        if is_human_recording_required(line):
            recorded = (VOICE_DIR / filename).exists()
            index[filename] = {
                "speaker": line.speaker, "text": line.text, "nahuat": True,
                "voice": "grabación humana" if recorded else None,
                "status": "grabada" if recorded else "pendiente de grabación humana",
            }
            if not recorded:
                pending_nahuat.append({"file": filename, "text": line.text})
            continue
        cfg = character_config(config, line.speaker)
        digest = config_hash(line.text, cfg, engine_name)
        voice_label = cfg["model"] if engine_name == "piper" else f"winrt:{WINRT_VOICE_OF.get(line.speaker, 'female')}"
        index[filename] = {"speaker": line.speaker, "text": line.text, "nahuat": False, "voice": voice_label, "hash": digest, "status": "generada"}
        unchanged = old_index.get(filename, {}).get("hash") == digest and (VOICE_DIR / filename).exists()
        if force or not unchanged:
            todo.append((line, filename, cfg))

    print(f"{len(index)} líneas distintas; {len(todo)} por sintetizar; {len(pending_nahuat)} en náhuat pendientes de grabación humana.")
    failures = 0
    for n, (line, filename, cfg) in enumerate(todo, 1):
        try:
            engine.synthesize(line.text, cfg, VOICE_DIR / filename, speaker=line.speaker)
            if n % 10 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            index[filename]["status"] = f"error: {exc}"
            log_error(f"{filename} ({line.speaker}): {exc}")
    engine.flush()
    index["_pending_nahuat"] = pending_nahuat
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    missing = [f for f, v in index.items() if not f.startswith("_") and not v["nahuat"] and not (VOICE_DIR / f).exists()]
    print(f"Hecho. Errores: {failures}. Archivos ausentes tras generar: {len(missing)}. Índice: {INDEX_PATH}")
    return 1 if failures or missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engine", choices=("piper", "winrt"), default="piper")
    parser.add_argument("--sample", action="store_true", help="Generar solo las frases de prueba de voices.json")
    parser.add_argument("--force", action="store_true", help="Regenerar aunque el hash no haya cambiado")
    args = parser.parse_args()
    config = load_config()
    engine = PiperEngine(config) if args.engine == "piper" else WinRTEngine()
    if args.sample:
        return generate_samples(engine, config)
    return generate_all(engine, config, args.engine, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
