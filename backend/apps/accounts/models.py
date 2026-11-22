# Create your models here.
from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    """
    Datos académicos mínimos del estudiante.

    Se usa el modelo User de Django para credenciales y roles:
    is_staff = administrador; el resto son estudiantes.
    """

    class EducationLevel(models.TextChoices):
        HIGH_SCHOOL = "HIGH_SCHOOL", "Estudiante de secundaria"
        UNIVERSITY = "UNIVERSITY", "Estudiante universitario"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    education_level = models.CharField(
        max_length=12,
        choices=EducationLevel.choices,
        default=EducationLevel.HIGH_SCHOOL,
    )
    # Carrera que cursa actualmente (para quien quiere cambiar de carrera).
    current_program = models.ForeignKey(
        "catalog.CareerProgram",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # Departamento donde quiere estudiar; filtra las ofertas del catálogo.
    preferred_department = models.ForeignKey(
        "catalog.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.user.email or self.user.username}"