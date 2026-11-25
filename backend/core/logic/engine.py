"""
Motor de inferencia propio (paradigma LÓGICO): encadenamiento hacia adelante.

No usa Prolog ni librerías externas. Parte de un conjunto de hechos y de una lista de
reglas; en cada pasada dispara las reglas cuyas condiciones (todas, combinadas con Y) ya
son hechos conocidos y agrega su conclusión. Repite hasta que una pasada no dispara nada.

Control de terminación:
  * cada regla se dispara a lo sumo una vez (conjunto de reglas ya disparadas);
  * las condiciones se evalúan contra una copia de los hechos al inicio de la pasada, por
    lo que las capas se resuelven en orden y el número de pasada queda en el rastro;
  * límite defensivo de pasadas (nº de reglas + 1).
El resultado conserva el rastro completo (qué regla, en qué pasada, con qué hechos), que
es la base de la explicación al estudiante.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Firing:
    rule_id: str
    iteration: int
    conditions: tuple
    conclusion: tuple
    new_fact: bool  # False si la conclusión ya se conocía por otra regla


@dataclass(frozen=True)
class Inference:
    facts: frozenset  # hechos iniciales + inferidos
    initial: frozenset
    trace: tuple  # Firing en el orden en que ocurrieron


def matches(rule, facts):
    """Una regla se cumple si TODAS sus condiciones están en los hechos."""
    return all(condition in facts for condition in rule.conditions)


def forward_chain(initial_facts, rules, max_iterations=None):
    active = sorted((r for r in rules if r.active), key=lambda r: (r.priority, r.id))
    limit = max_iterations if max_iterations is not None else len(active) + 1

    initial = frozenset(initial_facts)
    facts = set(initial)
    fired = set()
    trace = []

    for iteration in range(1, limit + 1):
        snapshot = frozenset(facts)
        fired_now = [r for r in active if r.id not in fired and matches(r, snapshot)]
        if not fired_now:
            break
        for rule in fired_now:
            fired.add(rule.id)
            is_new = rule.conclusion not in facts
            facts.add(rule.conclusion)
            trace.append(Firing(rule.id, iteration, rule.conditions, rule.conclusion, is_new))

    return Inference(frozenset(facts), initial, tuple(trace))