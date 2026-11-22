"""Pruebas del catálogo: filtrado por departamento y reglas de verificación."""
from datetime import date

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import (
    Campus,
    CareerCategory,
    CareerProgram,
    Department,
    Institution,
    ProgramOffering,
)


class CatalogApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_departments")
        cls.fm = Department.objects.get(slug="francisco-morazan")
        cls.cortes = Department.objects.get(slug="cortes")

        inst = Institution.objects.create(
            name="Institución de prueba", acronym="IDP", sector="PUBLIC"
        )
        cls.campus_fm = Campus.objects.create(
            institution=inst, name="Sede Tegucigalpa", department=cls.fm
        )
        cls.campus_cortes = Campus.objects.create(
            institution=inst, name="Sede San Pedro Sula", department=cls.cortes
        )
        cat = CareerCategory.objects.create(name="Tecnología", slug="tecnologia")
        cls.sistemas = CareerProgram.objects.create(
            name="Ingeniería en Sistemas", program_type="UNIVERSITY", category=cat
        )
        cls.electricidad = CareerProgram.objects.create(
            name="Técnico en Electricidad", program_type="TECHNICAL", category=cat
        )
        cls.derecho = CareerProgram.objects.create(
            name="Derecho", program_type="UNIVERSITY", category=cat
        )

        def offering(program, campus, modality, verified=True):
            return ProgramOffering.objects.create(
                program=program,
                campus=campus,
                official_name=program.name,
                modality=modality,
                source_url="https://example.org/oferta" if verified else "",
                verified_at=date(2026, 11, 22) if verified else None,
                is_active=verified,
            )

        offering(cls.sistemas, cls.campus_fm, "IN_PERSON")
        offering(cls.electricidad, cls.campus_cortes, "IN_PERSON")
        offering(cls.derecho, cls.campus_cortes, "ONLINE")
        # Oferta sin verificar: nunca debe mostrarse.
        offering(cls.derecho, cls.campus_fm, "IN_PERSON", verified=False)

    def names(self, response):
        return sorted(item["name"] for item in response.json())

    def test_departamentos_son_18(self):
        response = self.client.get("/api/v1/departments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 18)

    def test_filtra_por_departamento_e_incluye_en_linea(self):
        response = self.client.get("/api/v1/careers/?department=francisco-morazan")
        # Sistemas (presencial en FM) y Derecho (en línea, disponible desde cualquier lugar).
        self.assertEqual(self.names(response), ["Derecho", "Ingeniería en Sistemas"])

    def test_excluir_en_linea(self):
        response = self.client.get(
            "/api/v1/careers/?department=francisco-morazan&include_online=false"
        )
        self.assertEqual(self.names(response), ["Ingeniería en Sistemas"])

    def test_oferta_sin_verificar_no_se_muestra(self):
        response = self.client.get("/api/v1/careers/?department=francisco-morazan")
        derecho = next(c for c in response.json() if c["name"] == "Derecho")
        self.assertEqual(len(derecho["offerings"]), 1)
        self.assertEqual(derecho["offerings"][0]["modality"], "ONLINE")

    def test_filtra_por_tipo(self):
        response = self.client.get("/api/v1/careers/?department=cortes&type=TECHNICAL")
        self.assertEqual(self.names(response), ["Técnico en Electricidad"])

    def test_sin_departamento_devuelve_todo_lo_disponible(self):
        response = self.client.get("/api/v1/careers/")
        self.assertEqual(len(response.json()), 3)

    def test_catalogo_publico_ignora_token_invalido(self):
        response = self.client.get(
            "/api/v1/departments/", HTTP_AUTHORIZATION="Bearer token-invalido"
        )
        self.assertEqual(response.status_code, 200)

    def test_oferta_activa_exige_fuente_y_fecha(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProgramOffering.objects.create(
                program=self.sistemas,
                campus=self.campus_cortes,
                official_name="Sin fuente",
                modality="IN_PERSON",
                is_active=True,
            )