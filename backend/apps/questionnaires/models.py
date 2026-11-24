# Create your models here.
"""
Cuestionario de SEOV (versión 1.x).

- Dimension: una sola tabla para intereses (INTEREST) y habilidades (SKILL).
- Questionnaire: versión identificable; solo una puede estar activa.
- Question: pertenece a una sección (intereses o habilidades) de una versión.
- AnswerOption: opciones con puntos. Los puntos mínimo y máximo de cada pregunta
  se obtienen de sus opciones (no hay constantes en el código del procesador).
- QuestionDimension: a qué dimensión aporta una pregunta y con qué peso.

Una evaluación enviada nunca debe modificar estas tablas: un cambio sustancial
se publica como una versión nueva del cuestionario.
"""
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Dimension(models.Model):
    class Kind(models.TextChoices):
        INTEREST = "INTEREST", "Interés"
        SKILL = "SKILL", "Habilidad"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["kind", "code"]
        constraints = [
            # Los intereses usan el prefijo INT- y las habilidades HAB-.
            models.CheckConstraint(
                condition=(Q(kind="INTEREST", code__startswith="INT-"))
                | (Q(kind="SKILL", code__startswith="HAB-")),
                name="dimension_code_matches_kind",
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Questionnaire(models.Model):
    title = models.CharField(max_length=150)
    version = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    interests_instructions = models.TextField(blank=True)
    skills_instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # A lo sumo un cuestionario activo a la vez.
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="only_one_active_questionnaire",
            )
        ]

    def __str__(self):
        return f"{self.title} v{self.version}"


class Question(models.Model):
    class Section(models.TextChoices):
        INTERESTS = "INTERESTS", "Intereses"
        SKILLS = "SKILLS", "Habilidades"

    class Kind(models.TextChoices):
        LIKERT = "LIKERT", "Escala de 1 a 5"
        CHOICE = "CHOICE", "Opción múltiple"

    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.PROTECT, related_name="questions"
    )
    section = models.CharField(max_length=10, choices=Section.choices)
    code = models.CharField(max_length=20)  # estable, ej. S-LOG-1
    text = models.TextField()
    passage = models.TextField(blank=True)  # lectura previa (opcional)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    order = models.PositiveSmallIntegerField()
    # Documentación para revisión y defensa (nunca se envía al estudiante).
    justification = models.TextField(blank=True)
    bias_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["questionnaire", "section", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["questionnaire", "code"], name="uniq_question_code_per_questionnaire"
            ),
            models.UniqueConstraint(
                fields=["questionnaire", "section", "order"],
                name="uniq_question_order_per_section",
            ),
        ]

    def __str__(self):
        return self.code

    @property
    def min_points(self):
        return min((o.points for o in self.options.all()), default=0)

    @property
    def max_points(self):
        return max((o.points for o in self.options.all()), default=0)


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=300)
    points = models.PositiveSmallIntegerField()
    order = models.PositiveSmallIntegerField()
    # Por qué recibe esos puntos (conducta observable). Nunca se envía al estudiante.
    criterion = models.TextField(blank=True)

    class Meta:
        ordering = ["question", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order"], name="uniq_option_order_per_question"
            )
        ]

    def __str__(self):
        return f"{self.question.code}: {self.text[:40]}"


class QuestionDimension(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="dimension_links"
    )
    dimension = models.ForeignKey(
        Dimension, on_delete=models.PROTECT, related_name="question_links"
    )
    weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "dimension"], name="uniq_question_dimension"
            ),
            models.CheckConstraint(condition=Q(weight__gt=0), name="question_dimension_weight_positive"),
        ]

    def __str__(self):
        return f"{self.question.code} -> {self.dimension.code} ({self.weight})"

    def clean(self):
        """Una pregunta de intereses solo aporta a intereses, y una de habilidades a habilidades."""
        if not (self.question_id and self.dimension_id):
            return
        expected = {
            Question.Section.INTERESTS: Dimension.Kind.INTEREST,
            Question.Section.SKILLS: Dimension.Kind.SKILL,
        }[self.question.section]
        if self.dimension.kind != expected:
            raise ValidationError(
                "La dimensión no corresponde a la sección de la pregunta "
                "(intereses con intereses, habilidades con habilidades)."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)