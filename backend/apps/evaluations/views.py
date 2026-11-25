# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Evaluation
from .serializers import EvaluationSummarySerializer, SaveAnswersSerializer

# Todas las vistas exigen sesión (JWT) y trabajan solo con las evaluaciones del propio
# usuario: las de otras personas responden 404.


class EvaluationListCreateView(APIView):
    def get(self, request):
        evaluations = Evaluation.objects.filter(user=request.user).select_related("questionnaire")
        return Response(EvaluationSummarySerializer(evaluations, many=True).data)

    def post(self, request):
        evaluation, created = services.start_evaluation(request.user)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(services.detail(evaluation), status=code)


class EvaluationDetailView(APIView):
    def get(self, request, pk):
        evaluation = get_object_or_404(
            Evaluation.objects.select_related("questionnaire"), pk=pk, user=request.user
        )
        return Response(services.detail(evaluation))


class EvaluationAnswersView(APIView):
    """PUT {"answers": [{"question": 1, "option": 3}, {"question": 2, "option": null}]}"""

    def put(self, request, pk):
        serializer = SaveAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation = services.save_answers(request.user, pk, serializer.validated_data["answers"])
        return Response(services.detail(evaluation))


class EvaluationSubmitView(APIView):
    def post(self, request, pk):
        try:
            evaluation = services.submit_evaluation(request.user, pk)
        except services.NotReadyToSubmit as error:
            # Se responde a mano para conservar los números del progreso (DRF los
            # convertiría en texto dentro de un ValidationError).
            return Response(
                {"detail": str(error), "progress": error.progress},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(services.detail(evaluation))
    
class EvaluationResultView(APIView):
    def get(self, request, pk):
        return Response(services.get_result(request.user, pk))

class EvaluationRecommendationsView(APIView):
    def get(self, request, pk):
        include_online = request.query_params.get("include_online", "true").lower() != "false"
        data = services.get_recommendations(
            request.user, pk, request.query_params.get("department"), include_online
        )
        return Response(data)