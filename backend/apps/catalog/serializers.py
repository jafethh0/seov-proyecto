from rest_framework import serializers

from .models import Campus, CareerProgram, Department, Institution, ProgramOffering


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "slug")


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ("id", "name", "acronym", "sector", "website")


class CampusSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Campus
        fields = ("id", "name", "city", "institution", "department")


class OfferingSerializer(serializers.ModelSerializer):
    campus = CampusSerializer(read_only=True)

    class Meta:
        model = ProgramOffering
        fields = (
            "id",
            "official_name",
            "modality",
            "duration_months",
            "source_url",
            "verified_at",
            "campus",
        )


class CareerProgramSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="name", read_only=True)
    # Solo las ofertas disponibles (y del departamento pedido); la vista las precarga.
    offerings = OfferingSerializer(many=True, read_only=True, source="available_offerings")

    class Meta:
        model = CareerProgram
        fields = (
            "id",
            "name",
            "program_type",
            "category",
            "description",
            "general_profile",
            "job_field",
            "offerings",
        )