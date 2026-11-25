"""
Cálculo de afinidad y compatibilidad (paradigma FUNCIONAL).

Funciones puras con reduce/map/filter/lambda. No modifican sus argumentos.

    I = Σ w·score / Σ w   (dimensiones de interés con puntuación válida)
    H = Σ w·score / Σ w   (dimensiones de habilidad con puntuación válida)
    compat = 0.6·I + 0.4·H, con cuatro casos según qué secciones tengan datos:
        A: hay I y H      -> 0.6·I + 0.4·H
        B: solo hay I     -> I
        C: solo hay H     -> H
        D: ninguna        -> None (nunca 0: no hay información para comparar)
"""
from functools import reduce

from core import config


def kind_of(code):
    return "INTEREST" if code.startswith("INT-") else "SKILL"


def weighted_average(pairs):
    """pairs: lista de (peso, puntuación). None si el peso total es 0."""
    total_weight = reduce(lambda acc, pair: acc + pair[0], pairs, 0)
    if total_weight == 0:
        return None
    return reduce(lambda acc, pair: acc + pair[0] * pair[1], pairs, 0) / total_weight


def section_affinity(weights, scores, kind):
    """Afinidad de una sección: solo cuentan las dimensiones del tipo con puntuación válida."""
    pairs = list(
        map(
            lambda item: (item[1], scores[item[0]]),
            filter(lambda item: kind_of(item[0]) == kind and item[0] in scores, weights.items()),
        )
    )
    return weighted_average(pairs)


def compat_index(interest, skill):
    """Devuelve (índice o None, caso 'A'|'B'|'C'|'D')."""
    if interest is not None and skill is not None:
        value = config.WEIGHT_INTERESTS * interest + config.WEIGHT_SKILLS * skill
        return round(value, 2), "A"
    if interest is not None:
        return round(interest, 2), "B"
    if skill is not None:
        return round(skill, 2), "C"
    return None, "D"


def affinity_level(value):
    if value is None:
        return None
    if value >= config.AFFINITY_HIGH:
        return "HIGH"
    if value >= config.AFFINITY_MEDIUM:
        return "MEDIUM"
    return "EXPLORATORY"


def rank(items, key):
    """Orden por índice descendente y nombre ascendente (desempate estable)."""
    return sorted(items, key=lambda item: (-key(item), item["name"]))