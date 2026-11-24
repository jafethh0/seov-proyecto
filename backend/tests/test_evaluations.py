"""Pruebas de evaluaciones: borrador, guardado, envío, propiedad e inmutabilidad."""
import json
from io import StringIO
from math import ceil

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from apps.evaluations import services
from apps.evaluations.models import Answer, Evaluation
from apps.questionnaires.models import (
    AnswerOption,
    Question,
    QuestionDimension,
    Questionnaire,
)
from core import config

User = get_user_model()

LIST = "/api/v1/evaluations/"
INTERESTS = ["INT-CIE", "INT-TEC", "INT-SOC", "INT-ART", "INT-ADM", "INT-PRA", "INT-COM"]
SKILLS = ["HAB-LOG", "HAB-NUM", "HAB-VER", "HAB-CRE", "HAB-SOC", "HAB-ORG", "HAB-TEC"]


def url(pk, tail=""):
    return f"{LIST}{pk}/{tail}"


def items_for(codes, limit=None):
    """Respuestas (primera opción) para las preguntas de las dimensiones dadas."""
    items = []
    for code in codes:
        links = (
            QuestionDimension.objects.filter(dimension__code=code)
            .select_related("question")
            .order_by("question__order")
        )
        for link in list(links)[:limit]:
            option = list(link.question.options.order_by("order"))[0]
            items.append({"question": link.question_id, "option": option.id})
    return items


class EvaluationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_questionnaire", stdout=StringIO())
        cls.ana = User.objects.create_user("ana@example.com", "ana@example.com", "ClaveSegura#2026")
        cls.luis = User.objects.create_user("luis@example.com", "luis@example.com", "ClaveSegura#2026")

    def headers(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}

    def start(self, user=None):
        user = user or self.ana
        return self.client.post(LIST, **self.headers(user))

    def put(self, pk, items, user=None):
        user = user or self.ana
        return self.client.put(
            url(pk, "answers/"),
            json.dumps({"answers": items}),
            content_type="application/json",
            **self.headers(user),
        )

    def submit(self, pk, user=None):
        user = user or self.ana
        return self.client.post(url(pk, "submit/"), **self.headers(user))

    def ready_evaluation(self):
        """Borrador con 5 dimensiones de intereses y 5 de habilidades completas."""
        pk = self.start().json()["id"]
        self.put(pk, items_for(INTERESTS[:5]) + items_for(SKILLS[:5]))
        return pk


class StartAndOwnershipTests(EvaluationTestCase):
    def test_exige_autenticacion(self):
        self.assertEqual(self.client.post(LIST).status_code, 401)
        self.assertEqual(self.client.get(LIST).status_code, 401)

    def test_crea_borrador_y_lo_reutiliza(self):
        first = self.start()
        self.assertEqual(first.status_code, 201)
        body = first.json()
        self.assertEqual(body["status"], "DRAFT")
        self.assertEqual(body["questionnaire"]["version"], "1.0")
        self.assertEqual(body["progress"]["total"], 49)
        self.assertFalse(body["progress"]["can_submit"])
        second = self.start()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["id"], body["id"])
        self.assertEqual(Evaluation.objects.filter(user=self.ana).count(), 1)

    def test_la_bd_impide_dos_borradores(self):
        self.start()
        questionnaire = Questionnaire.objects.get(is_active=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Evaluation.objects.create(user=self.ana, questionnaire=questionnaire)

    def test_estado_enviada_exige_fecha(self):
        questionnaire = Questionnaire.objects.get(is_active=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Evaluation.objects.create(
                user=self.ana, questionnaire=questionnaire, status="SUBMITTED"
            )

    def test_nadie_ve_ni_modifica_la_evaluacion_de_otro(self):
        pk = self.start().json()["id"]
        other = self.headers(self.luis)
        self.assertEqual(self.client.get(url(pk), **other).status_code, 404)
        self.assertEqual(self.put(pk, items_for(["INT-CIE"], 1), user=self.luis).status_code, 404)
        self.assertEqual(self.submit(pk, user=self.luis).status_code, 404)
        self.assertEqual(self.client.get(LIST, **other).json(), [])

    def test_lista_solo_las_propias(self):
        self.start()
        self.start(self.luis)
        listed = self.client.get(LIST, **self.headers(self.ana)).json()
        self.assertEqual(len(listed), 1)


class SaveAnswersTests(EvaluationTestCase):
    def test_guardar_actualiza_el_progreso(self):
        pk = self.start().json()["id"]
        response = self.put(pk, items_for(["INT-CIE"]))
        self.assertEqual(response.status_code, 200)
        progress = response.json()["progress"]
        self.assertEqual(progress["answered"], 4)
        self.assertEqual(progress["sections"]["INTERESTS"]["answered"], 4)
        self.assertEqual(progress["sections"]["INTERESTS"]["valid_dimensions"], 1)
        self.assertEqual(progress["sections"]["SKILLS"]["answered"], 0)

    def test_reanudar_devuelve_las_respuestas_guardadas(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(["INT-CIE"], 2))
        detail = self.client.get(url(pk), **self.headers(self.ana)).json()
        self.assertEqual(len(detail["answers"]), 2)

    def test_cambiar_una_respuesta_no_duplica(self):
        pk = self.start().json()["id"]
        question = Question.objects.get(code="I-CIE-1")
        first, last = list(question.options.order_by("order"))[0], list(question.options.order_by("order"))[-1]
        self.put(pk, [{"question": question.id, "option": first.id}])
        self.put(pk, [{"question": question.id, "option": last.id}])
        answers = Answer.objects.filter(evaluation_id=pk)
        self.assertEqual(answers.count(), 1)
        self.assertEqual(answers.get().option_id, last.id)

    def test_option_null_borra_la_respuesta(self):
        pk = self.start().json()["id"]
        item = items_for(["INT-CIE"], 1)[0]
        self.put(pk, [item])
        self.put(pk, [{"question": item["question"], "option": None}])
        self.assertEqual(Answer.objects.filter(evaluation_id=pk).count(), 0)

    def test_opcion_de_otra_pregunta_es_rechazada(self):
        pk = self.start().json()["id"]
        q1, q2 = Question.objects.get(code="I-CIE-1"), Question.objects.get(code="I-CIE-2")
        response = self.put(pk, [{"question": q1.id, "option": q2.options.first().id}])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Answer.objects.count(), 0)

    def test_pregunta_ajena_al_cuestionario_es_rechazada(self):
        pk = self.start().json()["id"]
        other = Questionnaire.objects.create(title="Otro", version="9.0")
        foreign = Question.objects.create(
            questionnaire=other, section="INTERESTS", code="X-1", text="x", kind="LIKERT", order=1
        )
        option = AnswerOption.objects.create(question=foreign, text="Sí", points=1, order=1)
        response = self.put(pk, [{"question": foreign.id, "option": option.id}])
        self.assertEqual(response.status_code, 400)

    def test_pregunta_inactiva_es_rechazada(self):
        pk = self.start().json()["id"]
        item = items_for(["INT-CIE"], 1)[0]
        Question.objects.filter(pk=item["question"]).update(is_active=False)
        self.assertEqual(self.put(pk, [item]).status_code, 400)

    def test_todo_o_nada_si_una_respuesta_es_invalida(self):
        pk = self.start().json()["id"]
        good = items_for(["INT-CIE"], 1)[0]
        bad = {"question": good["question"] + 1, "option": good["option"]}  # opción de otra pregunta
        self.assertEqual(self.put(pk, [good, bad]).status_code, 400)
        self.assertEqual(Answer.objects.count(), 0)

    def test_preguntas_repetidas_y_cuerpo_vacio(self):
        pk = self.start().json()["id"]
        item = items_for(["INT-CIE"], 1)[0]
        self.assertEqual(self.put(pk, [item, item]).status_code, 400)
        self.assertEqual(self.put(pk, []).status_code, 400)

    def test_la_bd_impide_dos_respuestas_a_la_misma_pregunta(self):
        pk = self.start().json()["id"]
        item = items_for(["INT-CIE"], 1)[0]
        self.put(pk, [item])
        evaluation = Evaluation.objects.get(pk=pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Answer.objects.bulk_create(
                [Answer(evaluation=evaluation, question_id=item["question"], option_id=item["option"])]
            )

    def test_la_respuesta_no_expone_puntos(self):
        pk = self.start().json()["id"]
        raw = json.dumps(self.put(pk, items_for(["HAB-LOG"])).json()).lower()
        # Ni puntos ni criterios ni a qué dimensión pertenece cada pregunta.
        for forbidden in ("points", "criterion", "weight", "int-", "hab-"):
            self.assertNotIn(forbidden, raw)


class ValidityTests(EvaluationTestCase):
    def coverage(self, pk):
        return services.dimension_coverage(Evaluation.objects.get(pk=pk))

    def test_umbral_de_dos_tercios_en_intereses(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(["INT-CIE"], 3) + items_for(["INT-TEC"], 2))
        coverage = self.coverage(pk)
        self.assertEqual(coverage["INT-CIE"]["required"], 3)  # ceil(4 * 2/3)
        self.assertTrue(coverage["INT-CIE"]["valid"])  # 3 de 4
        self.assertFalse(coverage["INT-TEC"]["valid"])  # 2 de 4

    def test_umbral_de_dos_tercios_en_habilidades(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(["HAB-LOG"], 2) + items_for(["HAB-NUM"], 1))
        coverage = self.coverage(pk)
        self.assertEqual(coverage["HAB-LOG"]["required"], 2)  # ceil(3 * 2/3)
        self.assertTrue(coverage["HAB-LOG"]["valid"])  # 2 de 3
        self.assertFalse(coverage["HAB-NUM"]["valid"])  # 1 de 3

    def test_el_minimo_exacto_sale_de_la_configuracion(self):
        self.assertEqual(ceil(3 * config.MIN_ANSWERED_RATIO), 2)
        self.assertEqual(ceil(4 * config.MIN_ANSWERED_RATIO), 3)
        self.assertEqual(ceil(1 * config.MIN_ANSWERED_RATIO), 1)


class SubmitTests(EvaluationTestCase):
    def test_rechaza_envio_si_faltan_dimensiones_validas(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(INTERESTS[:4]) + items_for(SKILLS[:5]))  # solo 4 de intereses
        response = self.submit(pk)
        self.assertEqual(response.status_code, 400)
        progress = response.json()["progress"]
        self.assertEqual(progress["sections"]["INTERESTS"]["valid_dimensions"], 4)
        self.assertEqual(progress["sections"]["INTERESTS"]["required_dimensions"], 5)
        self.assertEqual(Evaluation.objects.get(pk=pk).status, "DRAFT")

    def test_rechaza_envio_vacio(self):
        pk = self.start().json()["id"]
        self.assertEqual(self.submit(pk).status_code, 400)

    def test_envia_con_cinco_y_cinco_dimensiones_validas(self):
        pk = self.ready_evaluation()
        response = self.submit(pk)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "SUBMITTED")
        self.assertIsNotNone(body["submitted_at"])

    def test_dimensiones_parciales_pero_validas_alcanzan(self):
        pk = self.start().json()["id"]
        # 3 de 4 en intereses y 2 de 3 en habilidades: validas, aunque falten preguntas.
        self.put(pk, items_for(INTERESTS[:5], 3) + items_for(SKILLS[:5], 2))
        self.assertEqual(self.submit(pk).status_code, 200)

    def test_no_se_envia_dos_veces(self):
        pk = self.ready_evaluation()
        self.assertEqual(self.submit(pk).status_code, 200)
        self.assertEqual(self.submit(pk).status_code, 409)

    def test_enviada_es_inmutable(self):
        pk = self.ready_evaluation()
        self.submit(pk)
        before = Answer.objects.filter(evaluation_id=pk).count()
        self.assertEqual(self.put(pk, items_for(["INT-COM"])).status_code, 409)
        self.assertEqual(Answer.objects.filter(evaluation_id=pk).count(), before)

        answer = Answer.objects.filter(evaluation_id=pk).first()
        with self.assertRaises(ValidationError):
            answer.save()
        with self.assertRaises(ValidationError):
            answer.delete()

    def test_repetir_crea_una_evaluacion_nueva_y_conserva_el_historial(self):
        old_pk = self.ready_evaluation()
        self.submit(old_pk)
        new = self.start()
        self.assertEqual(new.status_code, 201)
        self.assertNotEqual(new.json()["id"], old_pk)
        self.assertEqual(Evaluation.objects.get(pk=old_pk).status, "SUBMITTED")
        self.assertGreater(Answer.objects.filter(evaluation_id=old_pk).count(), 0)
        self.assertEqual(len(self.client.get(LIST, **self.headers(self.ana)).json()), 2)


class QuestionnaireVersionTests(EvaluationTestCase):
    def publish_new_version(self):
        Questionnaire.objects.update(is_active=False)
        return Questionnaire.objects.create(title="Nuevo", version="2.0", is_active=True)

    def test_borrador_de_version_anterior_no_se_puede_guardar_ni_enviar(self):
        pk = self.ready_evaluation()
        self.publish_new_version()
        self.assertEqual(self.put(pk, items_for(["INT-COM"], 1)).status_code, 409)
        self.assertEqual(self.submit(pk).status_code, 409)

    def test_iniciar_descarta_el_borrador_obsoleto_y_crea_uno_nuevo(self):
        old_pk = self.start().json()["id"]
        new_version = self.publish_new_version()
        response = self.start()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["questionnaire"]["version"], "2.0")
        self.assertFalse(Evaluation.objects.filter(pk=old_pk).exists())
        self.assertEqual(Evaluation.objects.get(user=self.ana).questionnaire_id, new_version.id)

    def test_evaluacion_enviada_conserva_su_version(self):
        pk = self.ready_evaluation()
        self.submit(pk)
        self.publish_new_version()
        detail = self.client.get(url(pk), **self.headers(self.ana)).json()
        self.assertEqual(detail["questionnaire"]["version"], "1.0")
        self.assertEqual(detail["status"], "SUBMITTED")

    def test_sin_cuestionario_activo_no_se_puede_iniciar(self):
        Questionnaire.objects.update(is_active=False)
        self.assertEqual(self.start().status_code, 404)