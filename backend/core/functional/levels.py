"""
Niveles de las dimensiones (paradigma FUNCIONAL).

Funciones puras: no modifican sus argumentos ni dependen de estado externo; devuelven
datos nuevos. Se usan map, filter, reduce y lambda para transformar los resultados del
procesador de puntuaciones.
"""
from functools import reduce

from core import config

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


def level_for(score, high=config.LEVEL_HIGH, low=config.LEVEL_LOW):
    """Nivel de una puntuación de 0 a 100; None si la dimensión no tiene puntuación."""
    if score is None:
        return None
    if score >= high:
        return HIGH
    if score >= low:
        return MEDIUM
    return LOW


def with_levels(results, high=config.LEVEL_HIGH, low=config.LEVEL_LOW):
    """Devuelve copias de los resultados con el campo 'level' agregado (map + lambda)."""
    return list(map(lambda r: {**r, "level": level_for(r["score"], high, low)}, results))


def valid_only(results):
    """Solo las dimensiones válidas (filter + lambda)."""
    return list(filter(lambda r: r["valid"], results))


def of_kind(results, kind):
    """Solo las dimensiones de un tipo (INTEREST o SKILL)."""
    return list(filter(lambda r: r["kind"] == kind, results))


def strongest(results, count=2, minimum=0):
    """Las `count` dimensiones válidas de mayor puntuación (mínimo `minimum`)."""
    candidates = filter(lambda r: r["valid"] and r["score"] >= minimum, results)
    ranked = sorted(candidates, key=lambda r: (-r["score"], r["code"]))  # desempate estable
    return ranked[:count]


def average_score(results):
    """Promedio de las puntuaciones válidas (reduce); None si no hay ninguna."""
    scores = [r["score"] for r in results if r["valid"]]
    if not scores:
        return None
    return round(reduce(lambda total, score: total + score, scores, 0) / len(scores), 2)