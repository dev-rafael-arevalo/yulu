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


def spectral_gate(x: np.ndarray, rate: int, strength: float) -> np.ndarray:
    spec = stft(x)
    mag = np.abs(spec)
    energy = mag.mean(axis=1)
    quiet = mag[energy <= np.percentile(energy, 15)]
    noise = quiet.mean(axis=0) if len(quiet) else mag.min(axis=0)
    floor = 10 ** (FLOOR_DB / 20)
    gain = np.clip((mag - strength * noise[None, :]) / np.maximum(mag, 1e-9), floor, 1.0)
    # suavizado temporal (3 tramas) y en frecuencia (5 bandas) contra el ruido musical
    kernel_t = np.ones(3) / 3
    kernel_f = np.ones(5) / 5
    gain = np.apply_along_axis(lambda g: np.convolve(g, kernel_t, mode="same"), 0, gain)
    gain = np.apply_along_axis(lambda g: np.convolve(g, kernel_f, mode="same"), 1, gain)
    freqs = np.fft.rfftfreq(FRAME, 1 / rate)
    band = ((freqs >= HIGHPASS_HZ) & (freqs <= LOWPASS_HZ)).astype(float)
    band = np.convolve(band, np.ones(3) / 3, mode="same")
    return istft(spec * gain * band[None, :], len(x))


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


def process(path: Path, strength: float) -> tuple[float, float]:
    raw_path = RAW_DIR / path.relative_to(VOICE_DIR)
    if not raw_path.exists():
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, raw_path)
    x, rate = read_wav(raw_path)
    before = noise_floor_db(x, rate)
    y = spectral_gate(x, rate, strength)
    y = resample(y, rate)
    y = normalize(y)
    write_wav(path, y, TARGET_RATE)
    return before, noise_floor_db(y, TARGET_RATE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strength", type=float, default=1.6, help="Factor de sustracción del ruido (1.0 suave, 2.0 agresivo)")
    parser.add_argument("--only", help="Procesar solo este archivo (ruta relativa a voice/)")
    args = parser.parse_args()
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    targets = [k for k, v in index.items() if not k.startswith("_") and str(v.get("voice", "")).startswith("grabación humana")]
    if args.only:
        targets = [t for t in targets if t == args.only]
    done = 0
    improvements = []
    for name in targets:
        path = VOICE_DIR / name
        if not path.exists():
            print(f"  FALTA {name}")
            continue
        before, after = process(path, args.strength)
        improvements.append(before - after)
        index[name]["processed"] = {"strength": args.strength, "rate": TARGET_RATE, "noise_floor_db": round(after, 1)}
        done += 1
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    if improvements:
        print(f"{done} archivos limpiados. Suelo de ruido reducido en promedio {np.mean(improvements):.1f} dB (mín {min(improvements):.1f}, máx {max(improvements):.1f}).")
    print(f"Originales conservados en {RAW_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
