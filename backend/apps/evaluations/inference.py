"""
Puente entre el resultado de puntuación y el motor lógico (core/logic).

Convierte las puntuaciones guardadas en hechos, ejecuta el encadenamiento hacia adelante
con las reglas vigentes y guarda el razonamiento junto con la versión del conjunto de reglas.
"""
from core.logic import explain
from core.logic.engine import forward_chain
from core.logic.facts import facts_from_scores, format_fact
from core.logic.rules import RULES, RULESET_VERSION

from .models import ResultInference


def scores_as_dicts(result):
    return [
        {
            "code": s.dimension.code,
            "kind": s.dimension.kind,
            "score": None if s.score is None else float(s.score),
            "valid": s.is_valid,
            "level": s.level,
        }
        for s in result.scores.select_related("dimension")
    ]


def store_inference(result):
    initial = facts_from_scores(scores_as_dicts(result))
    outcome = forward_chain(initial, RULES)
    return ResultInference.objects.create(
        result=result,
        rules_version=RULESET_VERSION,
        facts=sorted(format_fact(f) for f in initial),
        summary=explain.summarize(outcome),
    )


def serialize(result):
    stored = getattr(result, "inference", None)
    if stored is None:
        return None
    return {"rules_version": stored.rules_version, **stored.summary}