"""Explicación del razonamiento: convierte el rastro del motor en un resumen legible."""
from .engine import Inference
from .facts import format_fact
from .rules import RULES

RULES_BY_ID = {rule.id: rule for rule in RULES}


def conclusions(inference: Inference, predicate):
    """Argumentos de los hechos inferidos con ese predicado, sin repetir y en orden."""
    seen = []
    for firing in inference.trace:
        fact = firing.conclusion
        if fact[0] == predicate:
            value = fact[1] if len(fact) > 1 else fact[0]
            if value not in seen:
                seen.append(value)
    return seen


def rules_supporting(inference: Inference, fact):
    """Identificadores de todas las reglas disparadas que concluyen ese hecho."""
    return [f.rule_id for f in inference.trace if f.conclusion == fact]


def summarize(inference: Inference, rules_by_id=None):
    rules_by_id = rules_by_id or RULES_BY_ID
    profiles = [f.conclusion[0].removeprefix("perfil_") for f in inference.trace
                if f.conclusion[0].startswith("perfil_")]
    areas = [
        {"name": name, "rules": rules_supporting(inference, ("area", name))}
        for name in conclusions(inference, "area")
    ]
    return {
        "profiles": profiles,
        "areas": areas,
        "program_types": conclusions(inference, "sugerir_tipo"),
        "steps": [
            {
                "rule": f.rule_id,
                "layer": rules_by_id[f.rule_id].layer,
                "iteration": f.iteration,
                "if": [format_fact(c) for c in f.conditions],
                "then": format_fact(f.conclusion),
                "text": rules_by_id[f.rule_id].explanation,
            }
            for f in inference.trace
        ],
    }