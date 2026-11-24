# Create your views here.
from django.db.models import Prefetch
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnswerOption, Question, Questionnaire
from .serializers import QuestionSerializer


class ActiveQuestionnaireView(APIView):
    """Cuestionario activo, con sus secciones y preguntas. Requiere sesión (JWT)."""

    def get(self, request):
        questionnaire = Questionnaire.objects.filter(is_active=True).first()
        if questionnaire is None:
            return Response(
                {"detail": "No hay un cuestionario activo."}, status=404
            )

        questions = (
            Question.objects.filter(questionnaire=questionnaire, is_active=True)
            .prefetch_related(
                Prefetch("options", queryset=AnswerOption.objects.order_by("order"))
            )
            .order_by("section", "order")
        )

        def section(key, title, instructions):
            items = [q for q in questions if q.section == key]
            return {
                "key": key,
                "title": title,
                "instructions": instructions,
                "questions": QuestionSerializer(items, many=True).data,
            }

        return Response(
            {
                "id": questionnaire.id,
                "title": questionnaire.title,
                "version": questionnaire.version,
                "description": questionnaire.description,
                "sections": [
                    section(
                        Question.Section.INTERESTS,
                        "Intereses",
                        questionnaire.interests_instructions,
                    ),
                    section(
                        Question.Section.SKILLS,
                        "Habilidades",
                        questionnaire.skills_instructions,
                    ),
                ],
            }
        )