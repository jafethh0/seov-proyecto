"""
Configuración centralizada y versionada del SEOV (sin números mágicos en el código).

Estos valores son INICIALES y experimentales: deben revisarse con la prueba piloto.
Cada cambio que afecte al cálculo debe publicarse con una nueva SCORING_VERSION, y cada
resultado guarda la versión con la que se calculó.
"""
from fractions import Fraction

SCORING_VERSION = "1.0"

# Niveles por dimensión (puntuación de 0 a 100).
LEVEL_HIGH = 70  # score >= 70  -> ALTO
LEVEL_LOW = 40   # score <  40  -> BAJO; entre ambos, MEDIO

# Validez de una dimensión: proporción mínima de sus preguntas que deben estar respondidas.
MIN_ANSWERED_RATIO = Fraction(2, 3)

# Para enviar una evaluación: dimensiones válidas mínimas por sección (de 7 en cada una).
MIN_VALID_INTEREST_DIMS = 5
MIN_VALID_SKILL_DIMS = 5

# Compatibilidad con carreras (se usa en el módulo de recomendaciones).
WEIGHT_INTERESTS = 0.6
WEIGHT_SKILLS = 0.4
AFFINITY_HIGH = 70    # alta >= 70
AFFINITY_MEDIUM = 50  # media 50-69.99; exploratoria < 50
FALLBACK_TOP_AREAS = 3
RESULT_LIMIT = 10