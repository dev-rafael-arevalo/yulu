# Bitácora de vibecoding y prompt engineering — YULU: La noche del jaguar

Plantilla para la actividad de *AI for Developers*. Las secciones marcadas con ✎ deben
completarse con la experiencia propia del estudiante. Lo que aparece sin esa marca es un
registro de lo ocurrido en la sesión de desarrollo del 18 de octubre de 2026 con
Claude Code, incluido como ejemplo verificable; puede editarse o sustituirse.

Estudiante: ✎ Rafael Edgardo Arévalo   Curso: ✎ AI for Developers G3   Fecha de entrega: ✎ 18/10/2026

## 1. Prompts documentados

Documenta al menos tres prompts. Para cada uno: el texto (o un resumen fiel), qué se
esperaba, qué se obtuvo, qué hubo que corregir y qué aprendiste sobre cómo formular la
petición.

### Prompt 1 — Encargo inicial por fases

- **Texto (resumen):** especificación completa del juego (concepto, tecnología, dirección
  artística, cinco escenas, estado, audio, náhuat, arquitectura, pruebas) con un método de
  trabajo obligatorio en cinco fases y la instrucción de inspeccionar el entorno y presentar
  un plan antes de tocar archivos.
- **Qué se esperaba:** un plan técnico y criterios de aceptación, sin código.
- **Qué se obtuvo:** inspección del entorno (Python 3.15 sin binarios de `pygame`, por lo que
  se eligió `pygame-ce`), estructura de carpetas, plan por fases y criterios de aceptación.
- **Correcciones:** ninguna en esta fase; la decisión abierta (fuentes de náhuat) se delegó
  explícitamente al asistente.
- **Aprendizaje sobre el prompt:** ✎ pedir "plan antes de código" evitó que el
  asistente generara todo el proyecto de golpe; las reglas "no afirmes que una prueba pasó
  si no se ejecutó" se cumplieron de forma visible en los informes.

### Prompt 2 — Cambio radical de dirección artística

- **Texto (resumen):** los gráficos procedurales "parecen Paint"; se pidió fotorrealismo
  cinematográfico, un plan de sustitución, prompts por imagen si no había herramienta de
  generación, y conservar la lógica existente.
- **Qué se esperaba:** fondos realistas integrados.
- **Qué se obtuvo:** el asistente no tenía herramienta de generación de imágenes; entregó un
  manifiesto de recursos, un cargador con degradación controlada y un documento de prompts.
  El estudiante generó una cuadrícula con ChatGPT ImageGen y el asistente la cortó con una
  herramienta propia.
- **Correcciones:** la primera conversión del jaguar a transparencia lo dejó translúcido y con
  un recuadro gris; se corrigió en dos iteraciones ajustando umbrales de luminancia. Un zip
  posterior con fondos a 1920×1080 resultó ser la misma cuadrícula reescalada, con una franja
  blanca en tres archivos, y se descartó tras medir la nitidez.
- **Aprendizaje sobre el prompt:** ✎ La validación manual permite identificar el rumbo del proyecto, y ajustarlo si algo no se apega a lo necesario.

### Prompt 3 — Renovación profesional del audio

- **Texto (resumen):** sustituir sonidos sintéticos por grabaciones con licencia verificada,
  reglas estrictas de licencias y atribución, diseño sonoro por escena, manifiesto, créditos
  e informe final.
- **Qué se esperaba:** ambientación realista y documentada.
- **Qué se obtuvo:** 21 grabaciones CC0/CC BY de Freesound (vía API de Openverse) y Wikimedia
  Commons, manifiesto con metadatos de licencia, `CREDITS.md`, herramientas de validación y
  previsualización, y una prueba automatizada que impide usar material CC BY sin verificar.
- **Correcciones y límites:** un sonido de jaguar se descartó porque su página estaba
  eliminada; se usan gruñidos de tigre como felino compatible; las vistas previas MP3 son de
  128 kb/s porque los originales exigen cuenta.
- **Aprendizaje sobre el prompt:** ✎

### Prompt 4 (opcional) — ✎

## 2. Mejoras solicitadas tras ver el resultado

| Fecha | Mejora pedida | Motivo | Resultado |
|---|---|---|---|
| 2026-10-18 | Música menos estridente, ambientes más suaves | La mezcla sintética cansaba | Música de dron con licencia, volúmenes por defecto 35 % / 50 % |
| 2026-10-18 | Jaguar solo donde haga falta y sólido | Aparecía en todas las escenas y translúcido | Visible en 7 nodos; alfa sólido; umbral de recorte corregido |
| 2026-10-18 | Personajes de la aldea | Dar rostro a los interlocutores | Retratos al hablar y grupos en escenas concretas |
| 2026-10-18 | Narración con más sentimiento y voz masculina | Voz plana y única | SSML por personaje y voz Raul (WinRT) para los hombres |
| 2026-10-18 | Voces Piper locales y referencias culturales de vestuario | Voces de Windows sonaban robóticas; vestuario con elementos ajenos (casco) | Piper en entorno 3.14, voces por personaje; retratos íntegros de anciana y guardia, jaguar y aldea como fondos; `docs/REFERENCIAS_CULTURALES.md` |
| 2026-10-18 | Grabar toda la narración y el náhuat con voz propia | Las voces sintéticas no convencían | `tools/record_voice.py` (grabación guiada) y `tools/clean_voice.py` (reducción de ruido de 15 dB de media) |
| ✎ | | | |

## 3. Errores y limitaciones observados

Registra solo lo que realmente ocurrió, con la evidencia (captura, salida de consola, prueba).

| Fecha | Error o limitación | Evidencia | Cómo se resolvió o por qué sigue abierto |
|---|---|---|---|
| 2026-10-18 | La viñeta acumulaba alfa y dejaba la pantalla casi negra | Captura sin monitor | Reescrita con elipses que sobrescriben el alfa |
| 2026-10-18 | Halos aditivos con alfa se veían como manchas sólidas | Captura | `BLEND_ADD` ignora el alfa; se oscurece el color en su lugar |
| 2026-10-18 | La fuente serif no tenía flechas ni triángulos | Cuadros en pantalla | Sustituidos por texto |
| 2026-10-18 | Dos fuentes de verdad para la escena actual | Revisión de código | La presentación deriva siempre del estado |
| 2026-10-18 | Picos de volumen en palabras sueltas en náhuat | Reporte del estudiante al escuchar | Eliminados `volume` y `emphasis` del SSML |
| 2026-10-18 | No existe voz nativa de náhuat | Inventario de voces del sistema | Declarado en README y glosario; voz española con fonética aproximada |
| 2026-10-18 | Fondos a 555×252 reescalados | Medición de nitidez | Abierto: generar cada fondo por separado a 1920×1080 |
| 2026-10-18 | La escucha previa sonaba acelerada; la herramienta se congelaba al detener una toma | Reporte del estudiante | Formato mono/estéreo del mezclador; el micrófono se abre una sola vez por sesión |
| 2026-10-18 | Micrófono con ruido de fondo | Reporte del estudiante y medición del suelo de ruido | Puerta espectral; originales conservados en voice/raw |
| ✎ | | | |

## 4. Reflexión final del estudiante ✎

Responde en 300 a 600 palabras. Preguntas guía:

- ¿Qué parte del proyecto habría sido más lenta o imposible sin asistencia de IA, y cuál
  habría salido mejor haciéndola a mano?
- ¿Qué instrucciones del prompt inicial resultaron decisivas (fases, "no inventes",
  "informa qué pruebas ejecutaste") y cuáles sobraban?
- ¿Cómo verificaste lo que el asistente afirmaba (pruebas, capturas, licencias, fuentes
  lingüísticas)? ¿Hubo algo que aceptaste sin comprobar?
- ¿Qué aprendiste sobre el náhuat y sobre el riesgo de presentar contenido generado como
  auténtico?
- ¿Qué harías distinto en el siguiente proyecto con IA?

✎

## 5. Anexos

- Capturas: ✎ (ruta o enlace)
- Salida de `pytest -q`: ✎ (pegar)
- Salida de `tools/check_audio.py` y `tools/check_assets.py`: ✎ (pegar)
- Resultado de `docs/PRUEBAS_MANUALES.md`: ✎
