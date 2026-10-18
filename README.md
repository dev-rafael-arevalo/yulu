# YULU: La noche del jaguar

Aventura narrativa educativa de supervivencia desarrollada en Python y Pygame para la
actividad académica de *AI for Developers* sobre vibecoding y prompt engineering.

El jugador despierta de noche en un bosque del territorio que hoy conocemos como
El Salvador, en una época prehispánica ficticia. Un jaguar lo sigue. A lo lejos hay una
aldea cuyos habitantes hablan náhuat. Para sobrevivir hasta el amanecer tendrá que
aprender expresiones, interpretar diálogos y tomar decisiones con consecuencias.

> Estado del proyecto: **FASE 4 completada**. Capítulo 1 jugable de principio a fin con
> cinco escenas, 12 expresiones de náhuat con fuente citada, glosario, dos finales,
> fondos generados por IA, ambiente sonoro por capas, efectos, música, narración en
> español pregenerada y volúmenes independientes. Pendiente: pruebas finales y
> documentación académica (FASE 5).

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
| V | Repetir la narración de la línea actual |
| ← → (en pausa) | Ajustar el volumen de música, ambiente, efectos o voces |
| Esc | Menú de pausa (continuar, volúmenes, volver a empezar, salir) |
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
mezcla cuatro categorías con volumen propio: música en bucle, ambiente por capas con
fundidos, efectos y voz. El paisaje sonoro ([`soundscape.py`](yulu/audio/soundscape.py))
elige las capas según la escena y añade una capa de tensión y rugidos espaciados al azar
según la amenaza. Si falta cualquier archivo, la partida continúa y se registra una advertencia.
Los volúmenes se guardan en `settings.json`.

- **Efectos, ambientes y música** son **sintéticos provisionales** generados localmente:
  `python tools/generate_sounds.py`. Pueden sustituirse por grabaciones con licencia
  compatible conservando el nombre del archivo en `yulu/assets/audio/`.
- **Narración en español**: se pregenera sin conexión con la voz SAPI5 de Windows
  (`Microsoft Sabina Desktop`, es-MX):

  ```powershell
  .venv\Scripts\python tools\generate_narration.py
  ```

  Crea unos 106 WAV (35 MB) en `yulu/assets/audio/voice/`, que no se incluyen en Git.
  Las frases en náhuat se leen con fonética española aproximada: **no es una voz nativa**.

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
docs/                   Fuentes lingüísticas, prompts de arte, plantilla académica (FASE 5)
```
