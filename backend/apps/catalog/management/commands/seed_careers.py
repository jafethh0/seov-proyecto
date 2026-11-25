"""
Carga las categorías (11 áreas) y las carreras genéricas con sus pesos de dimensiones.

    python manage.py seed_careers

Es idempotente: se puede repetir sin duplicar. NO crea instituciones ni ofertas.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog import seed_careers_data as data
from apps.catalog.models import CareerCategory, CareerDimension, CareerProgram
from apps.questionnaires.models import Dimension
from core.domain.areas import AREA_WEIGHTS


def effective_weights(area, overrides):
    weights = dict(AREA_WEIGHTS[area])
    for code, weight in overrides.items():
        if weight is None:
            weights.pop(code, None)
        else:
            weights[code] = weight
    return weights


class Command(BaseCommand):
    help = "Carga áreas y carreras genéricas con sus pesos."

    @transaction.atomic
    def handle(self, *args, **options):
        dimensions = {d.code: d for d in Dimension.objects.all()}
        if not dimensions:
            self.stderr.write("Primero ejecuta: python manage.py seed_questionnaire")
            return

        categories = {}
        for name in AREA_WEIGHTS:
            categories[name], _ = CareerCategory.objects.get_or_create(
                name=name, defaults={"slug": slugify(name)}
            )

        created = 0
        for name, program_type, area, description, job_field, overrides in data.CAREERS:
            weights = effective_weights(area, overrides)
            unknown = set(weights) - set(dimensions)
            if unknown:
                raise ValueError(f"{name}: dimensiones desconocidas {sorted(unknown)}")
            program, was_created = CareerProgram.objects.update_or_create(
                name=name,
                program_type=program_type,
                defaults={
                    "category": categories[area],
                    "description": description,
                    "job_field": job_field,
                    "is_active": True,
                },
            )
            created += was_created
            program.dimension_weights.all().delete()
            CareerDimension.objects.bulk_create(
                CareerDimension(program=program, dimension=dimensions[code], weight=weight)
                for code, weight in weights.items()
            )
        self.stdout.write(
            f"{len(data.CAREERS)} carreras listas ({created} nuevas) en {len(categories)} áreas."
        )