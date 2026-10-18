# Informe de la actividad: vibecoding y prompt engineering

**Proyecto:** YULU: La noche del jaguar. Mini-juego narrativo en Python para aprender náhuat.
**Estudiante:** Rafael Edgardo Arévalo · **Curso:** AI for Developers G3 · **Fecha:** 18 de octubre de 2026
**Repositorio:** https://github.com/dev-rafael-arevalo/yulu
**IA de apoyo:** Claude Code (Anthropic) dentro de VS Code; ChatGPT ImageGen para el arte.
**Lenguaje y librerías:** Python 3.15, pygame-ce 2.5, pytest.

---

## 1. Aplicación funcional

YULU es un juego de decisiones en el que el jugador despierta de noche en la selva, perseguido
por un jaguar, y debe llegar a una aldea cuyos habitantes hablan náhuat. El idioma es la
mecánica central: las respuestas correctas en náhuat suman confianza, los errores enseñan la
expresión y permiten reintentar, y al amanecer el estado acumulado decide uno de dos finales.

| Requisito | Cómo se cumple |
|---|---|
| Ejecuta sin errores críticos | 57 pruebas automatizadas en verde; recorrido automático de todo el capítulo sin excepciones (`main.py --smoke-frames 1500`); 25 pruebas manuales superadas en equipo real (`docs/PRUEBAS_MANUALES.md`) |
| Cumple el objetivo | Cinco escenas jugables, 12 expresiones de náhuat con fuente citada, glosario, dos finales, audio ambiental y arte integrado |
| Instalación reproducible | Clon limpio + `pip install -r requirements.txt` + `python main.py`, comprobado desde cero |

Instalación y ejecución (Windows):

```powershell
git clone https://github.com/dev-rafael-arevalo/yulu.git
cd yulu
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

## 2. Evidencia de vibecoding: prompts utilizados

Se usaron muchos más de tres prompts; se documentan los que marcaron el rumbo del proyecto.

### Prompt 1: encargo inicial por fases

**Qué se pidió.** Una especificación completa del juego (concepto, tecnología, dirección
artística, cinco escenas, estado, audio, náhuat, arquitectura y pruebas) con un método de
trabajo obligatorio en cinco fases y una regla explícita: inspeccionar el entorno y presentar
un plan antes de modificar archivos. Incluía además normas de honestidad: no inventar
traducciones ni fuentes, no afirmar que una prueba pasó si no se ejecutó.

**Qué se obtuvo.** La IA inspeccionó el entorno, detectó que Python 3.15 no tenía binarios de
`pygame` y propuso `pygame-ce`; entregó la estructura de carpetas, el plan y los criterios de
aceptación sin escribir código.

**Por qué se formuló así y qué aprendí.** Pedir "plan antes de código" evitó que el asistente
generara todo el proyecto de golpe, y las reglas de "no afirmes que una prueba pasó si no se
ejecutó" se cumplieron de forma visible en cada informe de fase. Iniciar siempre con un plan
por fases resulta efectivo para revisar y ajustar cada etapa sin esperar a que todo esté
terminado.

### Prompt 2: cambio radical de dirección artística

**Qué se pidió.** Los gráficos procedurales iniciales "parecían Paint". Pedí fotorrealismo
cinematográfico, un plan de sustitución, prompts por imagen si la IA no tenía herramienta de
generación, y conservar intacta la lógica narrativa.

**Qué se obtuvo.** La IA no tenía generador de imágenes, y lo dijo. Entregó un manifiesto de
recursos, un cargador con degradación controlada (si falta una imagen, el juego sigue con un
sustituto marcado como provisional) y un documento con un prompt por imagen. Yo generé el arte
con ChatGPT ImageGen y la IA construyó herramientas para cortarlo e integrarlo.

**Por qué se refinó.** La primera conversión del jaguar a transparencia lo dejó translúcido y
con un recuadro gris; hicieron falta varias iteraciones (umbrales de luminancia, relleno desde
los bordes, recorte de fragmentos vecinos) hasta que quedó sólido. Un paquete posterior con
fondos "a 1920×1080" resultó ser la misma cuadrícula reescalada, con una franja blanca en tres
archivos; la IA lo detectó midiendo la nitidez y lo descartó. La validación manual permite
identificar el rumbo del proyecto y ajustarlo si algo no se apega a lo necesario.

### Prompt 3: renovación profesional del audio

**Qué se pidió.** Sustituir los sonidos sintéticos por grabaciones reales con licencia
verificada, con reglas estrictas: solo fuentes legítimas, verificar cada licencia, registrar
autor y URL, no inventar atribuciones, documentar lo que no se consiguiera.

**Qué se obtuvo.** 21 grabaciones CC0 y CC BY de Freesound (a través de la API de Openverse) y
Wikimedia Commons, un manifiesto con metadatos de licencia por archivo, un `CREDITS.md`, una
herramienta de validación y otra de previsualización por escena, y una prueba automatizada
que impide usar material CC BY sin verificar en su página.

**Por qué se refinó.** Un sonido de jaguar se descartó porque su página había sido eliminada;
los rugidos de ataque son de tigre, como gran felino compatible, y así quedó documentado; los
archivos son las vistas previas MP3 porque los originales exigen cuenta. Tuve que refactorizar
los audios muchas veces porque las narraciones se escuchaban muy mal; para música y
ambientación es mejor utilizar sonidos naturales que no infrinjan derechos de autor.

### Prompt 4: voz propia para la narración

**Qué se pidió.** Después de probar voces de Windows y Piper TTS, decidí grabar yo toda la
narración y las frases en náhuat, y pedí a la IA que me guiara y grabara línea por línea.

**Qué se obtuvo.** Una herramienta de grabación guiada (muestra la línea, graba con el
micrófono, permite escuchar, aceptar o repetir, y guarda con el nombre que espera el juego) y
otra de limpieza de ruido. Grabé las 104 líneas.

**Por qué se descartó.** Incluso con una reducción de ruido de 42 dB, el resultado con un
micrófono de baja calidad no me convenció. Decidí dejar el juego en modo lectura, con un
interruptor en la configuración que conserva todo el trabajo de voz por si se retoma.

## 3. Iteración y mejora

| Mejora solicitada | Motivo | Resultado |
|---|---|---|
| Música menos estridente y ambientes más suaves | La mezcla sintética cansaba | Música de dron con licencia; volúmenes por defecto 35 % y 50 % |
| Jaguar solo donde hace falta y sólido | Aparecía en todas las escenas y translúcido | Reparto por escena; jaguar íntegro en la persecución y recortes sólidos en acecho y ataque |
| Personajes de la aldea en escena | Dar rostro a los interlocutores | Personajes de cuerpo entero con sombra, luz de escena y locutor destacado |
| Narración con más sentimiento y voz masculina | Voz plana y única | Prosodia por personaje y voz masculina; después Piper con cuatro modelos |
| Referencias culturales de vestuario | Un guardia llevaba un tocado con aspecto de casco europeo | Nuevo reparto coherente y `docs/REFERENCIAS_CULTURALES.md` con criterios e incertidumbres |
| Grabar la narración con voz propia | Las voces sintéticas no convencían | Herramientas de grabación y limpieza |
| Quitar la narración hablada | El resultado de voz no convenció | Juego en modo lectura; trabajo de voz conservado tras un interruptor |
| Limpieza para publicar | Archivos sin uso en el repositorio | Eliminación de recursos y herramientas obsoletas, README para GitHub, licencia MIT |

## 4. Validación del resultado

**Cómo se probó.**

- `pytest`: 57 pruebas sobre el motor narrativo (transiciones válidas, escenas inalcanzables,
  temporizadores, los dos finales, reinicio), el léxico (campos obligatorios, fuentes
  declaradas, nada provisional en producción), los recursos (archivos ausentes o dañados no
  interrumpen el juego) y el audio (volúmenes independientes, capas que no se acumulan al
  cambiar de escena, licencias CC BY verificadas).
- Recorrido automático sin pantalla (`--smoke-frames`) que atraviesa el capítulo completo.
- Capturas de pantalla renderizadas sin monitor en cada iteración para revisar el encuadre.
- 25 pruebas manuales en equipo real: pantalla completa, F11, ratón y teclado, glosario con el
  temporizador, volúmenes, mezcla por escena, ambos finales, reinicio. Todas superadas.
- Instalación desde un clon limpio en un entorno nuevo antes de publicar.

**Errores y limitaciones encontrados (selección).**

| Error o limitación | Cómo se detectó | Resolución |
|---|---|---|
| La viñeta acumulaba alfa y dejaba la pantalla casi negra | Captura | Reescrita con elipses que sobrescriben el alfa |
| Halos aditivos con alfa se veían como manchas sólidas | Captura | `BLEND_ADD` ignora el alfa; se oscurece el color en su lugar |
| Dos fuentes de verdad para la escena actual | Revisión de código | La presentación deriva siempre del estado |
| Picos de volumen en palabras sueltas en náhuat | Al escuchar | Eliminadas las etiquetas de volumen y énfasis del SSML |
| La herramienta de grabación se congelaba al detener una toma | Al grabar | El micrófono se abre una sola vez por sesión |
| Rosetas del jaguar convertidas en agujeros al quitar el fondo negro | Hoja de control | Relleno desde los bordes en lugar de clave por color |
| No existe voz nativa de náhuat ni voz TTS centroamericana | Inventario de voces y catálogo de Piper | Declarado en la documentación; el juego no incluye voz |
| Fondos de la cuadrícula a baja resolución | Medición de nitidez | Sustituidos después por imágenes íntegras |

## 5. Reflexión final

**Qué aprendí usando IA para programar.** La parte que habría sido más lenta o imposible sin IA
fue la generación de imágenes: habría tenido que diseñarlas a mano o recurrir a bancos
digitales. También aprendí que la IA rinde mucho mejor con un plan por fases: revisar y
ajustar cada etapa sin esperar a que todo esté terminado reduce el riesgo de acumular errores.

**Ventajas y límites del vibecoding.** La ventaja es la velocidad y la amplitud: en un día se
construyó un motor narrativo probado, un sistema de audio por capas, herramientas propias de
corte de imágenes y grabación, y documentación completa. Los límites aparecieron en dos
frentes. Primero, la verificación: revisar por completo el código fuente es un desafío porque
no estoy familiarizado con pygame, aunque la estructura se entiende. Segundo, las fuentes: el
náhuat salvadoreño tiene pocas referencias accesibles, y hoy no es posible comprobar la
pronunciación sin interactuar con las comunidades que lo hablan. Aun así se encontró
documentación publicada (King 2011, Campbell 1985, Hernández 2016) que sirve de base para un
primer conjunto de expresiones, y el juego declara en cada entrada su fuente y su estado de
validación en lugar de presentar contenido generado como auténtico.

**Qué partes del código comprendo y cuáles necesito reforzar.** Comprendo el flujo general:
el estado de la partida separado de la presentación, el motor que valida el grafo de escenas
y aplica decisiones, el léxico cargado desde JSON y la organización del audio por capas. Las
pruebas automatizadas me ayudaron a entender qué debía cumplir cada módulo. Necesito reforzar
el detalle de pygame (superficies, mezcla de alfa, canales del mezclador) y el procesamiento de
imagen y sonido de las herramientas, donde dependí más de la IA.

**Qué haría distinto.** Planificar con más tiempo. Con poco tiempo el riesgo crece, porque se
depende más de la IA como fuente de verdad y no se tienen fuentes suficientes para comprobar.

## Anexos

- Capturas del juego: `docs/capturas/` (seis imágenes) y en el README del repositorio.
- Bitácora completa de prompts y errores: `docs/PROMPTS_TEMPLATE.md`.
- Pruebas manuales con resultados: `docs/PRUEBAS_MANUALES.md`.
- Fuentes lingüísticas: `docs/NAHUAT_SOURCES.md`. Créditos de audio: `yulu/assets/audio/CREDITS.md`.
- Salidas de verificación del clon limpio (18/10/2026):

```
pytest -q                 -> 57 passed
tools/check_assets.py     -> 45/45 referencias presentes
tools/check_audio.py      -> 25 sonidos, 0 problemas
main.py --smoke-frames 1500 -> sin errores
```
