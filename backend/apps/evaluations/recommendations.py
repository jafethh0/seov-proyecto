"""
Puente entre el resultado y el recomendador (core/imperative/recommender.py).

Al enviar la evaluación se guardan las recomendaciones ordenadas (independientes del
departamento). Al leerlas se agregan las ofertas verificadas del departamento elegido.
"""
from decimal import Decimal

from django.db.models import Max

from apps.analytics import sqlqueries
from apps.catalog.models import CareerProgram
from apps.questionnaires.models import Dimension
from core.domain.career import Career, StudentProfile
from core.functional import affinity
from core.imperative.recommender import recommend
from core.logic.explain import RULES_BY_ID

from . import inference
from .models import CareerRecommendation

NOTICE = (
    "El índice de compatibilidad no es una probabilidad de éxito académico o profesional: "
    "mide qué tan cerca están tus respuestas del perfil de cada carrera. Sirve para explorar "
    "opciones, no para decidir por ti."
)


def catalog_version():
    stats = CareerProgram.objects.filter(is_active=True).aggregate(
        last=Max("updated_at")
    )
    count = CareerProgram.objects.filter(is_active=True).count()
    last = stats["last"].isoformat() if stats["last"] else "none"
    return f"{count}@{last}"


def load_careers():
    programs = (
        CareerProgram.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("dimension_weights__dimension")
    )
    return [
        Career(
            id=program.id,
            name=program.name,
            program_type=program.program_type,
            area=program.category.name,
            weights={
                w.dimension.code: w.weight
                for w in program.dimension_weights.all()
                if w.dimension.is_active
            },
        )
        for program in programs
    ]


def _dec(value):
    return None if value is None else Decimal(str(value))


def store_recommendations(result):
    profile = StudentProfile.from_scores(inference.scores_as_dicts(result))
    summary = result.inference.summary
    rule_areas = {a["name"]: a["rules"] for a in summary["areas"]}
    ranked = recommend(profile, load_careers(), rule_areas, summary["program_types"])
    CareerRecommendation.objects.bulk_create(
        [
            CareerRecommendation(
                result=result,
                program_id=item["career"].id,
                rank=position,
                compat=_dec(item["compat"]),
                interest_affinity=_dec(item["interest"]),
                skill_affinity=_dec(item["skill"]),
                origin=item["origin"],
                rule_ids=item["rules"],
                details={
                    "level": affinity.affinity_level(item["compat"]),
                    "case": item["case"],
                    "type_highlighted": item["type_highlighted"],
                    "strengths": item["strengths"],
                    "to_reinforce": item["to_reinforce"],
                },
            )
            for position, item in enumerate(ranked, start=1)
        ]
    )


def _offering_row(row):
    """Fila de la vista SQL v_available_offerings -> oferta para la API."""
    return {
        "id": row["offering_id"],
        "official_name": row["official_name"],
        "institution": row["institution"],
        "acronym": row["acronym"],
        "sector": row["sector"],
        "campus": row["campus"],
        "department": row["department"],
        "city": row["city"],
        "modality": row["modality"],
        "duration_months": row["duration_months"],
        "admission_requirements": row["admission_requirements"],
        "source_url": row["source_url"],
        "verified_at": row["verified_at"],
    }


def _available_offerings(department, include_online):
    """Ofertas disponibles, consultadas con SQL declarativo (vista v_available_offerings)."""
    if department is None:
        return sqlqueries.fetch_all("offerings_all")
    name = "offerings_in_department_or_online" if include_online else "offerings_in_department"
    return sqlqueries.fetch_all(name, {"department_id": department.id})


def serialize_recommendations(result, department=None, include_online=True):
    rows = list(result.recommendations.select_related("program__category"))
    wanted = {r.program_id for r in rows}
    by_program = {}
    for row in _available_offerings(department, include_online):
        if row["program_id"] in wanted:
            by_program.setdefault(row["program_id"], []).append(_offering_row(row))

    names = dict(Dimension.objects.values_list("code", "name"))

    def item(row):
        details = row.details
        return {
            "rank": row.rank,
            "program": {
                "id": row.program_id,
                "name": row.program.name,
                "program_type": row.program.program_type,
                "category": row.program.category.name,
                "description": row.program.description,
                "job_field": row.program.job_field,
            },
            "compat": float(row.compat),
            "level": details.get("level"),
            "interest_affinity": None if row.interest_affinity is None else float(row.interest_affinity),
            "skill_affinity": None if row.skill_affinity is None else float(row.skill_affinity),
            "origin": row.origin,
            "why": {
                "rules": [
                    {"id": rid, "text": RULES_BY_ID[rid].explanation}
                    for rid in row.rule_ids
                    if rid in RULES_BY_ID
                ],
                "strengths": [
                    {"code": s["code"], "name": names.get(s["code"], s["code"]), "score": s["score"]}
                    for s in details.get("strengths", [])
                ],
                "to_reinforce": [
                    {"code": c, "name": names.get(c, c)} for c in details.get("to_reinforce", [])
                ],
                "type_highlighted": details.get("type_highlighted", False),
            },
            "offerings": by_program.get(row.program_id, []),
        }

    items = [item(r) for r in rows]
    if department is None:
        main, also = items, []
    else:
        main = [i for i in items if i["offerings"]]
        also = [i for i in items if not i["offerings"]]
    return {
        "department": None if department is None else {"id": department.id, "name": department.name, "slug": department.slug},
        "recommendations": main,
        "also_interesting": also,
        "notice": NOTICE,
    }