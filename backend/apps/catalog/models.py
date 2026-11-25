# Create your models here.
"""
Catálogo académico de SEOV.

Estructura:
- Department: los 18 departamentos de Honduras.
- Institution: universidad o centro técnico (pública o privada).
- Campus: sede o centro regional de una institución, ubicada en un departamento.
- CareerCategory: área de la carrera (Tecnología, Salud, etc.).
- CareerProgram: la carrera o programa técnico GENÉRICO (lo que recomienda el motor).
- ProgramOffering: dónde y cómo se imparte una carrera (sede, modalidad, fuente).

Regla de datos: una oferta solo se muestra al estudiante si está activa, tiene
fuente (source_url) y fecha de verificación (verified_at).
"""
from django.db import models
from django.db.models import Q


class Department(models.Model):
    """Departamento de Honduras. Se carga con: python manage.py seed_departments."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Institution(models.Model):
    """Universidad o centro técnico."""

    class Sector(models.TextChoices):
        PUBLIC = "PUBLIC", "Pública"
        PRIVATE = "PRIVATE", "Privada"

    name = models.CharField(max_length=150, unique=True)
    acronym = models.CharField(max_length=20, blank=True)
    sector = models.CharField(max_length=10, choices=Sector.choices)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.acronym or self.name


class Campus(models.Model):
    """Sede o centro regional de una institución, en un departamento."""

    institution = models.ForeignKey(
        Institution, on_delete=models.PROTECT, related_name="campuses"
    )
    name = models.CharField(max_length=150)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="campuses"
    )
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["institution__name", "name"]
        verbose_name_plural = "campuses"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"], name="uniq_campus_per_institution"
            )
        ]

    def __str__(self):
        return f"{self.institution} - {self.name}"


class CareerCategory(models.Model):
    """Área o categoría de carreras."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "career categories"

    def __str__(self):
        return self.name


class CareerProgram(models.Model):
    """Carrera universitaria o programa técnico genérico (no ligado a una institución)."""

    class ProgramType(models.TextChoices):
        UNIVERSITY = "UNIVERSITY", "Carrera universitaria"
        TECHNICAL = "TECHNICAL", "Programa técnico"

    name = models.CharField(max_length=150)
    program_type = models.CharField(max_length=12, choices=ProgramType.choices)
    category = models.ForeignKey(
        CareerCategory, on_delete=models.PROTECT, related_name="programs"
    )
    description = models.TextField(blank=True)
    general_profile = models.TextField(blank=True)
    job_field = models.TextField(blank=True)  # campo laboral orientativo
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "program_type"], name="uniq_program_name_type"
            )
        ]

    def __str__(self):
        return self.name


class ProgramOfferingQuerySet(models.QuerySet):
    def available(self):
        """Ofertas que se pueden mostrar al estudiante (verificadas y activas)."""
        return self.filter(
            is_active=True,
            verified_at__isnull=False,
            campus__is_active=True,
            campus__institution__is_active=True,
            program__is_active=True,
            ).exclude(source_url="").exclude(
            verification_status=ProgramOffering.VerificationStatus.OUTDATED
        )


class ProgramOffering(models.Model):
    """Una carrera impartida en una sede concreta, con su fuente verificable."""

    class Modality(models.TextChoices):
        IN_PERSON = "IN_PERSON", "Presencial"
        ONLINE = "ONLINE", "En línea"
        HYBRID = "HYBRID", "Semipresencial"

    program = models.ForeignKey(
        CareerProgram, on_delete=models.PROTECT, related_name="offerings"
    )
    campus = models.ForeignKey(
        Campus, on_delete=models.PROTECT, related_name="offerings"
    )
    class VerificationStatus(models.TextChoices):
        VERIFIED = "VERIFIED", "Verificada"
        OUTDATED = "OUTDATED", "Desactualizada"
    official_name = models.CharField(max_length=200)  # nombre oficial en la institución
    modality = models.CharField(max_length=10, choices=Modality.choices)
    duration_months = models.PositiveSmallIntegerField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    verified_at = models.DateField(null=True, blank=True)
    verified_at = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=10, choices=VerificationStatus.choices, default=VerificationStatus.VERIFIED
    )
    admission_requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    objects = ProgramOfferingQuerySet.as_manager()

    class Meta:
        ordering = ["program__name", "campus__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "campus", "modality"],
                name="uniq_offering_program_campus_modality",
            ),
            # Una oferta activa exige fuente y fecha de verificación.
            models.CheckConstraint(
                condition=Q(is_active=False)
                | (Q(verified_at__isnull=False) & ~Q(source_url="")),
                name="active_offering_requires_source_and_date",
            ),
        ]

    def __str__(self):
        return f"{self.official_name} @ {self.campus}"

class CareerDimension(models.Model):
    program = models.ForeignKey(
        CareerProgram, on_delete=models.CASCADE, related_name="dimension_weights"
    )
    dimension = models.ForeignKey(
        "questionnaires.Dimension", on_delete=models.PROTECT, related_name="career_weights"
    )
    weight = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["program__name", "dimension__kind", "dimension__code"]
        constraints = [
            models.UniqueConstraint(fields=["program", "dimension"], name="uniq_dimension_per_program"),
            models.CheckConstraint(
                condition=Q(weight__gte=1) & Q(weight__lte=3),
                name="career_dimension_weight_1_to_3",
            ),
        ]

    def __str__(self):
        return f"{self.program} - {self.dimension_id}: {self.weight}"