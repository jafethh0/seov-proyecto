"""
Selección y ordenamiento de carreras recomendadas (orquestación IMPERATIVA).

Pasos (sección 11 del diseño):
  1. áreas candidatas = áreas que sugieren las reglas ∪ las N de mayor afinidad;
  2. carreras candidatas = las de esas áreas;
  3. compatibilidad de cada una (objeto Career) y descarte de las que no tienen índice;
  4. orden por índice desc / nombre asc y límite de resultados.
Una habilidad baja nunca excluye una carrera: solo aparece como «por reforzar».
"""
from core import config
from core.domain.areas import AREA_WEIGHTS
from core.domain.career import Career
from core.functional import affinity


def rank_areas(profile):
    """Afinidad con cada área (usando sus pesos), de mayor a menor."""
    rows = []
    for name, weights in AREA_WEIGHTS.items():
        pseudo = Career(0, name, "", name, weights)
        index, _, _, _ = pseudo.compatibility(profile)
        if index is not None:
            rows.append({"name": name, "index": index})
    return affinity.rank(rows, key=lambda row: row["index"])


def recommend(profile, careers, rule_areas, suggested_types=(), fallback=None, limit=None):
    """
    rule_areas: dict {nombre de área: [ids de reglas que la sugieren]}.
    Devuelve una lista de dicts ordenada, lista para guardar y mostrar.
    """
    fallback = config.FALLBACK_TOP_AREAS if fallback is None else fallback
    limit = config.RESULT_LIMIT if limit is None else limit

    origin = {name: "RULE" for name in rule_areas}
    for row in rank_areas(profile)[:fallback]:
        origin.setdefault(row["name"], "AFFINITY")

    results = []
    for career in careers:
        if career.area not in origin:
            continue
        index, case, interest, skill = career.compatibility(profile)
        if index is None:
            continue
        results.append(
            {
                "career": career,
                "name": career.name,
                "compat": index,
                "case": case,
                "interest": None if interest is None else round(interest, 2),
                "skill": None if skill is None else round(skill, 2),
                "origin": origin[career.area],
                "rules": list(rule_areas.get(career.area, [])),
                "type_highlighted": career.program_type in suggested_types,
                "strengths": career.strengths(profile),
                "to_reinforce": career.to_reinforce(profile),
            }
        )
    ordered = affinity.rank(results, key=lambda row: row["compat"])
    return ordered[:limit]