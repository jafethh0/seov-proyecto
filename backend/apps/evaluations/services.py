"""
Lógica de negocio de las evaluaciones. Las vistas solo validan la entrada y llaman aquí.

Todo lo que cambia el estado de una evaluación se hace dentro de una transacción con la
fila bloqueada (select_for_update), para que guardar y enviar no se pisen entre sí.
"""
from math import ceil

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.questionnaires.models import AnswerOption, Question, QuestionDimension, Questionnaire
from core import config

from . import inference, recommendations, scoring
from .models import Answer, Evaluation

SECTION_KIND = {"INTERESTS": "INTEREST", "SKILLS": "SKILL"}
MIN_VALID_DIMS = {
    "INTERESTS": config.MIN_VALID_INTEREST_DIMS,
    "SKILLS": config.MIN_VALID_SKILL_DIMS,
}


class Conflict(APIException):
    status_code = 409
    default_detail = "La operación entra en conflicto con el estado de la evaluación."
    default_code = "conflict"


class NotReadyToSubmit(Exception):
    """La evaluación aún no cumple el mínimo de dimensiones válidas. Lleva el progreso."""

    def __init__(self, current_progress):
        super().__init__("Faltan respuestas para poder enviar la evaluación.")
        self.progress = current_progress


# ---------------------------------------------------------------------------
# Cobertura y progreso (estilo imperativo: ciclos y condicionales explícitos)
# ---------------------------------------------------------------------------
def dimension_coverage(evaluation):
    """
    Por dimensión: total de preguntas, respondidas, mínimo requerido y si es válida.
    Una dimensión es válida si se respondió al menos MIN_ANSWERED_RATIO de sus preguntas.
    """
    links = QuestionDimension.objects.filter(
        question__questionnaire_id=evaluation.questionnaire_id,
        question__is_active=True,
        dimension__is_active=True,
    ).values_list("question_id", "dimension__code", "dimension__kind")
    answered_ids = set(
        Answer.objects.filter(evaluation=evaluation).values_list("question_id", flat=True)
    )

    coverage = {}
    for question_id, code, kind in links:
        entry = coverage.setdefault(code, {"kind": kind, "total": 0, "answered": 0})
        entry["total"] += 1
        if question_id in answered_ids:
            entry["answered"] += 1

    for entry in coverage.values():
        entry["required"] = ceil(entry["total"] * config.MIN_ANSWERED_RATIO)
        entry["valid"] = entry["answered"] >= entry["required"]
    return coverage


def progress(evaluation):
    """Avance por sección y si ya se puede enviar."""
    coverage = dimension_coverage(evaluation)
    active_questions = Question.objects.filter(
        questionnaire_id=evaluation.questionnaire_id, is_active=True
    )
    answered_questions = Answer.objects.filter(
        evaluation=evaluation, question__is_active=True
    )

    sections = {}
    can_submit = True
    for section, kind in SECTION_KIND.items():
        dims = [entry for entry in coverage.values() if entry["kind"] == kind]
        valid = sum(1 for entry in dims if entry["valid"])
        required = min(MIN_VALID_DIMS[section], len(dims))
        sections[section] = {
            "answered": answered_questions.filter(question__section=section).count(),
            "total": active_questions.filter(section=section).count(),
            "valid_dimensions": valid,
            "required_dimensions": required,
        }
        if valid < required:
            can_submit = False

    return {
        "answered": sum(s["answered"] for s in sections.values()),
        "total": sum(s["total"] for s in sections.values()),
        "sections": sections,
        "can_submit": can_submit,
    }


def detail(evaluation):
    """Representación completa de una evaluación (sin puntos ni respuestas correctas)."""
    return {
        "id": evaluation.id,
        "status": evaluation.status,
        "questionnaire": {
            "id": evaluation.questionnaire_id,
            "version": evaluation.questionnaire.version,
        },
        "started_at": evaluation.started_at,
        "submitted_at": evaluation.submitted_at,
        "answers": [
            {"question": question_id, "option": option_id}
            for question_id, option_id in evaluation.answers.values_list("question_id", "option_id")
        ],
        "progress": progress(evaluation),
        "result": result_payload(evaluation),
    }

def result_payload(evaluation):
    """Resultado de puntuación si la evaluación ya fue enviada; si no, None."""
    result = getattr(evaluation, "result", None)
    return scoring.serialize_result(result) if result else None


def get_result(user, pk):
    """Resultado de una evaluación propia. Borrador -> 409; ajena -> 404."""
    evaluation = get_object_or_404(Evaluation, pk=pk, user=user)
    payload = result_payload(evaluation)
    if payload is None:
        raise Conflict("La evaluación aún no se ha enviado.")
    return payload

# ---------------------------------------------------------------------------
# Operaciones
# ---------------------------------------------------------------------------
def _start(user):
    questionnaire = Questionnaire.objects.filter(is_active=True).first()
    if questionnaire is None:
        raise NotFound("No hay un cuestionario activo.")
    draft = (
        Evaluation.objects.select_for_update()
        .filter(user=user, status=Evaluation.Status.DRAFT)
        .first()
    )
    if draft and draft.questionnaire_id == questionnaire.id:
        return draft, False
    if draft:
        # Borrador de una versión que ya no está activa: no se puede enviar, se descarta.
        draft.delete()
    return Evaluation.objects.create(user=user, questionnaire=questionnaire), True


def start_evaluation(user):
    """Devuelve (evaluación, creada). Si ya hay un borrador vigente, lo reutiliza."""
    try:
        with transaction.atomic():
            return _start(user)
    except IntegrityError:  # dos solicitudes simultáneas: la otra ganó
        with transaction.atomic():
            return _start(user)


def _locked_draft(user, pk):
    evaluation = get_object_or_404(
        Evaluation.objects.select_for_update(), pk=pk, user=user  # solo las propias
    )
    if evaluation.status == Evaluation.Status.SUBMITTED:
        raise Conflict("La evaluación ya fue enviada y no se puede modificar.")
    if not evaluation.questionnaire.is_active:
        raise Conflict(
            "El cuestionario cambió de versión. Inicia una nueva evaluación."
        )
    return evaluation


@transaction.atomic
def save_answers(user, pk, items):
    """
    Guarda varias respuestas a la vez (todo o nada). `items` es una lista de
    {"question": id, "option": id | None}; option None borra la respuesta (omitir).
    """
    evaluation = _locked_draft(user, pk)

    question_ids = [item["question"] for item in items]
    questions = {
        q.id: q
        for q in Question.objects.filter(
            id__in=question_ids, questionnaire_id=evaluation.questionnaire_id, is_active=True
        )
    }
    missing = set(question_ids) - set(questions)
    if missing:
        raise ValidationError({"answers": f"Preguntas que no pertenecen al cuestionario: {sorted(missing)}"})

    option_ids = [item["option"] for item in items if item["option"] is not None]
    options = {o.id: o for o in AnswerOption.objects.filter(id__in=option_ids)}
    for item in items:
        option_id = item["option"]
        if option_id is None:
            continue
        option = options.get(option_id)
        if option is None or option.question_id != item["question"]:
            raise ValidationError(
                {"answers": f"La opción {option_id} no pertenece a la pregunta {item['question']}."}
            )

    for item in items:
        if item["option"] is None:
            Answer.objects.filter(evaluation=evaluation, question_id=item["question"]).delete()
        else:
            Answer.objects.update_or_create(
                evaluation=evaluation,
                question=questions[item["question"]],
                defaults={"option": options[item["option"]]},
            )
    evaluation.save(update_fields=["updated_at"])
    return evaluation


@transaction.atomic
def submit_evaluation(user, pk):
    """Envía la evaluación si cumple el mínimo de dimensiones válidas por sección."""
    evaluation = _locked_draft(user, pk)
    current = progress(evaluation)
    if not current["can_submit"]:
        raise NotReadyToSubmit(current)
    evaluation.status = Evaluation.Status.SUBMITTED
    evaluation.submitted_at = timezone.now()
    evaluation.save(update_fields=["status", "submitted_at", "updated_at"])
    result = scoring.store_result(evaluation)
    inference.store_inference(result)
    recommendations.store_recommendations(result)
    return evaluation

def get_recommendations(user, pk, department_slug=None, include_online=True):
    from apps.catalog.models import Department

    evaluation = get_object_or_404(Evaluation, pk=pk, user=user)
    result = getattr(evaluation, "result", None)
    if result is None:
        raise Conflict("La evaluación aún no se ha enviado.")
    if department_slug is None:
        profile = getattr(user, "profile", None)
        department = profile.preferred_department if profile else None
    elif department_slug == "all":
        department = None
    else:
        department = get_object_or_404(Department, slug=department_slug)
    return recommendations.serialize_recommendations(result, department, include_online)