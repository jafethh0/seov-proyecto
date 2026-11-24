from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.questionnaires import seed_data
from apps.questionnaires.models import (
    AnswerOption,
    Dimension,
    Question,
    QuestionDimension,
    Questionnaire,
)


class Command(BaseCommand):
    help = "Carga las dimensiones y el cuestionario v1.0 (todo o nada)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Actualiza la versión existente. Úsalo SOLO si aún no hay evaluaciones "
            "enviadas con esa versión; si ya las hay, crea una versión nueva.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        exists = Questionnaire.objects.filter(version=seed_data.VERSION).exists()
        if exists and not options["update"]:
            raise CommandError(
                f"La versión {seed_data.VERSION} ya existe. Con --update se actualiza "
                "(solo si no hay evaluaciones enviadas con ella)."
            )

        dimensions = {}
        for kind, code, name, description in seed_data.DIMENSIONS:
            dimension, _ = Dimension.objects.update_or_create(
                code=code,
                defaults={"kind": kind, "name": name, "description": description},
            )
            dimensions[code] = dimension

        questionnaire, _ = Questionnaire.objects.update_or_create(
            version=seed_data.VERSION,
            defaults={
                "title": seed_data.TITLE,
                "description": seed_data.DESCRIPTION,
                "interests_instructions": seed_data.INTERESTS_INSTRUCTIONS,
                "skills_instructions": seed_data.SKILLS_INSTRUCTIONS,
            },
        )
        # Una sola versión activa: se desactivan las demás antes de activar esta.
        Questionnaire.objects.exclude(pk=questionnaire.pk).update(is_active=False)
        if not questionnaire.is_active:
            questionnaire.is_active = True
            questionnaire.save(update_fields=["is_active"])

        questions_data = seed_data.build_questions()

        # Se eliminan las preguntas de esta versión que ya no están en el banco (por
        # ejemplo, restos de un intento anterior). Si alguna tuviera respuestas, el
        # borrado falla y toda la operación se revierte.
        current_codes = [data["code"] for data in questions_data]
        questionnaire.questions.exclude(code__in=current_codes).delete()
        # Dimensiones que no son del banco y no tienen preguntas asociadas.
        Dimension.objects.exclude(code__in=dimensions).filter(question_links__isnull=True).delete()

        count = 0
        for data in questions_data:
            # Se desplazan los órdenes para no chocar con la restricción de unicidad
            # al reordenar durante --update.
            question, _ = Question.objects.update_or_create(
                questionnaire=questionnaire,
                code=data["code"],
                defaults={
                    "section": data["section"],
                    "kind": data["kind"],
                    "order": data["order"] + 1000,
                    "text": data["text"],
                    "passage": data["passage"],
                    "justification": data["justification"],
                    "bias_notes": data["bias_notes"],
                },
            )
            for position, (text, points, criterion) in enumerate(data["options"], start=1):
                AnswerOption.objects.update_or_create(
                    question=question,
                    order=position,
                    defaults={"text": text, "points": points, "criterion": criterion},
                )
            question.options.filter(order__gt=len(data["options"])).delete()
            QuestionDimension.objects.update_or_create(
                question=question,
                dimension=dimensions[data["dimension"]],
                defaults={"weight": 1},
            )
            count += 1

        # Segunda pasada: se asigna el orden definitivo (ya sin choques).
        for data in questions_data:
            Question.objects.filter(questionnaire=questionnaire, code=data["code"]).update(
                order=data["order"]
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Cuestionario v{seed_data.VERSION} listo: {len(dimensions)} dimensiones y {count} preguntas."
            )
        )