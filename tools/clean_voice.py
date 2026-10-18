"""Limpia las grabaciones humanas: reduce el ruido de fondo, filtra graves, iguala el nivel
y las deja a 22 050 Hz, el formato de la narración del juego.

Ejecutar con el entorno de herramientas (tiene numpy):
    .venv-tts\\Scripts\\python tools\\clean_voice.py            # todas las grabaciones humanas
    .venv-tts\\Scripts\\python tools\\clean_voice.py --strength 1.2   # reducción más suave (por defecto 1.6)
    .venv-tts\\Scripts\\python tools\\clean_voice.py --only nahuat/tekwani.wav

Los originales se guardan una sola vez en voice/raw/ y el procesado siempre parte de ellos,
así que se puede repetir con otros parámetros sin degradar nada.

Método (sin dependencias externas salvo numpy):
1. Perfil de ruido: espectro medio de los tramos más silenciosos de la propia toma.
2. Puerta espectral por tramas (STFT de 2048 muestras, salto 512): se atenúa cada banda en
   proporción a cuánto supera el ruido, con un suelo de -24 dB y suavizado en tiempo y
   frecuencia para evitar el "ruido musical".
3. Filtro paso alto a 85 Hz (golpes, zumbido) y paso bajo a 10 kHz.
4. Normalización a -20 dBFS RMS con pico máximo -1 dBFS, fundidos de 15 ms y remuestreo a 22 050 Hz.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.paths import AUDIO_DIR  # noqa: E402

VOICE_DIR = AUDIO_DIR / "voice"
RAW_DIR = VOICE_DIR / "raw"
INDEX_PATH = VOICE_DIR / "index.json"
TARGET_RATE = 22050
FRAME, HOP = 2048, 512
HIGHPASS_HZ, LOWPASS_HZ = 85.0, 10000.0
FLOOR_DB = -24.0
PRESETS = {
    # suave: solo reducción de ruido moderada (como la primera pasada)
    "suave": dict(strength=1.6, floor_db=-24.0, gate_db=None, presence_db=0.0, compress=False, reverb=0.0),
    # estudio: ruido muy reducido, silencios cerrados del todo, presencia, compresión y sala corta
    "estudio": dict(strength=2.6, floor_db=-42.0, gate_db=-46.0, presence_db=3.5, compress=True, reverb=0.10),
}
TARGET_RMS_DB, PEAK_DB = -20.0, -1.0


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def write_wav(path: Path, samples: np.ndarray, rate: int) -> None:
    pcm = np.clip(samples * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def stft(x: np.ndarray) -> np.ndarray:
    window = np.hanning(FRAME)
    pad = np.concatenate([np.zeros(FRAME // 2), x, np.zeros(FRAME)])
    frames = 1 + (len(pad) - FRAME) // HOP
    idx = np.arange(FRAME)[None, :] + HOP * np.arange(frames)[:, None]
    return np.fft.rfft(pad[idx] * window, axis=1)


def istft(spec: np.ndarray, length: int) -> np.ndarray:
    window = np.hanning(FRAME)
    frames = spec.shape[0]
    out = np.zeros(FRAME + HOP * (frames - 1))
    norm = np.zeros_like(out)
    chunks = np.fft.irfft(spec, n=FRAME, axis=1) * window
    for i in range(frames):
        out[i * HOP: i * HOP + FRAME] += chunks[i]
        norm[i * HOP: i * HOP + FRAME] += window ** 2
    out /= np.maximum(norm, 1e-6)
    return out[FRAME // 2: FRAME // 2 + length]


def spectral_gate(x: np.ndarray, rate: int, strength: float, floor_db: float = FLOOR_DB, presence_db: float = 0.0) -> np.ndarray:
    spec = stft(x)
    mag = np.abs(spec)
    energy = mag.mean(axis=1)
    quiet = mag[energy <= np.percentile(energy, 15)]
    noise = quiet.mean(axis=0) if len(quiet) else mag.min(axis=0)
    floor = 10 ** (floor_db / 20)
    gain = np.clip((mag - strength * noise[None, :]) / np.maximum(mag, 1e-9), floor, 1.0)
    # suavizado temporal (3 tramas) y en frecuencia (5 bandas) contra el ruido musical
    kernel_t = np.ones(3) / 3
    kernel_f = np.ones(5) / 5
    gain = np.apply_along_axis(lambda g: np.convolve(g, kernel_t, mode="same"), 0, gain)
    gain = np.apply_along_axis(lambda g: np.convolve(g, kernel_f, mode="same"), 1, gain)
    freqs = np.fft.rfftfreq(FRAME, 1 / rate)
    band = ((freqs >= HIGHPASS_HZ) & (freqs <= LOWPASS_HZ)).astype(float)
    band = np.convolve(band, np.ones(3) / 3, mode="same")
    if presence_db:
        # realce de presencia (inteligibilidad) entre 2 y 4,5 kHz
        bump = np.exp(-((freqs - 3200.0) / 1100.0) ** 2) * (10 ** (presence_db / 20) - 1)
        band = band * (1 + bump)
    return istft(spec * gain * band[None, :], len(x))


def time_gate(x: np.ndarray, rate: int, gate_db: float, attack_ms: float = 8, release_ms: float = 90) -> np.ndarray:
    """Silencia del todo los huecos entre frases: envolvente RMS con ataque rápido y liberación lenta."""
    win = max(1, int(rate * 0.01))
    power = np.convolve(x ** 2, np.ones(win) / win, mode="same")
    level_db = 10 * np.log10(power + 1e-12)
    target = (level_db > gate_db).astype(float)
    a_att, a_rel = np.exp(-1 / (rate * attack_ms / 1000)), np.exp(-1 / (rate * release_ms / 1000))
    env = np.empty_like(target)
    g = 0.0
    for i, t in enumerate(target):
        g = t + (g - t) * (a_att if t > g else a_rel)
        env[i] = g
    return x * (0.02 + 0.98 * env)


def compress(x: np.ndarray, rate: int, threshold_db: float = -24.0, ratio: float = 2.5) -> np.ndarray:
    """Compresión suave para igualar sílabas fuertes y débiles."""
    win = int(rate * 0.03)
    env = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode="same") + 1e-12)
    env_db = 20 * np.log10(env)
    over = np.maximum(env_db - threshold_db, 0.0)
    gain_db = -over * (1 - 1 / ratio)
    return x * 10 ** (gain_db / 20)


def small_room(x: np.ndarray, rate: int, mix: float) -> np.ndarray:
    """Reverberación corta de sala (algunas reflexiones tempranas amortiguadas)."""
    if mix <= 0:
        return x
    out = x.copy()
    for delay_ms, gain in ((13, 0.45), (23, 0.35), (37, 0.28), (53, 0.2), (79, 0.14), (113, 0.09)):
        d = int(rate * delay_ms / 1000)
        out[d:] += x[:-d] * gain * mix
    return out


def normalize(x: np.ndarray) -> np.ndarray:
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    gain = 10 ** (TARGET_RMS_DB / 20) / rms
    peak = np.max(np.abs(x)) * gain
    gain = min(gain, 10 ** (PEAK_DB / 20) / max(peak / gain, 1e-9))
    y = x * gain
    fade = int(0.015 * TARGET_RATE)
    ramp = np.linspace(0, 1, fade)
    y[:fade] *= ramp
    y[-fade:] *= ramp[::-1]
    return y


def resample(x: np.ndarray, rate: int) -> np.ndarray:
    if rate == TARGET_RATE:
        return x
    n_out = int(round(len(x) * TARGET_RATE / rate))
    spec = np.fft.rfft(x)
    keep = n_out // 2 + 1
    spec = spec[:keep] if keep <= len(spec) else np.pad(spec, (0, keep - len(spec)))
    return np.fft.irfft(spec, n=n_out) * (n_out / len(x))


def noise_floor_db(x: np.ndarray, rate: int) -> float:
    win = int(0.2 * rate)
    if len(x) < win * 2:
        return -120.0
    blocks = [np.sqrt(np.mean(x[i: i + win] ** 2)) for i in range(0, len(x) - win, win // 2)]
    return float(20 * np.log10(min(blocks) + 1e-9))


def process(path: Path, preset: dict) -> tuple[float, float]:
    raw_path = RAW_DIR / path.relative_to(VOICE_DIR)
    if not raw_path.exists():
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, raw_path)
    x, rate = read_wav(raw_path)
    before = noise_floor_db(x, rate)
    y = spectral_gate(x, rate, preset["strength"], preset["floor_db"], preset["presence_db"])
    if preset["gate_db"] is not None:
        y = time_gate(y, rate, preset["gate_db"])
    if preset["compress"]:
        y = compress(y, rate)
    y = small_room(y, rate, preset["reverb"])
    y = resample(y, rate)
    y = normalize(y)
    write_wav(path, y, TARGET_RATE)
    return before, noise_floor_db(y, TARGET_RATE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="estudio", help="Conjunto de ajustes (por defecto: estudio)")
    parser.add_argument("--strength", type=float, default=None, help="Sobrescribe el factor de sustracción del ruido del preajuste")
    parser.add_argument("--only", help="Procesar solo este archivo (ruta relativa a voice/)")
    args = parser.parse_args()
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    targets = [k for k, v in index.items() if not k.startswith("_") and str(v.get("voice", "")).startswith("grabación humana")]
    if args.only:
        targets = [t for t in targets if t == args.only]
    preset = dict(PRESETS[args.preset])
    if args.strength is not None:
        preset["strength"] = args.strength
    done = 0
    improvements = []
    for name in targets:
        path = VOICE_DIR / name
        if not path.exists():
            print(f"  FALTA {name}")
            continue
        before, after = process(path, preset)
        improvements.append(before - after)
        index[name]["processed"] = {"preset": args.preset, **preset, "rate": TARGET_RATE, "noise_floor_db": round(after, 1)}
        done += 1
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    if improvements:
        print(f"{done} archivos limpiados. Suelo de ruido reducido en promedio {np.mean(improvements):.1f} dB (mín {min(improvements):.1f}, máx {max(improvements):.1f}).")
    print(f"Originales conservados en {RAW_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
