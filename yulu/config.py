"""Constantes de configuración: resolución lógica, paleta y valores por defecto."""
from __future__ import annotations

TITLE = "YULU: La noche del jaguar"
LOGICAL_WIDTH = 1280
LOGICAL_HEIGHT = 720
FPS = 60

# Paleta: azul noche, verde profundo, ámbar y fuego.
NIGHT_TOP = (6, 10, 30)
NIGHT_BOTTOM = (10, 28, 48)
DEEP_GREEN = (10, 38, 30)
FOREST_DARK = (4, 18, 16)
FOG = (120, 150, 170)
AMBER = (232, 170, 60)
FIRE = (240, 110, 30)
EMBER = (180, 60, 20)
MOON = (220, 228, 240)
TEXT = (236, 230, 214)
TEXT_DIM = (160, 158, 150)
PANEL = (6, 10, 22)
JAGUAR_EYE = (255, 196, 70)
DANGER = (200, 60, 40)

# Rango de los indicadores de estado.
METER_MIN = 0
METER_MAX = 100
THREAT_START = 15
TRUST_START = 0
# Umbral a partir del cual la presentación y el audio pasan a modo de peligro.
THREAT_HIGH = 70

# Volúmenes por defecto (0.0 a 1.0), independientes por categoría.
DEFAULT_VOLUMES = {"music": 0.5, "ambient": 0.7, "sfx": 0.8, "voice": 1.0}

# Velocidad del texto en caracteres por segundo.
TYPEWRITER_CPS = 45
