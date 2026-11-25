# Create your models here.
"""
Evaluaciones de los estudiantes.

Una evaluación enviada (SUBMITTED) es inmutable: no se pueden agregar, cambiar ni borrar
sus respuestas. Si el estudiante quiere repetirla, se crea una nueva y el historial se
conserva.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Evaluation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        SUBMITTED = "SUBMITTED", "Enviada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evaluations"
    )
    questionnaire = models.ForeignKey(
        "questionnaires.Questionnaire", on_delete=models.PROTECT, related_name="evaluations"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            # Un estudiante tiene a lo sumo un borrador a la vez.
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="DRAFT"),
                name="one_draft_per_user",
            ),
            # Enviada <=> tiene fecha de envío.
            models.CheckConstraint(
                condition=Q(status="DRAFT", submitted_at__isnull=True)
                | Q(status="SUBMITTED", submitted_at__isnull=False),
                name="submitted_status_matches_date",
            ),
        ]

    def __str__(self):
        return f"Evaluación {self.pk} ({self.get_status_display()})"


class Answer(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(
        "questionnaires.Question", on_delete=models.PROTECT, related_name="answers"
    )
    option = models.ForeignKey(
        "questionnaires.AnswerOption", on_delete=models.PROTECT, related_name="answers"
    )
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["evaluation", "question"]
        constraints = [
            models.UniqueConstraint(
                fields=["evaluation", "question"], name="one_answer_per_question"
            )
        ]

    def __str__(self):
        return f"Respuesta {self.question_id} de la evaluación {self.evaluation_id}"

    def clean(self):
        if self.evaluation.status == Evaluation.Status.SUBMITTED:
            raise ValidationError("La evaluación ya fue enviada y no se puede modificar.")
        if self.option.question_id != self.question_id:
            raise ValidationError("La opción no pertenece a la pregunta.")
        if self.question.questionnaire_id != self.evaluation.questionnaire_id:
            raise ValidationError("La pregunta no pertenece al cuestionario de la evaluación.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.evaluation.status == Evaluation.Status.SUBMITTED:
            raise ValidationError("La evaluación ya fue enviada y no se puede modificar.")
        return super().delete(*args, **kwargs)

class EvaluationResult(models.Model):
    evaluation = models.OneToOneField(Evaluation, on_delete=models.PROTECT, related_name="result")
    scoring_version = models.CharField(max_length=20)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resultado de la evaluación {self.evaluation_id} (v{self.scoring_version})"


class ResultDimensionScore(models.Model):
    class Level(models.TextChoices):
        HIGH = "HIGH", "Alto"
        MEDIUM = "MEDIUM", "Medio"
        LOW = "LOW", "Bajo"

    result = models.ForeignKey(EvaluationResult, on_delete=models.CASCADE, related_name="scores")
    dimension = models.ForeignKey(
        "questionnaires.Dimension", on_delete=models.PROTECT, related_name="result_scores"
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    level = models.CharField(max_length=6, choices=Level.choices, null=True, blank=True)
    answered = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    required = models.PositiveSmallIntegerField()
    is_valid = models.BooleanField()

    class Meta:
        ordering = ["dimension__kind", "dimension__code"]
        constraints = [
            models.UniqueConstraint(fields=["result", "dimension"], name="one_score_per_dimension_in_result"),
            models.CheckConstraint(
                condition=Q(score__isnull=True) | (Q(score__gte=0) & Q(score__lte=100)),
                name="result_score_between_0_and_100",
            ),
            models.CheckConstraint(
                condition=Q(is_valid=True, score__isnull=False, level__isnull=False)
                | Q(is_valid=False, score__isnull=True, level__isnull=True),
                name="result_score_matches_validity",
            ),
        ]

    def __str__(self):
        return f"{self.dimension_id}: {self.score}"

class ResultInference(models.Model):
    result = models.OneToOneField(
        EvaluationResult, on_delete=models.CASCADE, related_name="inference"
    )
    rules_version = models.CharField(max_length=20)
    facts = models.JSONField(default=list)
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inferencia del resultado {self.result_id} (reglas v{self.rules_version})"