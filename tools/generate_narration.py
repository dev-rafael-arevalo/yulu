"""Pregenera la narración en español con la voz SAPI5 de Windows (sin conexión).

Uso:  python tools/generate_narration.py [--force] [--voice "Microsoft Sabina Desktop"]

Recorre todas las líneas de diálogo y retroalimentaciones del capítulo, calcula el nombre
estable de archivo de cada una (ver yulu/audio/voice.py) y sintetiza las que falten en
yulu/assets/audio/voice/. Escribe además voice/index.json con la correspondencia.

Aviso: la voz es un sintetizador de español. Las frases en náhuat se leen con fonética
española aproximada; NO representan la pronunciación de hablantes nativos.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yulu.audio.voice import voice_filename  # noqa: E402
from yulu.narrative.scenes import CHILD, ELDER, GUARD, NARRATOR, SCENES, YOU  # noqa: E402
from yulu.narrative.schema import DialogueLine  # noqa: E402
from yulu.paths import AUDIO_DIR  # noqa: E402

VOICE_DIR = AUDIO_DIR / "voice"
SCRIPT = Path(__file__).resolve().parent / "tts_sapi.ps1"


def all_lines() -> list[DialogueLine]:
    lines: list[DialogueLine] = []
    for scene in SCENES.values():
        lines.extend(scene.lines)
        for choice in scene.choices:
            if choice.feedback:
                lines.append(DialogueLine(NARRATOR, choice.feedback))
    return lines


# Prosodia por personaje (SSML): ritmo, tono y volumen relativos a la voz base.
PROSODY: dict[str, dict[str, str]] = {
    NARRATOR: {"rate": "-12%", "pitch": "-4%", "volume": "medium"},
    YOU: {"rate": "-5%", "pitch": "+3%", "volume": "medium"},
    GUARD: {"rate": "+12%", "pitch": "-12%", "volume": "x-loud"},
    ELDER: {"rate": "-22%", "pitch": "-8%", "volume": "soft"},
    CHILD: {"rate": "+5%", "pitch": "+28%", "volume": "medium"},
}
DEFAULT_PROSODY = {"rate": "-8%", "pitch": "0%", "volume": "medium"}


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_ssml(line: DialogueLine) -> str:
    """Construye SSML con pausas en puntos suspensivos y énfasis en exclamaciones.

    Las frases en náhuat se leen más despacio y con una pausa previa, para que el jugador
    distinga que cambia la lengua. Sigue siendo una voz española: no es pronunciación nativa.
    """
    prosody = PROSODY.get(line.speaker, DEFAULT_PROSODY)
    text = _escape(line.text)
    text = text.replace("...", '<break time="650ms"/>').replace("…", '<break time="650ms"/>')
    text = text.replace(". ", '.<break time="380ms"/> ').replace("? ", '?<break time="320ms"/> ').replace("! ", '!<break time="320ms"/> ')
    if line.text.endswith("!") or line.text.endswith("?!"):
        text = f'<emphasis level="strong">{text}</emphasis>'
    rate, pitch = prosody["rate"], prosody["pitch"]
    if line.nahuat_id:
        rate = "-30%"
        text = '<break time="250ms"/>' + text
    body = f'<prosody rate="{rate}" pitch="{pitch}" volume="{prosody["volume"]}">{text}</prosody>'
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-MX">'
        f"{body}</speak>"
    )


def build_jobs(force: bool) -> tuple[list[dict], dict[str, dict]]:
    jobs: list[dict] = []
    index: dict[str, dict] = {}
    for line in all_lines():
        filename = voice_filename(line)
        if filename in index:
            continue
        index[filename] = {"speaker": line.speaker, "text": line.text, "nahuat": bool(line.nahuat_id)}
        target = VOICE_DIR / filename
        if force or not target.exists():
            jobs.append({"file": str(target), "text": line.text, "ssml": build_ssml(line)})
    return jobs, index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="Regenerar aunque el archivo exista")
    parser.add_argument("--voice", default="Microsoft Sabina Desktop", help="Nombre de la voz SAPI5")
    args = parser.parse_args()

    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    jobs, index = build_jobs(args.force)
    (VOICE_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(index)} líneas distintas; {len(jobs)} por sintetizar.")
    if not jobs:
        return 0
    if sys.platform != "win32":
        print("La síntesis SAPI5 solo está disponible en Windows. Copia los WAV generados en otra máquina.")
        return 1
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(jobs, fh, ensure_ascii=False)
        job_file = fh.name
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-JobFile", job_file, "-Voice", args.voice]
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
        return result.returncode
    missing = [j["file"] for j in jobs if not Path(j["file"]).exists()]
    if missing:
        print(f"ADVERTENCIA: {len(missing)} archivos no se generaron.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
