# Create your views here.
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import sqlqueries


class SummaryView(APIView):
    """Resumen agregado para el equipo (solo personal autorizado). Sin datos personales."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(
            {
                "overview": sqlqueries.fetch_one("overview"),
                "dimensions": sqlqueries.fetch_all("dimension_summary"),
                "top_careers": sqlqueries.fetch_all("top_careers", {"limit": 10}),
                "coverage_by_department": sqlqueries.fetch_all("coverage_by_department"),
            }
        )