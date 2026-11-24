"""Pruebas del cuestionario: integridad del banco, siembra y API pública."""
import json
from collections import Counter
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.questionnaires.models import (
    AnswerOption,
    Dimension,
    Question,
    QuestionDimension,
    Questionnaire,
)

ACTIVE = "/api/v1/questionnaires/active/"


def seed(*args):
    call_command("seed_questionnaire", *args, stdout=StringIO())


def dimension_scores(questionnaire, pick):
    """
    Puntuación 0-100 por dimensión con la fórmula del diseño, usando solo los datos de
    la base: valor = (puntos - mínimo) / (máximo - mínimo) de cada pregunta, ponderado.
    `pick(question)` devuelve los puntos elegidos.
    """
    totals = {}
    questions = Question.objects.filter(questionnaire=questionnaire).prefetch_related(
        "options", "dimension_links__dimension"
    )
    for question in questions:
        low, high = question.min_points, question.max_points
        value = (pick(question) - low) / (high - low)
        for link in question.dimension_links.all():
            weight = float(link.weight)
            num, den = totals.get(link.dimension.code, (0.0, 0.0))
            totals[link.dimension.code] = (num + weight * value, den + weight)
    return {code: 100 * num / den for code, (num, den) in totals.items()}


class SeedIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.questionnaire = Questionnaire.objects.get(version="1.0")

    def test_dimensiones_7_intereses_y_7_habilidades(self):
        self.assertEqual(Dimension.objects.filter(kind="INTEREST").count(), 7)
        self.assertEqual(Dimension.objects.filter(kind="SKILL").count(), 7)

    def test_49_preguntas_28_intereses_y_21_habilidades(self):
        questions = Question.objects.filter(questionnaire=self.questionnaire)
        self.assertEqual(questions.count(), 49)
        self.assertEqual(questions.filter(section="INTERESTS").count(), 28)
        self.assertEqual(questions.filter(section="SKILLS").count(), 21)

    def test_cuatro_preguntas_por_interes_y_tres_por_habilidad(self):
        for dimension in Dimension.objects.all():
            expected = 4 if dimension.kind == "INTEREST" else 3
            self.assertEqual(dimension.question_links.count(), expected, dimension.code)

    def test_cada_pregunta_aporta_a_una_dimension_de_su_tipo(self):
        for question in Question.objects.prefetch_related("dimension_links__dimension"):
            links = list(question.dimension_links.all())
            self.assertEqual(len(links), 1, question.code)
            expected = "INTEREST" if question.section == "INTERESTS" else "SKILL"
            self.assertEqual(links[0].dimension.kind, expected, question.code)

    def test_likert_tiene_cinco_opciones_de_1_a_5(self):
        for question in Question.objects.filter(kind="LIKERT").prefetch_related("options"):
            self.assertEqual([o.points for o in question.options.all()], [1, 2, 3, 4, 5])
            self.assertEqual((question.min_points, question.max_points), (1, 5))

    def test_preguntas_de_habilidades_tienen_puntaje_valido(self):
        for question in Question.objects.filter(kind="CHOICE").prefetch_related("options"):
            points = [o.points for o in question.options.all()]
            self.assertEqual(question.min_points, 0, question.code)
            self.assertIn(question.max_points, (1, 2), question.code)
            self.assertGreaterEqual(len(points), 4, question.code)
            if question.max_points == 1:
                # Con respuesta correcta: exactamente una opción vale 1.
                self.assertEqual(points.count(1), 1, question.code)
            else:
                # Situacional: hay al menos una opción de 2 y criterio en cada opción.
                self.assertIn(2, points, question.code)
                for option in question.options.all():
                    self.assertTrue(option.criterion, f"{question.code}: opción sin criterio")

    def test_toda_pregunta_tiene_justificacion_y_nota_de_sesgos(self):
        for question in Question.objects.all():
            self.assertTrue(question.justification, question.code)
            self.assertTrue(question.bias_notes, question.code)

    def test_la_respuesta_correcta_no_se_concentra_en_una_posicion(self):
        positions = []
        for question in Question.objects.filter(kind="CHOICE", questionnaire=self.questionnaire):
            options = list(question.options.all())
            if question.max_points == 1:
                positions.append([o.points for o in options].index(1))
        counts = Counter(positions)
        self.assertGreaterEqual(len(counts), 4)  # aparece en las 4 posiciones
        self.assertLessEqual(max(counts.values()) / len(positions), 0.4)

    def test_respuestas_maximas_dan_100_y_minimas_0_en_las_14_dimensiones(self):
        best = dimension_scores(self.questionnaire, lambda q: q.max_points)
        worst = dimension_scores(self.questionnaire, lambda q: q.min_points)
        self.assertEqual(len(best), 14)
        for code in best:
            self.assertAlmostEqual(best[code], 100.0, places=6, msg=code)
            self.assertAlmostEqual(worst[code], 0.0, places=6, msg=code)

    def test_respuesta_intermedia_coincide_con_la_formula(self):
        # Todas las respuestas de interés en "Algo" (3): (3-1)/4 = 50 en cada dimensión.
        scores = dimension_scores(
            self.questionnaire,
            lambda q: 3 if q.kind == "LIKERT" else q.max_points,
        )
        for code, value in scores.items():
            expected = 50.0 if code.startswith("INT-") else 100.0
            self.assertAlmostEqual(value, expected, places=6, msg=code)

    def test_orden_mezclado_sin_bloques_por_dimension(self):
        first = list(
            Question.objects.filter(section="INTERESTS").order_by("order")[:7]
            .values_list("code", flat=True)
        )
        self.assertEqual(len(set(c.split("-")[1] for c in first)), 7)


class SeedCommandTests(TestCase):
    def test_segunda_ejecucion_sin_update_falla_y_no_duplica(self):
        seed()
        with self.assertRaises(CommandError):
            seed()
        self.assertEqual(Question.objects.count(), 49)

    def test_update_es_idempotente(self):
        seed()
        options_before = AnswerOption.objects.count()
        seed("--update")
        self.assertEqual(Question.objects.count(), 49)
        self.assertEqual(AnswerOption.objects.count(), options_before)
        self.assertEqual(QuestionDimension.objects.count(), 49)
        self.assertEqual(Questionnaire.objects.filter(is_active=True).count(), 1)


class SeedLeftoversTests(TestCase):
    def test_update_limpia_restos_de_un_intento_anterior(self):
        """Reproduce un intento previo: misma versión, otras preguntas y otra dimensión."""
        old_dimension = Dimension.objects.create(kind="INTEREST", code="INT-VIEJA", name="Vieja")
        old = Questionnaire.objects.create(title="Intento previo", version="1.0", is_active=True)
        for number in range(1, 4):
            question = Question.objects.create(
                questionnaire=old,
                section="INTERESTS",
                code=f"VIEJA-{number}",
                text="Pregunta vieja",
                kind="LIKERT",
                order=number,  # ocupa los órdenes 1, 2 y 3
            )
            AnswerOption.objects.create(question=question, text="Sí", points=1, order=1)
            QuestionDimension.objects.create(question=question, dimension=old_dimension)

        seed("--update")

        questionnaire = Questionnaire.objects.get(version="1.0")
        self.assertEqual(Question.objects.filter(questionnaire=questionnaire).count(), 49)
        self.assertFalse(Question.objects.filter(code__startswith="VIEJA").exists())
        self.assertFalse(Dimension.objects.filter(code="INT-VIEJA").exists())
        self.assertEqual(Dimension.objects.count(), 14)
        orders = list(
            Question.objects.filter(section="INTERESTS").order_by("order").values_list("order", flat=True)
        )
        self.assertEqual(orders, list(range(1, 29)))
        self.assertEqual(Questionnaire.objects.filter(is_active=True).count(), 1)


class ModelRulesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def test_solo_un_cuestionario_activo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Questionnaire.objects.create(title="Otro", version="9.9", is_active=True)

    def test_dimension_exige_prefijo_segun_tipo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Dimension.objects.create(kind="SKILL", code="INT-XXX", name="Mal")

    def test_pregunta_de_intereses_no_acepta_dimension_de_habilidad(self):
        question = Question.objects.get(code="I-CIE-1")
        skill = Dimension.objects.get(code="HAB-LOG")
        with self.assertRaises(ValidationError):
            QuestionDimension.objects.create(question=question, dimension=skill, weight=1)

    def test_peso_debe_ser_positivo(self):
        question = Question.objects.get(code="I-CIE-1")
        link = question.dimension_links.get()
        link.weight = Decimal("0")
        with self.assertRaises(IntegrityError), transaction.atomic():
            link.save()


class ActiveQuestionnaireApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def login(self):
        self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "ana@example.com",
                "password": "ClaveSegura#2026",
                "first_name": "Ana",
                "education_level": "HIGH_SCHOOL",
            },
            content_type="application/json",
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "ana@example.com", "password": "ClaveSegura#2026"},
            content_type="application/json",
        )
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}

    def test_exige_autenticacion(self):
        self.assertEqual(self.client.get(ACTIVE).status_code, 401)

    def test_devuelve_dos_secciones_con_49_preguntas(self):
        response = self.client.get(ACTIVE, **self.login())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["version"], "1.0")
        self.assertEqual([s["key"] for s in body["sections"]], ["INTERESTS", "SKILLS"])
        self.assertEqual([len(s["questions"]) for s in body["sections"]], [28, 21])
        for section in body["sections"]:
            self.assertTrue(section["instructions"])

    def test_no_revela_puntos_criterios_ni_dimensiones(self):
        raw = json.dumps(self.client.get(ACTIVE, **self.login()).json()).lower()
        for forbidden in ("points", "criterion", "justification", "bias", "dimension", "weight"):
            self.assertNotIn(forbidden, raw)
        question = self.client.get(ACTIVE, **self.login()).json()["sections"][1]["questions"][0]
        self.assertEqual(set(question), {"id", "kind", "text", "passage", "options"})
        self.assertEqual(set(question["options"][0]), {"id", "text"})

    def test_sin_cuestionario_activo_devuelve_404(self):
        Questionnaire.objects.update(is_active=False)
        self.assertEqual(self.client.get(ACTIVE, **self.login()).status_code, 404)