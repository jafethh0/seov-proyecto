"""
Hechos del motor lógico (paradigma LÓGICO).

Un hecho es una tupla inmutable: (predicado, argumento) o (predicado,) si no lleva
argumento. Ejemplos:  ("habilidad_alta", "HAB-LOG")   ("perfil_analitico",)
"""
from core import config
from core.functional import levels

LEVEL_WORD = {levels.HIGH: "alto", levels.MEDIUM: "medio", levels.LOW: "bajo"}
KIND_PREFIX = {"INTEREST": ("interes", "alto"), "SKILL": ("habilidad", "alta")}


def interest_high(code):
    return ("interes_alto", code)


def skill_high(code):
    return ("habilidad_alta", code)


def profile(name):
    return ("perfil_" + name,)


def area(name):
    return ("area", name)


def program_type(kind):
    return ("sugerir_tipo", kind)


def predicate_for(kind, level):
    """Predicado de nivel: interes_alto / interes_medio / interes_bajo, habilidad_alta..."""
    noun, _ = KIND_PREFIX[kind]
    word = LEVEL_WORD[level]
    if kind == "SKILL":  # concordancia: habilidad alta / media / baja
        word = {"alto": "alta", "medio": "media", "bajo": "baja"}[word]
    return f"{noun}_{word}"


def facts_from_scores(scores, dominant_count=2, dominant_minimum=50):
    """
    scores: lista de dicts {"code", "kind", "score", "valid", "level"}.
    Solo las dimensiones válidas generan hechos. Los intereses dominantes (los de mayor
    puntaje, con al menos `dominant_minimum`) sirven solo para redactar explicaciones.
    """
    facts = set()
    for item in scores:
        if item["valid"] and item["level"] is not None:
            facts.add((predicate_for(item["kind"], item["level"]), item["code"]))
    interests = levels.of_kind(scores, "INTEREST")
    for item in levels.strongest(interests, dominant_count, dominant_minimum):
        facts.add(("interes_dominante", item["code"]))
    return frozenset(facts)


def format_fact(fact):
    """('habilidad_alta', 'HAB-LOG') -> 'habilidad_alta(HAB-LOG)'."""
    if len(fact) == 1:
        return fact[0]
    return f"{fact[0]}({fact[1]})"