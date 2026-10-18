# YULU: La noche del jaguar

Aventura narrativa educativa de supervivencia desarrollada en Python y Pygame para la
actividad académica de *AI for Developers* sobre vibecoding y prompt engineering.

El jugador despierta de noche en un bosque del territorio que hoy conocemos como
El Salvador, en una época prehispánica ficticia. Un jaguar lo sigue. A lo lejos hay una
aldea cuyos habitantes hablan náhuat. Para sobrevivir hasta el amanecer tendrá que
aprender expresiones, interpretar diálogos y tomar decisiones con consecuencias.

> Estado del proyecto: **FASE 2 completada** (escenas 1 y 2 jugables). Las escenas 3 a 5,
> el náhuat, el glosario, el audio y la documentación académica llegan en las fases 3 a 5.

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
| Esc | Menú de pausa (continuar, volver a empezar, salir) |
| F11 | Alternar pantalla completa / ventana |
| R (en un final) | Volver a jugar |

## Pruebas

```powershell
.venv\Scripts\python -m pytest -q
```

Prueba de humo sin pantalla (recorre la historia automáticamente durante N fotogramas):

```powershell
.venv\Scripts\python main.py --smoke-frames 1500
```

## Estructura

```
main.py                 Punto de entrada
yulu/app.py             Ciclo principal, fases de juego, pausa, pantalla completa
yulu/config.py          Paleta, resolución lógica, umbrales y volúmenes por defecto
yulu/paths.py           Rutas de recursos independientes del directorio de ejecución
yulu/narrative/         Esquema de datos (schema.py) y escenas del capítulo (scenes.py)
yulu/state/             Estado de la partida (game_state.py) y motor narrativo (engine.py)
yulu/ui/                Fondo procedural, jaguar, diálogo, decisiones, HUD, transiciones, pausa
yulu/language/          Datos lingüísticos de náhuat (FASE 3)
yulu/audio/             Administrador de audio (FASE 4)
yulu/assets/            Imágenes, audio y fuentes locales
tests/                  Pruebas automatizadas con pytest
docs/                   Documentación académica (FASE 5)
```

## Recursos gráficos

Los escenarios actuales son **sustitutos provisionales generados por código**
(gradientes, siluetas, niebla y antorchas). No representan reconstrucciones arqueológicas.
