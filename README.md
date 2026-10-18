# YULU: La noche del jaguar

Aventura narrativa educativa de supervivencia desarrollada en Python y Pygame para la
actividad académica de *AI for Developers* sobre vibecoding y prompt engineering.

El jugador despierta de noche en un bosque del territorio que hoy conocemos como
El Salvador, en una época prehispánica ficticia. Un jaguar lo sigue. A lo lejos hay una
aldea cuyos habitantes hablan náhuat. Para sobrevivir hasta el amanecer tendrá que
aprender expresiones, interpretar diálogos y tomar decisiones con consecuencias.

> Estado del proyecto: **FASE 5 en curso**. Capítulo 1 jugable de principio a fin con
> cinco escenas, 12 expresiones de náhuat con fuente citada, glosario, dos finales,
> fondos y personajes generados por IA, grabaciones ambientales con licencia, música de
> dron, narración expresiva con dos voces y volúmenes independientes. Pendiente: las
> pruebas manuales en equipo real ([`docs/PRUEBAS_MANUALES.md`](docs/PRUEBAS_MANUALES.md))
> y la bitácora académica ([`docs/PROMPTS_TEMPLATE.md`](docs/PROMPTS_TEMPLATE.md)).

## Requisitos

- Windows 10/11 (probado en Windows 11).
- Python 3.11 o superior (desarrollado con Python 3.15).
- Dependencias: `pygame-ce` y `pytest` (ver `requirements.txt`).

Se usa **pygame-ce** (fork mantenido de Pygame con la misma API `import pygame`) porque
el paquete `pygame` clásico no publica binarios para Python 3.15.

## Instalación

```powershell
cd C:\yulu
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

No se instala nada a nivel global ni se requiere conexión durante la partida.

## Ejecución

```powershell
.venv\Scripts\python main.py             # pantalla completa
.venv\Scripts\python main.py --windowed  # en ventana
```

## Controles

| Tecla / acción | Función |
|---|---|
| Enter, Espacio o clic | Mostrar el texto completo / continuar |
| Flechas ↑ ↓ o 1-9 | Seleccionar una decisión |
| Enter o clic | Confirmar la decisión |
| G | Abrir o cerrar el glosario de náhuat (detiene el temporizador) |
| ← → (en pausa) | Ajustar el volumen de música, ambiente, efectos o voces |
| Esc | Menú de pausa (continuar, volúmenes de música, ambiente y efectos, volver a empezar, salir) |
| F11 | Alternar pantalla completa / ventana |
| R (en un final) | Volver a jugar y explorar otras decisiones |

## Cómo se juega

- **Amenaza**: sube con decisiones ruidosas o lentas; baja al usar el río, los árboles o el fuego.
- **Confianza**: sube al entender y responder bien en náhuat; baja con silencios o malos modos.
- **Temporizador**: solo en tres momentos (la persecución, el aviso del jaguar y la alarma en el
  refugio). Nunca mientras se aprende una expresión nueva, y se detiene al abrir el glosario.
- **Errores**: una respuesta equivocada enseña la expresión correcta y permite seguir.
- **Finales**: al amanecer, confianza ≥ 40 y amenaza ≤ 84 llevan al final con la aldea;
  en otro caso, al final en soledad.

## Náhuat

Las 12 expresiones del capítulo tienen texto, traducción, contexto, fuente y estado de
validación en [`yulu/language/data/nahuat_ch1.json`](yulu/language/data/nahuat_ch1.json).
Las fuentes y los límites del material están en [`docs/NAHUAT_SOURCES.md`](docs/NAHUAT_SOURCES.md).
No existe en el proyecto ninguna voz nativa de náhuat.

## Recursos gráficos

Los escenarios actuales son **sustitutos procedurales provisionales** y el juego lo indica
en pantalla. El manifiesto [`yulu/assets/manifest.json`](yulu/assets/manifest.json) declara
las imágenes definitivas; al colocarlas en `yulu/assets/images/` se cargan automáticamente
con ajuste 16:9, deriva de cámara, niebla y humo. Los prompts para generarlas están en
[`docs/ART_PROMPTS.md`](docs/ART_PROMPTS.md). Comprueba qué falta con:

```powershell
.venv\Scripts\python tools\check_assets.py
```

## Audio

El administrador de audio ([`yulu/audio/audio_manager.py`](yulu/audio/audio_manager.py))
lee [`yulu/assets/audio/manifest.json`](yulu/assets/audio/manifest.json) y mezcla cuatro
categorías con volumen propio: música en bucle, ambiente por capas con fundidos, efectos
(con ligera variación de volumen y paneo) y voz. La música se atenúa mientras habla un
personaje. El paisaje sonoro ([`soundscape.py`](yulu/audio/soundscape.py)) elige las capas
por escena, hace crecer los tambores con la amenaza durante la persecución, amortigua el
exterior dentro del refugio y lanza vocalizaciones del jaguar a intervalos aleatorios.
Si falta cualquier archivo, la partida continúa y se registra una advertencia. Los
volúmenes se guardan en `settings.json`.

- **Grabaciones**: selva nocturna, lluvia, viento, murmullo de aldea, fuego, tambores,
  pasos, vocalizaciones de felinos y música de dron son grabaciones con licencia CC0 o
  CC BY obtenidas de Freesound (a través de la API de Openverse) y Wikimedia Commons.
  Autor, licencia, URL, fecha y limitaciones de cada una están en
  [`yulu/assets/audio/CREDITS.md`](yulu/assets/audio/CREDITS.md). Solo las cuatro señales
  de interfaz (`ui_*`) se generan por código.
- **Narración hablada: desactivada.** El juego se lee; los diálogos se muestran con subtítulos y
  sin voz. Las grabaciones del estudiante y las herramientas de voz se conservan, y para
  reactivarlas basta poner `VOICE_ENABLED = True` en `yulu/config.py` (vuelven la tecla V,
  el volumen de voces y la atenuación de la música al hablar).
- **Narración en español (Piper TTS, local, opcional)**: los diálogos se pregeneran con
  [Piper](https://github.com/OHF-Voice/piper1-gpl) (código GPL-3.0) y modelos oficiales de
  `rhasspy/piper-voices`. Piper necesita `onnxruntime`, que todavía no publica binarios para
  Python 3.15, así que se usa un **segundo entorno solo para generar voces** con el Python 3.14
  ya instalado en el equipo (el juego sigue en `.venv` y solo reproduce WAV):

  ```powershell
  # una vez: entorno de herramientas (ajusta la ruta si tu Python 3.14 está en otro sitio)
  py -V:Astral\CPython3.14.7 -m venv .venv-tts
  .venv-tts\Scripts\python -m pip install piper-tts onnxruntime

  # modelos (unos 300 MB, no se incluyen en Git) en yulussetsoices\piper  # descarga manual desde https://huggingface.co/rhasspy/piper-voices (archivo .onnx + .onnx.json + MODEL_CARD)
  # o con la utilidad de Piper:
  .venv-tts\Scripts\python -m piper.download_voices es_MX-claude-high es_MX-ald-medium es_AR-daniela-high es_ES-davefx-medium --data-dir yulussetsoices\piper

  # 1) tres frases de prueba para escuchar y evaluar
  .venv-tts\Scripts\python tools\generate_narration.py --sample
  # 2) todo el capítulo (solo lo que falta o cambió; --force para regenerar)
  .venv-tts\Scripts\python tools\generate_narration.py
  ```

  | Personaje | Modelo | Licencia del dataset (según MODEL_CARD) |
  |---|---|---|
  | Narradora | `es_MX-claude-high` | Apache-2.0 |
  | Anciana | `es_AR-daniela-high` | CC BY-SA 4.0 |
  | Guardia y niño | `es_MX-ald-medium` | Unlicense |
  | Protagonista | `es_ES-davefx-medium` | CC0 |

  - **Cambiar la voz de un personaje**: edita `yulu/assets/audio/voices.json` (modelo,
    `length_scale` para la velocidad, `sentence_silence` para las pausas) y vuelve a ejecutar
    el generador; solo se regeneran las líneas cuyo texto o configuración cambió.
  - **Escuchar las muestras**: `yulu/assets/audio/voice/samples/` (cualquier reproductor) o
    `tools/audio_preview.py`. Los WAV finales quedan en `yulu/assets/audio/voice/` con
    `index.json` (texto, locutor, modelo, estado) y `errors.log` si algo falló.
  - **Náhuat**: las frases en náhuat **no se sintetizan**. Solo suenan si existe una grabación
    hecha por una persona competente en la lengua en `yulu/assets/audio/voice/nahuat/<id>.wav`
    (el id es el de `nahuat_ch1.json`); mientras tanto el juego muestra el texto y el aviso
    "náhuat: sin grabación de hablante". `index.json` lista las pendientes.
  - **Respaldo**: `--engine winrt` usa las voces de Windows (Sabina y Raul) si Piper no está
    disponible.
  - **Errores comunes**: *"piper-tts no está instalado en este intérprete"*: estás usando
    `.venv` en lugar de `.venv-tts`. *"Modelo ... no encontrado"*: faltan el `.onnx` o el
    `.onnx.json` en `yulu/assets/voices/piper/`. *"No matching distribution found for
    onnxruntime"*: el intérprete es 3.15; crea `.venv-tts` con 3.14. Si falta un WAV, el juego
    muestra el subtítulo, registra una advertencia y continúa.
- **Grabar con tu propia voz** (narración y náhuat): `tools/record_voice.py` muestra cada
  línea, graba con el micrófono al pulsar ESPACIO, permite escuchar (P), aceptar (ENTER) o
  repetir (R), recorta silencios, normaliza y guarda el WAV con el nombre que espera el juego.
  Las tomas quedan marcadas como "grabación humana" en `voice/index.json` y Piper no las
  sobrescribe. Las frases en náhuat solo pueden grabarse así.

  ```powershell
  .venv\Scripts\python tools
ecord_voice.py --list            # micrófonos y plan
  .venv\Scripts\python tools
ecord_voice.py --nahuat-only     # primero las 7 frases en náhuat
  .venv\Scripts\python tools
ecord_voice.py                   # el resto (97 líneas en español)
  .venv\Scripts\python tools
ecord_voice.py --redo --scene s1_despertar   # regrabar una escena
  ```
- **Limpiar las grabaciones**: `tools/clean_voice.py` (entorno `.venv-tts`, usa numpy)
  reduce el ruido de fondo con una puerta espectral calibrada en los silencios de cada toma,
  filtra graves y agudos, iguala el nivel a -20 dBFS y remuestrea a 22 050 Hz. Los originales
  quedan en `voice/raw/` y el procesado siempre parte de ellos (`--strength` ajusta la
  intensidad; 1.6 por defecto).

  ```powershell
  .venv-tts\Scripts\python tools\clean_voice.py
  ```
- **Herramientas**: `tools/check_audio.py` valida archivos y metadatos de licencia;
  `tools/audio_preview.py --scene s2_persecucion --threat 70` permite escuchar la mezcla
  de una escena, y `--id jaguar_sierra` un sonido concreto.

## Personajes y referencias culturales

Cada escena declara su **reparto** (`cast` en `yulu/assets/manifest.json`): personajes de
cuerpo entero y jaguar de pie sobre la línea de suelo, con sombra, tono de luz del escenario,
el que habla iluminado y los demás atenuados; el jaguar escala con la amenaza y nunca es
translúcido. Los recortes se generan desde el paquete de personajes con
`tools/prepare_cutouts.py` (fondo negro eliminado por relleno desde los bordes, figura
principal conservada, hoja de control sobre damero). El jaguar de la persecución y la
reunión de la aldea son fondos completos. Criterios de vestuario, lo que se retiró y las
incertidumbres declaradas están en [`docs/REFERENCIAS_CULTURALES.md`](docs/REFERENCIAS_CULTURALES.md).

## Pruebas

```powershell
.venv\Scripts\python -m pytest -q
```

Prueba de humo sin pantalla (recorre la historia automáticamente durante N fotogramas):

```powershell
.venv\Scripts\python main.py --smoke-frames 5000
```

## Estructura

```
main.py                 Punto de entrada
yulu/app.py             Ciclo principal, fases de juego, glosario, pausa, cámara
yulu/config.py          Paleta, resolución lógica, umbrales y volúmenes por defecto
yulu/paths.py           Rutas de recursos independientes del directorio de ejecución
yulu/narrative/         Esquema de datos (schema.py) y escenas del capítulo (scenes.py)
yulu/state/             Estado de la partida (game_state.py) y motor narrativo (engine.py)
yulu/language/          Léxico de náhuat (lexicon.py) y datos con fuentes (data/)
yulu/ui/                Carga de imágenes, fondo, jaguar, diálogo, decisiones, glosario, HUD
yulu/audio/             Administrador de audio, paisaje sonoro y claves de narración
yulu/assets/            Manifiesto, imágenes, audio y fuentes locales
tools/                  Comprobación de recursos, corte de cuadrículas, síntesis de sonidos y narración
tests/                  Pruebas automatizadas con pytest
docs/                   Fuentes lingüísticas, prompts de arte, pruebas manuales, bitácora académica
```
