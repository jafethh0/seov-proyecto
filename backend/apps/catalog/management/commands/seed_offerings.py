"""
Carga las ofertas académicas reales (con fuente y fecha de verificación).

    python manage.py seed_offerings

Requiere haber ejecutado antes: seed_departments y seed_careers.
Es idempotente: se puede repetir; actualiza lo existente sin duplicar.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog import seed_offerings_data as data
from apps.catalog.models import (
    Campus,
    CareerProgram,
    Department,
    Institution,
    ProgramOffering,
)


class Command(BaseCommand):
    help = "Carga ofertas académicas reales (UNAH: Francisco Morazán y Cortés)."

    @transaction.atomic
    def handle(self, *args, **options):
        institution, _ = Institution.objects.update_or_create(
            name=data.UNAH_INSTITUTION["name"], defaults=data.UNAH_INSTITUTION
        )

        campuses = {}
        for key, info in data.UNAH_CAMPUSES.items():
            try:
                department = Department.objects.get(name=info["department"])
            except Department.DoesNotExist:
                raise CommandError("Faltan los departamentos: ejecuta seed_departments.")
            campus, _ = Campus.objects.update_or_create(
                institution=institution,
                name=info["name"],
                defaults={"department": department, "city": info["city"], "is_active": True},
            )
            campuses[key] = campus

        created = updated = 0
        for generic, official, years, campus_keys in data.UNAH_OFFERINGS:
            try:
                program = CareerProgram.objects.get(name=generic)
            except CareerProgram.DoesNotExist:
                raise CommandError(f"No existe la carrera genérica «{generic}»: ejecuta seed_careers.")
            for key in campus_keys:
                _, was_created = ProgramOffering.objects.update_or_create(
                    program=program,
                    campus=campuses[key],
                    modality=ProgramOffering.Modality.IN_PERSON,
                    defaults={
                        "official_name": official,
                        "duration_months": round(years * 12),
                        "source_url": data.UNAH_SOURCE,
                        "verified_at": data.UNAH_VERIFIED_AT,
                        "verification_status": ProgramOffering.VerificationStatus.VERIFIED,
                        "is_active": True,
                    },
                )
                created += was_created
                updated += not was_created

        self.stdout.write(self.style.SUCCESS(f"Ofertas nuevas: {created} · actualizadas: {updated}"))