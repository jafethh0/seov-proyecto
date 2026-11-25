"""
Puente entre la base de datos y el procesador de puntuaciones.

Arma los datos simples que necesita `core.imperative.score_processor`, aplica los niveles
(`core.functional.levels`) y guarda el resultado junto con la versión y la configuración
usadas. No contiene la fórmula: esa vive en core/.
"""
from decimal import Decimal

from apps.questionnaires.models import Dimension, Question
from core import config
from core.functional import levels
from core.imperative.score_processor import compute_dimension_scores

from . import inference, recommendations
from .models import Answer, EvaluationResult, ResultDimensionScore

RESULT_NOTICE = (
    "Estos resultados son orientativos: describen tus respuestas en esta evaluación y no "
    "son un diagnóstico, ni una predicción de éxito, ni deciden tu futuro académico."
)


def config_snapshot():
    """Valores de configuración que afectan al cálculo."""
    return {
        "scoring_version": config.SCORING_VERSION,
        "level_high": config.LEVEL_HIGH,
        "level_low": config.LEVEL_LOW,
        "min_answered_ratio": str(config.MIN_ANSWERED_RATIO),
        "min_valid_interest_dims": config.MIN_VALID_INTEREST_DIMS,
        "min_valid_skill_dims": config.MIN_VALID_SKILL_DIMS,
        "catalog_version": recommendations.catalog_version(),
    }


def build_inputs(evaluation):
    """Convierte los datos de la base en listas y diccionarios simples."""
    questions = []
    linked_codes = set()
    queryset = Question.objects.filter(
        questionnaire_id=evaluation.questionnaire_id, is_active=True
    ).prefetch_related("options", "dimension_links__dimension")
    for question in queryset:
        links = [
            (link.dimension.code, float(link.weight))
            for link in question.dimension_links.all()
            if link.dimension.is_active
        ]
        linked_codes.update(code for code, _ in links)
        questions.append(
            {
                "id": question.id,
                "min_points": question.min_points,
                "max_points": question.max_points,
                "links": links,
            }
        )

    dimensions = [
        (code, kind)
        for code, kind in Dimension.objects.filter(is_active=True)
        .order_by("kind", "code")
        .values_list("code", "kind")
        if code in linked_codes
    ]
    answers = dict(
        Answer.objects.filter(evaluation=evaluation).values_list("question_id", "option__points")
    )
    return dimensions, questions, answers


def store_result(evaluation):
    """Calcula y guarda el resultado de una evaluación (se llama al enviarla)."""
    dimensions, questions, answers = build_inputs(evaluation)
    scored = levels.with_levels(compute_dimension_scores(dimensions, questions, answers))

    result = EvaluationResult.objects.create(
        evaluation=evaluation,
        scoring_version=config.SCORING_VERSION,
        config=config_snapshot(),
    )
    by_code = {d.code: d for d in Dimension.objects.filter(code__in=[s["code"] for s in scored])}
    ResultDimensionScore.objects.bulk_create(
        [
            ResultDimensionScore(
                result=result,
                dimension=by_code[item["code"]],
                score=None if item["score"] is None else Decimal(str(item["score"])),
                level=item["level"],
                answered=item["answered"],
                total=item["total"],
                required=item["required"],
                is_valid=item["valid"],
            )
            for item in scored
        ]
    )
    return result


def serialize_result(result):
    """Resultado listo para la API, separado en intereses y habilidades."""

    def row(score):
        return {
            "code": score.dimension.code,
            "name": score.dimension.name,
            "score": None if score.score is None else float(score.score),
            "level": score.level,
            "valid": score.is_valid,
            "answered": score.answered,
            "total": score.total,
        }

    scores = list(result.scores.select_related("dimension"))
    return {
        "scoring_version": result.scoring_version,
        "created_at": result.created_at,
        "interests": [row(s) for s in scores if s.dimension.kind == Dimension.Kind.INTEREST],
        "skills": [row(s) for s in scores if s.dimension.kind == Dimension.Kind.SKILL],
        "inference": inference.serialize(result),
        "notice": RESULT_NOTICE,
    }