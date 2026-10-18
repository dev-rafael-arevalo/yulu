"""Genera `yulu/assets/audio/manifest.json` y `CREDITS.md` a partir de la tabla de recursos.

Uso:  python tools/build_audio_manifest.py

La tabla ENTRIES es la fuente de verdad de licencias y atribuciones. Cada entrada se
verificó el 18/10/2026 en la página de origen indicada; `license_verified` solo es True
cuando la página se pudo abrir y mostraba la licencia. Los archivos de Freesound se
obtuvieron a través de la API de Openverse, que sirve la vista previa MP3 de alta calidad
(128 kb/s) de cada sonido; no se descargó el original porque exige cuenta en Freesound.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yulu.paths import AUDIO_DIR  # noqa: E402

DATE = "2026-10-18"
CC0 = ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")
BY4 = ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")
OPENVERSE_NOTE = "Descargado mediante la API de Openverse (vista previa MP3 HQ de Freesound). Sin ediciones."


def fs(sound_id: int, user: str) -> str:
    return f"https://freesound.org/people/{user}/sounds/{sound_id}/"


# id, archivo, categoría, ganancia base, bucle, escenas, título, autor, url, (licencia, url), verificada, notas
ENTRIES: list[dict] = [
    dict(id="jungla_noche_densa", file="ambient/jungla_noche_densa.mp3", category="ambient", gain=0.55, loop=True,
         scenes=["s1_*", "s4_* (atenuado)"], title="noche_Lacandona.wav", author="nicotep", url=fs(619310, "nicotep"), lic=CC0, verified=True,
         notes="Selva Lacandona (Chiapas, México), 2015. Insectos nocturnos. " + OPENVERSE_NOTE),
    dict(id="jungla_noche_abierta", file="ambient/jungla_noche_abierta.mp3", category="ambient", gain=0.45, loop=True,
         scenes=["s2_*", "s3_*"], title="Costa Rica cloud forest at night.wav", author="sethlind", url=fs(332722, "sethlind"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound; página no abierta individualmente. " + OPENVERSE_NOTE),
    dict(id="lluvia_ligera", file="ambient/lluvia_ligera.mp3", category="ambient", gain=0.3, loop=True,
         scenes=["s2_persecucion", "s2_rio"], title="Tropical Rain - light in a forest with drop hitting the leaves", author="nyoz", url=fs(615747, "nyoz"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound. " + OPENVERSE_NOTE),
    dict(id="viento_suave", file="ambient/viento_suave.mp3", category="ambient", gain=0.3, loop=True,
         scenes=["s1_*", "s5_*"], title="G56-26-Steady Blowing Wind.wav", author="craigsmith", url=fs(438881, "craigsmith"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound. " + OPENVERSE_NOTE),
    dict(id="viento_aullante", file="ambient/viento_aullante.mp3", category="ambient", gain=0.35, loop=True,
         scenes=["s2_*"], title="Howling Wind", author="Fission9", url=fs(521736, "Fission9"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound. " + OPENVERSE_NOTE),
    dict(id="aldea_distante", file="ambient/aldea_distante.mp3", category="ambient", gain=0.35, loop=True,
         scenes=["s2_claro", "s3_*", "s4_*"], title="geroezemoes.wav", author="gecop", url=fs(640254, "gecop"), lic=CC0, verified=True,
         notes="Murmullo lejano e ininteligible de un grupo hablando flamenco, grabado en interior. Se usa filtrado por volumen como bullicio tras la empalizada. " + OPENVERSE_NOTE),
    dict(id="amanecer_aves", file="ambient/amanecer_aves.mp3", category="ambient", gain=0.5, loop=True,
         scenes=["s5_final_*"], title="Rainforest Morning Chorus.wav", author="digifishmusic", url=fs(57608, "digifishmusic"), lic=BY4, verified=True,
         notes="Coro matinal de selva australiana (Crater Lakes), no centroamericana. " + OPENVERSE_NOTE),
    dict(id="jaguar_sierra", file="creatures/jaguar_sierra.flac", category="creatures", gain=0.9, loop=False,
         scenes=["señales aleatorias con amenaza >= 20"], title="Jaguar saw", author="About Zoos", url="https://commons.wikimedia.org/w/index.php?curid=112996041", lic=BY4, verified=True,
         notes="Vocalización real de jaguar (Panthera onca), Attica Zoological Park. Fuente original: vídeo de About Zoos. Descargado de Wikimedia Commons sin ediciones."),
    dict(id="felino_grunido", file="creatures/felino_grunido.mp3", category="creatures", gain=0.8, loop=False,
         scenes=["señales aleatorias", "amenaza alta"], title="Tiger Growl", author="peenois", url=fs(496131, "peenois"), lic=CC0, verified=False,
         notes="Gruñido de tigre usado como gran felino compatible: no se encontró gruñido largo de jaguar con licencia verificable. " + OPENVERSE_NOTE),
    dict(id="felino_rugido_ataque", file="creatures/felino_rugido_ataque.mp3", category="creatures", gain=1.0, loop=False,
         scenes=["subidas bruscas de amenaza", "s4_alarma", "final en soledad"], title="Tiger Roar", author="lauramellis", url=fs(263115, "lauramellis"), lic=CC0, verified=False,
         notes="Rugido de tigre como sustituto del ataque; limitación documentada. " + OPENVERSE_NOTE),
    dict(id="fogata_crepitante", file="effects/fogata_crepitante.mp3", category="effects", gain=0.6, loop=True,
         scenes=["s4_*", "s5_decision"], title="Crackling Fire", author="Sauron974", url=fs(204348, "Sauron974"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound. " + OPENVERSE_NOTE),
    dict(id="fogata_cercana_loop", file="effects/fogata_cercana_loop.mp3", category="effects", gain=0.5, loop=True,
         scenes=["s4_fuego"], title="Ambiance_Campfire_Loop_Stereo.wav", author="Nox_Sound", url=fs(558967, "Nox_Sound"), lic=CC0, verified=True,
         notes="Grabación cercana de hoguera, pensada para bucle. " + OPENVERSE_NOTE),
    dict(id="antorcha", file="effects/antorcha.mp3", category="effects", gain=0.45, loop=True,
         scenes=["s2_claro", "s3_*"], title="maple fire", author="Nivatius", url=fs(519520, "Nivatius"), lic=CC0, verified=False,
         notes="Fuego de leña usado como antorchas en segundo plano. " + OPENVERSE_NOTE),
    dict(id="tambor_lento", file="effects/tambor_lento.mp3", category="effects", gain=0.3, loop=True,
         scenes=["s2_claro", "s3_*"], title="Shaman Hand Frame Drumming 01", author="Jagadamba", url=fs(257182, "Jagadamba"), lic=BY4, verified=True,
         notes="Tambor de marco grabado en estudio. No es una reconstrucción de música pipil. " + OPENVERSE_NOTE),
    dict(id="tambor_persecucion", file="effects/tambor_persecucion.mp3", category="effects", gain=0.45, loop=True,
         scenes=["s2_persecucion (capa de tensión)", "s4_alarma"], title="Shaman Hand Frame Drumming 04", author="Jagadamba", url=fs(257183, "Jagadamba"), lic=BY4, verified=True,
         notes="Tambor de marco grabado en estudio. No es una reconstrucción de música pipil. " + OPENVERSE_NOTE),
    dict(id="pasos_hojarasca", file="effects/pasos_hojarasca.mp3", category="effects", gain=0.6, loop=False,
         scenes=["transiciones de escena"], title="Footsteps / Walking on foliage in a forest", author="Dominik_W", url=fs(398685, "Dominik_W"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound. " + OPENVERSE_NOTE),
    dict(id="vegetacion", file="effects/vegetacion.mp3", category="effects", gain=0.5, loop=False,
         scenes=["movimiento del jaguar entre la vegetación"], title="Rustle walking by the leaves.wav", author="Magdaadga", url=fs(420404, "Magdaadga"), lic=CC0, verified=False,
         notes="Licencia según metadatos de Openverse/Freesound. " + OPENVERSE_NOTE),
    dict(id="exploracion", file="music/exploracion.mp3", category="music", gain=0.5, loop=True,
         scenes=["s1_*", "s2_claro", "s3_*", "s4_refugio", "s4_sed", "s4_fuego"], title="Dark ambient drone sound", author="martinbeltov", url=fs(244196, "martinbeltov"), lic=CC0, verified=True,
         notes="Dron oscuro de síntesis (pad). " + OPENVERSE_NOTE),
    dict(id="persecucion", file="music/persecucion.mp3", category="music", gain=0.55, loop=True,
         scenes=["s2_persecucion", "s2_corrida", "s2_paralizado", "s3_tekwani", "s4_alarma"], title="Horror-Suspense Drone Texture", author="Hybrid_V", url=fs(320830, "Hybrid_V"), lic=BY4, verified=True,
         notes="La página muestra 'Attribution 4.0' y, en otro punto, 'Attribution 3.0'; se atribuye bajo CC BY 4.0, que cumple ambas. Capas de sintetizador y banjo preparado. " + OPENVERSE_NOTE),
    dict(id="desenlace_aldea", file="music/desenlace_aldea.mp3", category="music", gain=0.5, loop=True,
         scenes=["s5_final_aldea"], title="Mystical Guitar Atmosphere", author="MichiJung", url=fs(719441, "MichiJung"), lic=BY4, verified=True,
         notes="Atmósfera de guitarra procesada, calma. " + OPENVERSE_NOTE),
    dict(id="desenlace_solo", file="music/desenlace_solo.mp3", category="music", gain=0.5, loop=True,
         scenes=["s5_final_solo"], title="Deep Cinematic Rumble Stereo", author="PatrickLieberkind", url=fs(207555, "PatrickLieberkind"), lic=BY4, verified=True,
         notes="Rumor grave cinematográfico. " + OPENVERSE_NOTE),
    dict(id="ui_move", file="ui/ui_move.wav", category="ui", gain=0.35, loop=False, scenes=["menús"], title="ui_move (síntesis propia)", author="Proyecto YULU", url="tools/generate_sounds.py", lic=("Propio (sin restricciones)", ""), verified=True,
         notes="Breve señal de interfaz generada por código; no es sonido ambiental."),
    dict(id="ui_confirm", file="ui/ui_confirm.wav", category="ui", gain=0.4, loop=False, scenes=["confirmar decisión"], title="ui_confirm (síntesis propia)", author="Proyecto YULU", url="tools/generate_sounds.py", lic=("Propio (sin restricciones)", ""), verified=True,
         notes="Señal de interfaz generada por código."),
    dict(id="learn_chime", file="ui/learn_chime.wav", category="ui", gain=0.5, loop=False, scenes=["nueva expresión aprendida"], title="learn_chime (síntesis propia)", author="Proyecto YULU", url="tools/generate_sounds.py", lic=("Propio (sin restricciones)", ""), verified=True,
         notes="Señal de interfaz generada por código."),
    dict(id="tick", file="ui/tick.wav", category="ui", gain=0.5, loop=False, scenes=["últimos 3 s del temporizador"], title="tick (síntesis propia)", author="Proyecto YULU", url="tools/generate_sounds.py", lic=("Propio (sin restricciones)", ""), verified=True,
         notes="Señal de interfaz generada por código."),
]

PENDING = [
    ("Respiración grave de jaguar", "No se encontró grabación con licencia CC0/CC BY en Openverse ni Wikimedia Commons (búsquedas: 'big cat breathing purr', 'leopard growl')."),
    ("Pisadas de jaguar sobre hojas", "Sin grabación específica; se usa 'vegetacion' (hojas movidas) como aproximación."),
    ("Antorcha específica", "Las búsquedas de 'torch' devolvieron sopletes y encendedores; se usa fuego de leña ('maple fire')."),
    ("jaguar.wav de soundbytez (Freesound 97381)", "Descartado: la página del sonido está eliminada y la licencia no se pudo verificar."),
    ("Epic Drone Shots 001 (Sascha Ende, CC BY 4.0)", "Descartado por tono: la descripción lo define como enérgico y triunfal, inadecuado para el desenlace."),
    ("Música 'Ataque Jaguar' (BALAM, Jamendo)", "Descartado: la página de Jamendo no permitió verificar la licencia (contenido dinámico)."),
]


def main() -> int:
    manifest = {
        "_comment": "Manifiesto de audio de YULU. Ganancias 0-1 relativas al volumen de su categoría. Ver CREDITS.md.",
        "sounds": [],
    }
    lines = ["# Créditos de audio — YULU: La noche del jaguar", "",
             f"Recursos verificados y descargados el {DATE}. Todos los archivos de Freesound se obtuvieron a través de la API de Openverse "
             "(https://api.openverse.org/), que sirve la vista previa MP3 de alta calidad de cada sonido; los originales WAV exigen cuenta en Freesound y no se descargaron. "
             "Ningún archivo fue editado: el juego aplica ganancia, fundidos y paneo en tiempo de ejecución.", "",
             "| Id | Archivo | Título | Autor | Licencia | Fuente | Verificada en la página | Notas |", "|---|---|---|---|---|---|---|---|"]
    for e in ENTRIES:
        lic_name, lic_url = e["lic"]
        manifest["sounds"].append({
            "id": e["id"], "file": e["file"], "category": e["category"], "gain": e["gain"], "loop": e["loop"], "scenes": e["scenes"],
            "source": {"title": e["title"], "author": e["author"], "url": e["url"], "license": lic_name, "license_url": lic_url,
                        "attribution_required": lic_name.startswith("CC BY"), "license_verified_on_page": e["verified"],
                        "downloaded": DATE, "modifications": "ninguna"},
            "notes": e["notes"],
        })
        lic_cell = f"[{lic_name}]({lic_url})" if lic_url else lic_name
        lines.append(f"| {e['id']} | `{e['file']}` | {e['title']} | {e['author']} | {lic_cell} | {e['url']} | {'sí' if e['verified'] else 'no (metadatos de la API)'} | {e['notes']} |")
    lines += ["", "## Atribuciones requeridas (CC BY)", ""]
    for e in ENTRIES:
        if e["lic"][0].startswith("CC BY"):
            lines.append(f"- \"{e['title']}\" de {e['author']}, {e['lic'][0]} ({e['lic'][1]}). Fuente: {e['url']}. Sin modificaciones.")
    lines += ["", "## Recursos pendientes o descartados", ""]
    lines += [f"- **{name}**: {reason}" for name, reason in PENDING]
    lines += ["", "## Limitaciones declaradas", "",
              "- Los gruñidos y el rugido de ataque son de tigre (gran felino compatible); la única vocalización real de jaguar es la 'sierra' corta de Wikimedia Commons.",
              "- El coro de aves es de una selva australiana y el murmullo de aldea es un grupo hablando flamenco de forma ininteligible: aproximaciones ambientales, no registros de la región.",
              "- Los tambores son grabaciones de tambor de marco de estudio; no representan música pipil histórica.",
              "- Las señales de interfaz (ui_*) se generan por código y no son grabaciones.",
              "- La narración de voz la produce el sintetizador SAPI5 de Windows (voz 'Microsoft Sabina Desktop', es-MX); las frases en náhuat no tienen pronunciación nativa."]
    (AUDIO_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (AUDIO_DIR / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [e["file"] for e in ENTRIES if not (AUDIO_DIR / e["file"]).is_file()]
    print(f"{len(ENTRIES)} entradas escritas en manifest.json y CREDITS.md. Archivos ausentes: {missing or 'ninguno'}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
