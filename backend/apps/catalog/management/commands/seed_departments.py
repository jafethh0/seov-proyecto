from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Department

DEPARTMENTS = [
    "Atlántida",
    "Choluteca",
    "Colón",
    "Comayagua",
    "Copán",
    "Cortés",
    "El Paraíso",
    "Francisco Morazán",
    "Gracias a Dios",
    "Intibucá",
    "Islas de la Bahía",
    "La Paz",
    "Lempira",
    "Ocotepeque",
    "Olancho",
    "Santa Bárbara",
    "Valle",
    "Yoro",
]


class Command(BaseCommand):
    help = "Carga los 18 departamentos de Honduras (se puede ejecutar varias veces)."

    def handle(self, *args, **options):
        for name in DEPARTMENTS:
            Department.objects.update_or_create(
                slug=slugify(name), defaults={"name": name}
            )
        self.stdout.write(self.style.SUCCESS(f"{len(DEPARTMENTS)} departamentos listos."))

