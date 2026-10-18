"""Genera únicamente las señales de interfaz (ui_*) por síntesis, sin dependencias externas.

Los ambientes, criaturas, efectos y música del juego son grabaciones con licencia
(ver yulu/assets/audio/CREDITS.md); este script ya no los produce.

Uso:  python tools/generate_sounds.py [--force]

Los archivos se escriben en yulu/assets/audio/{ambient,sfx,music}/ como WAV mono de 16 bits
a 22 050 Hz. Son sustitutos sintéticos claramente provisionales: sirven para que el juego
suene completo sin conexión y pueden reemplazarse por grabaciones con licencia compatible
conservando los nombres de archivo.
"""
from __future__ import annotations

import math
import random
import struct
import sys
import wave
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.paths import AUDIO_DIR  # noqa: E402

SR = 22050
RNG = random.Random(2026)


# ---------- utilidades de síntesis ----------
def silence(seconds: float) -> list[float]:
    return [0.0] * int(SR * seconds)


def add(target: list[float], source: list[float], at: float = 0.0, gain: float = 1.0) -> None:
    start = int(at * SR)
    for i, v in enumerate(source):
        j = start + i
        if 0 <= j < len(target):
            target[j] += v * gain


def sine(freq: float, seconds: float, phase: float = 0.0) -> list[float]:
    step = 2 * math.pi * freq / SR
    return [math.sin(phase + step * i) for i in range(int(SR * seconds))]


def saw(freq: float, seconds: float) -> list[float]:
    period = SR / freq
    return [2 * ((i / period) % 1.0) - 1 for i in range(int(SR * seconds))]


def noise(seconds: float) -> list[float]:
    return [RNG.uniform(-1, 1) for _ in range(int(SR * seconds))]


def lowpass(signal: list[float], cutoff: float) -> list[float]:
    rc = 1 / (2 * math.pi * cutoff)
    alpha = (1 / SR) / (rc + 1 / SR)
    out, prev = [], 0.0
    for v in signal:
        prev += alpha * (v - prev)
        out.append(prev)
    return out


def highpass(signal: list[float], cutoff: float) -> list[float]:
    return [v - l for v, l in zip(signal, lowpass(signal, cutoff))]


def envelope(signal: list[float], attack: float, decay: float, sustain: float = 0.0) -> list[float]:
    n = len(signal)
    a, d = int(attack * SR), int(decay * SR)
    out = []
    for i, v in enumerate(signal):
        if i < a:
            g = i / max(1, a)
        elif i < a + d:
            g = 1 - (1 - sustain) * (i - a) / max(1, d)
        else:
            g = sustain
        out.append(v * g)
    return out


def fade_edges(signal: list[float], seconds: float = 0.02) -> list[float]:
    n = int(seconds * SR)
    out = list(signal)
    for i in range(min(n, len(out))):
        g = i / n
        out[i] *= g
        out[-1 - i] *= g
    return out


def make_loop(signal: list[float], crossfade: float = 1.0) -> list[float]:
    """Funde el final sobre el principio para que el bucle no tenga corte audible."""
    n = int(crossfade * SR)
    body = signal[: len(signal) - n]
    tail = signal[len(signal) - n :]
    for i in range(n):
        g = i / n
        body[i] = body[i] * g + tail[i] * (1 - g)
    return body


def tremolo(signal: list[float], rate: float, depth: float) -> list[float]:
    return [v * (1 - depth + depth * 0.5 * (1 + math.sin(2 * math.pi * rate * i / SR))) for i, v in enumerate(signal)]


def normalize(signal: list[float], peak: float = 0.85) -> list[float]:
    m = max(1e-6, max(abs(v) for v in signal))
    return [v * peak / m for v in signal]


def write_wav(path: Path, signal: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in signal))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(data.tobytes())


# ---------- ambientes (bucles) ----------
def insects() -> list[float]:
    out = silence(9.0)
    add(out, lowpass(noise(9.0), 6000), gain=0.03)
    for _ in range(140):
        f = RNG.uniform(3200, 5200)
        chirp = envelope(sine(f, 0.06), 0.005, 0.05)
        chirp = tremolo(chirp, RNG.uniform(60, 120), 0.9)
        add(out, chirp, at=RNG.uniform(0, 8.9), gain=RNG.uniform(0.05, 0.16))
    return normalize(make_loop(out), 0.6)


def wind() -> list[float]:
    base = lowpass(noise(11.0), 400)
    out = [v * (0.55 + 0.45 * math.sin(2 * math.pi * 0.09 * i / SR + 1.0)) for i, v in enumerate(base)]
    return normalize(make_loop(out), 0.7)


def heartbeat() -> list[float]:
    out = silence(4.0)
    for beat in range(4):
        t = beat * 1.0
        add(out, envelope(sine(55, 0.25), 0.005, 0.22), at=t, gain=1.0)
        add(out, envelope(sine(48, 0.2), 0.005, 0.18), at=t + 0.28, gain=0.7)
    return normalize(make_loop(out, 0.3), 0.8)


def drum() -> list[float]:
    out = silence(6.0)
    for hit in range(8):
        t = hit * 0.75
        body = envelope(sine(78, 0.5), 0.002, 0.45)
        click = envelope(highpass(noise(0.03), 2000), 0.001, 0.025)
        add(out, body, at=t, gain=0.9 if hit % 2 == 0 else 0.6)
        add(out, click, at=t, gain=0.2)
    return normalize(make_loop(out, 0.3), 0.75)


def fire() -> list[float]:
    out = lowpass(noise(9.0), 900)
    out = [v * 0.35 for v in out]
    for _ in range(90):
        pop = envelope(highpass(noise(0.02), 1500), 0.001, 0.018)
        add(out, pop, at=RNG.uniform(0, 8.9), gain=RNG.uniform(0.2, 0.7))
    return normalize(make_loop(out), 0.7)


def birds() -> list[float]:
    out = silence(10.0)
    for _ in range(26):
        f0 = RNG.uniform(1800, 3600)
        n = int(SR * 0.18)
        chirp = [math.sin(2 * math.pi * (f0 + 900 * math.sin(math.pi * i / n)) * i / SR) for i in range(n)]
        chirp = envelope(chirp, 0.01, 0.16)
        t = RNG.uniform(0, 9.7)
        for k in range(RNG.randint(1, 3)):
            add(out, chirp, at=t + k * 0.22, gain=RNG.uniform(0.12, 0.3))
    add(out, lowpass(noise(10.0), 300), gain=0.08)
    return normalize(make_loop(out), 0.65)


def tension() -> list[float]:
    a = sine(55, 9.0)
    b = sine(58.5, 9.0)
    c = lowpass(noise(9.0), 250)
    out = [0.5 * x + 0.5 * y + 0.5 * z for x, y, z in zip(a, b, c)]
    return normalize(make_loop(out), 0.7)


# ---------- efectos ----------
def footsteps() -> list[float]:
    out = silence(1.6)
    for i in range(4):
        step = envelope(lowpass(noise(0.12), 600), 0.004, 0.11)
        add(out, step, at=i * 0.38, gain=RNG.uniform(0.6, 1.0))
    return normalize(out, 0.7)


def branch_snap() -> list[float]:
    out = envelope(highpass(noise(0.18), 900), 0.001, 0.16)
    add(out, envelope(lowpass(noise(0.08), 500), 0.001, 0.07), gain=0.8)
    return normalize(fade_edges(out), 0.8)


def growl(seed_freq: float, seconds: float) -> list[float]:
    base = saw(seed_freq, seconds)
    base = tremolo(base, 24.0, 0.8)
    rough = lowpass([v + 0.5 * n for v, n in zip(base, noise(seconds))], 700)
    return normalize(envelope(rough, 0.12, seconds - 0.12), 0.8)


def roar() -> list[float]:
    n = int(SR * 2.2)
    sig = []
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = 85 + 70 * math.sin(math.pi * t) ** 0.7
        phase += 2 * math.pi * freq / SR
        sig.append(2 * ((phase / (2 * math.pi)) % 1.0) - 1)
    sig = tremolo(sig, 30.0, 0.6)
    sig = lowpass([v + 0.7 * nz for v, nz in zip(sig, noise(2.2))], 900)
    return normalize(envelope(sig, 0.08, 2.1), 0.9)


def ui_move() -> list[float]:
    return normalize(fade_edges(envelope(sine(640, 0.05), 0.003, 0.045)), 0.4)


def ui_confirm() -> list[float]:
    out = silence(0.22)
    add(out, envelope(sine(520, 0.1), 0.003, 0.09))
    add(out, envelope(sine(780, 0.12), 0.003, 0.11), at=0.09)
    return normalize(fade_edges(out), 0.5)


def learn_chime() -> list[float]:
    out = silence(1.4)
    for i, f in enumerate((659.3, 830.6, 987.8)):
        tone = [a + 0.3 * b for a, b in zip(sine(f, 0.9), sine(f * 2, 0.9))]
        add(out, envelope(tone, 0.005, 0.85), at=i * 0.14, gain=0.6)
    return normalize(out, 0.6)


def tick() -> list[float]:
    return normalize(fade_edges(envelope(sine(1000, 0.03), 0.001, 0.028)), 0.5)


def dawn_birds() -> list[float]:
    return normalize(birds()[: int(SR * 3.5)], 0.6)


# ---------- música (bucles) ----------
def pad(freqs: list[float], seconds: float, lfo: float, brightness: float) -> list[float]:
    out = silence(seconds)
    for k, f in enumerate(freqs):
        voice = [a + brightness * 0.4 * b + brightness * 0.15 * c for a, b, c in zip(sine(f, seconds), sine(f * 2 + 0.3, seconds), sine(f * 3, seconds))]
        voice = tremolo(voice, lfo * (1 + 0.13 * k), 0.35)
        add(out, voice, gain=1.0 / len(freqs))
    return normalize(make_loop(out, 2.0), 0.6)


def night_drone() -> list[float]:
    return pad([55.0, 82.4, 110.0, 130.8], 18.0, lfo=0.07, brightness=0.3)


def dawn_theme() -> list[float]:
    return pad([98.0, 130.8, 164.8, 196.0, 246.9], 18.0, lfo=0.11, brightness=0.7)


SOUNDS: dict[str, dict[str, callable]] = {
    "ui": {"ui_move": ui_move, "ui_confirm": ui_confirm, "learn_chime": learn_chime, "tick": tick},
}


def main(force: bool = False) -> int:
    written = skipped = 0
    for category, items in SOUNDS.items():
        for name, builder in items.items():
            path = AUDIO_DIR / category / f"{name}.wav"
            if path.exists() and not force:
                skipped += 1
                continue
            write_wav(path, builder())
            written += 1
            print(f"  {category}/{name}.wav")
    print(f"\n{written} archivos generados, {skipped} ya existían (usa --force para regenerar).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(force="--force" in sys.argv))
