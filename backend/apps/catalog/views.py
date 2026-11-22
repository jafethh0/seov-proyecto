# Create your views here.
from django.shortcuts import render
from django.db.models import Prefetch, Q
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import CareerProgram, Department, ProgramOffering
from .serializers import CareerProgramSerializer, DepartmentSerializer


class PublicCatalogView:
    """El catálogo es público: no exige token (ni valida uno inválido)."""

    permission_classes = [AllowAny]
    authentication_classes = []


class DepartmentListView(PublicCatalogView, generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    pagination_class = None


class CareerQueryMixin(PublicCatalogView):
    """
    Devuelve solo carreras activas con al menos una oferta disponible.

    Parámetros opcionales:
      department      slug del departamento (ej. francisco-morazan)
      include_online  "false" para excluir ofertas en línea (por defecto se incluyen,
                      porque se pueden cursar desde cualquier departamento)
      type            UNIVERSITY o TECHNICAL
      category        slug de la categoría
      q               texto contenido en el nombre
    """

    serializer_class = CareerProgramSerializer

    def _offerings(self):
        params = self.request.query_params
        offerings = ProgramOffering.objects.available()
        department = params.get("department")
        if department:
            condition = Q(campus__department__slug=department)
            if params.get("include_online", "true").lower() != "false":
                condition |= Q(modality=ProgramOffering.Modality.ONLINE)
            offerings = offerings.filter(condition)
        return offerings

    def get_queryset(self):
        params = self.request.query_params
        offerings = self._offerings()
        queryset = (
            CareerProgram.objects.filter(
                is_active=True, pk__in=offerings.values("program_id")
            )
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "offerings",
                    queryset=offerings.select_related(
                        "campus__institution", "campus__department"
                    ),
                    to_attr="available_offerings",
                )
            )
        )
        if params.get("type"):
            queryset = queryset.filter(program_type=params["type"])
        if params.get("category"):
            queryset = queryset.filter(category__slug=params["category"])
        if params.get("q"):
            queryset = queryset.filter(name__icontains=params["q"])
        return queryset.order_by("name")


class CareerListView(CareerQueryMixin, generics.ListAPIView):
    pagination_class = None


class CareerDetailView(CareerQueryMixin, generics.RetrieveAPIView):
    pass