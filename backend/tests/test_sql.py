"""Pruebas de la capa SQL declarativa: vistas, consultas, paridad con Python y analítica."""
from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from apps.analytics import sqlqueries
from apps.catalog.models import Campus, CareerProgram, Department, Institution, ProgramOffering
from apps.evaluations.models import (
    CareerRecommendation,
    Evaluation,
    EvaluationResult,
    ResultDimensionScore,
)
from apps.questionnaires.models import Dimension, Questionnaire
from core import config
from core.domain.career import StudentProfile
from core.functional import levels
from apps.evaluations import recommendations as recs
from tests.test_evaluations import INTERESTS, SKILLS, EvaluationTestCase, items_for

User = get_user_model()


def make_result(user, scores):
    """Crea una evaluación enviada con puntuaciones {código: score o None (inválida)}."""
    questionnaire = Questionnaire.objects.get(is_active=True)
    evaluation = Evaluation.objects.create(
        user=user, questionnaire=questionnaire,
        status=Evaluation.Status.SUBMITTED, submitted_at=timezone.now(),
    )
    result = EvaluationResult.objects.create(evaluation=evaluation, scoring_version="t", config={})
    for dim in Dimension.objects.all():
        score = scores.get(dim.code)
        ResultDimensionScore.objects.create(
            result=result, dimension=dim, score=score,
            level=None if score is None else levels.level_for(score),
            answered=3, total=3, required=2, is_valid=score is not None,
        )
    return result


def sql_compat(result, w_i=config.WEIGHT_INTERESTS, w_s=config.WEIGHT_SKILLS):
    rows = sqlqueries.fetch_all(
        "compatibility", {"result_id": result.id, "w_interest": w_i, "w_skill": w_s}
    )
    return {r["program_id"]: r for r in rows}


class SqlBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_questionnaire", stdout=StringIO())
        call_command("seed_departments", stdout=StringIO())
        call_command("seed_careers", stdout=StringIO())
        cls.user = User.objects.create_user("sql@example.com", "sql@example.com", "ClaveSegura#2026")

    def offering(self, program_name="Ingeniería en Sistemas", dept="francisco-morazan", **extra):
        inst, _ = Institution.objects.get_or_create(name="Inst SQL", defaults={"sector": "PUBLIC"})
        campus, _ = Campus.objects.get_or_create(
            institution=inst, name=f"Sede {dept}",
            defaults={"department": Department.objects.get(slug=dept)},
        )
        values = dict(
            official_name=program_name, modality="IN_PERSON", source_url="https://example.org/f",
            verified_at=date(2026, 11, 1), is_active=True,
        )
        values.update(extra)
        return ProgramOffering.objects.create(
            program=CareerProgram.objects.get(name=program_name), campus=campus, **values
        )


class ViewsTests(SqlBase):
    def test_all_views_exist_and_are_queryable(self):
        for name in sqlqueries.VIEWS:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {name} LIMIT 1")

    def test_create_views_is_idempotent(self):
        self.assertTrue(sqlqueries.create_views())
        self.assertTrue(sqlqueries.create_views())

    def test_available_offerings_view_matches_orm(self):
        good = self.offering()
        self.offering("Medicina", is_active=False)
        self.offering("Derecho", verification_status="OUTDATED")
        inactive_campus = self.offering("Economía", dept="cortes")
        Campus.objects.filter(pk=inactive_campus.campus_id).update(is_active=False)
        self.offering("Pedagogía", dept="atlantida")
        Institution.objects.filter(name="Inst SQL").update(is_active=True)
        CareerProgram.objects.filter(name="Pedagogía").update(is_active=False)
        self.offering("Biología", dept="olancho")
        via_sql = {r["offering_id"] for r in sqlqueries.fetch_all("offerings_all")}
        via_orm = set(ProgramOffering.objects.available().values_list("id", flat=True))
        self.assertEqual(via_sql, via_orm)
        self.assertIn(good.id, via_sql)
        self.assertEqual(len(via_sql), 2)  # Sistemas y Biología

    def test_inactive_institution_excluded(self):
        offer = self.offering()
        Institution.objects.update(is_active=False)
        self.assertNotIn(offer.id, {r["offering_id"] for r in sqlqueries.fetch_all("offerings_all")})
        self.assertFalse(ProgramOffering.objects.available().exists())

    def test_department_queries(self):
        presential = self.offering(dept="francisco-morazan")
        online = self.offering("Derecho", dept="cortes", modality="ONLINE")
        fm = Department.objects.get(slug="francisco-morazan").id
        only = {r["offering_id"] for r in sqlqueries.fetch_all("offerings_in_department", {"department_id": fm})}
        both = {r["offering_id"] for r in sqlqueries.fetch_all("offerings_in_department_or_online", {"department_id": fm})}
        self.assertEqual(only, {presential.id})
        self.assertEqual(both, {presential.id, online.id})

    def test_result_scores_view(self):
        result = make_result(self.user, {"INT-TEC": 80.0, "HAB-LOG": None})
        rows = [r for r in sqlqueries.fetch_all("dimension_summary")]
        self.assertEqual(len(rows), 14)
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT is_valid, score FROM v_result_scores WHERE result_id=%s AND dimension_code='HAB-LOG'", [result.id])
            valid, score = cursor.fetchone()
        self.assertFalse(valid)
        self.assertIsNone(score)

    def test_no_personal_data_in_views(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM v_result_scores LIMIT 1")
            columns = {c[0] for c in cursor.description}
        self.assertFalse({"user_id", "email", "username"} & columns)


class ParityTests(SqlBase):
    """El mismo cálculo en SQL (declarativo) y en Python (OO/funcional/imperativo)."""

    def python_compat(self, result, program_id):
        careers = {c.id: c for c in recs.load_careers()}
        profile = StudentProfile.from_scores(
            [{"code": s.dimension.code, "score": None if s.score is None else float(s.score),
              "valid": s.is_valid, "level": s.level} for s in result.scores.select_related("dimension")]
        )
        return careers[program_id].compatibility(profile)

    def assert_parity(self, result):
        sql = sql_compat(result)
        for program in CareerProgram.objects.all():
            index, case, interest, skill = self.python_compat(result, program.id)
            row = sql.get(program.id)
            if index is None:
                self.assertIsNone(row, program.name)
                continue
            self.assertIsNotNone(row, program.name)
            self.assertAlmostEqual(row["compat"], index, delta=0.011, msg=program.name)
            self.assertEqual(row["case_code"], case, program.name)

    def test_full_profile(self):
        scores = {c: float(v) for c, v in zip(INTERESTS + SKILLS, [85, 60, 20, 45, 10, 75, 55, 100, 66.7, 30, 90, 100, 0, 52.5])}
        self.assert_parity(make_result(self.user, scores))

    def test_all_hundred_avoids_integer_division(self):
        self.assert_parity(make_result(self.user, {c: 100.0 for c in INTERESTS + SKILLS}))

    def test_all_zero_is_a_real_value(self):
        result = make_result(self.user, {c: 0.0 for c in INTERESTS + SKILLS})
        self.assert_parity(result)
        self.assertTrue(all(r["compat"] == 0 for r in sql_compat(result).values()))

    def test_only_interests_case_b(self):
        scores = {c: 70.0 for c in INTERESTS}
        result = make_result(self.user, scores)
        self.assert_parity(result)
        self.assertEqual({r["case_code"] for r in sql_compat(result).values()}, {"B"})

    def test_only_skills_case_c(self):
        result = make_result(self.user, {c: 55.0 for c in SKILLS})
        self.assert_parity(result)
        self.assertEqual({r["case_code"] for r in sql_compat(result).values()}, {"C"})

    def test_no_valid_dimensions_case_d_returns_nothing(self):
        result = make_result(self.user, {})
        self.assertEqual(sql_compat(result), {})
        self.assert_parity(result)

    def test_sql_ranking_orders_by_compat_then_name(self):
        result = make_result(self.user, {c: float(i * 7 % 100) for i, c in enumerate(INTERESTS + SKILLS)})
        rows = sqlqueries.fetch_all(
            "compatibility", {"result_id": result.id, "w_interest": config.WEIGHT_INTERESTS, "w_skill": config.WEIGHT_SKILLS}
        )
        keys = [(-r["compat"], r["name"]) for r in rows]
        self.assertEqual(keys, sorted(keys))

    def test_stored_recommendations_match_sql_values(self):
        # Evaluación real enviada por la API y comparación con SQL
        from django.test import Client
        client = Client()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(self.user)}"}
        pk = client.post("/api/v1/evaluations/", **headers).json()["id"]
        import json
        client.put(f"/api/v1/evaluations/{pk}/answers/", json.dumps({"answers": items_for(INTERESTS + SKILLS)}),
                   content_type="application/json", **headers)
        self.assertEqual(client.post(f"/api/v1/evaluations/{pk}/submit/", **headers).status_code, 200)
        result = EvaluationResult.objects.get(evaluation_id=pk)
        sql = sql_compat(result)
        stored = list(CareerRecommendation.objects.filter(result=result))
        self.assertTrue(stored)
        for rec in stored:
            self.assertAlmostEqual(float(rec.compat), sql[rec.program_id]["compat"], delta=0.011)


class AnalyticsTests(SqlBase):
    def client_for(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}

    def test_requires_staff(self):
        url = "/api/v1/analytics/summary/"
        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.get(url, **self.client_for(self.user)).status_code, 403)

    def test_summary_content(self):
        staff = User.objects.create_user("staff@example.com", "staff@example.com", "ClaveSegura#2026", is_staff=True)
        make_result(self.user, {c: 80.0 for c in INTERESTS + SKILLS})
        self.offering()
        response = self.client.get("/api/v1/analytics/summary/", **self.client_for(staff))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["overview"]["submitted_evaluations"], 1)
        self.assertEqual(body["overview"]["students_with_results"], 1)
        self.assertEqual(body["overview"]["active_careers"], 40)
        self.assertEqual(body["overview"]["available_offerings"], 1)
        self.assertEqual(len(body["dimensions"]), 14)
        self.assertEqual(body["dimensions"][0]["high_count"], 1)
        self.assertEqual(len(body["coverage_by_department"]), 18)
        fm = [d for d in body["coverage_by_department"] if d["slug"] == "francisco-morazan"][0]
        self.assertEqual((fm["offerings"], fm["programs"]), (1, 1))
        text = response.content.decode().lower()
        self.assertNotIn("email", text)
        self.assertNotIn("sql@example.com", text)

    def test_top_careers_counts(self):
        staff = User.objects.create_user("staff@example.com", "staff@example.com", "ClaveSegura#2026", is_staff=True)
        result = make_result(self.user, {c: 80.0 for c in INTERESTS + SKILLS})
        programs = list(CareerProgram.objects.all()[:4])
        for rank, program in enumerate(programs, start=1):
            CareerRecommendation.objects.create(
                result=result, program=program, rank=rank, compat=90 - rank, origin="RULE"
            )
        top = sqlqueries.fetch_all("top_careers", {"limit": 2})
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["times_top3"], 1)
        body = self.client.get("/api/v1/analytics/summary/", **self.client_for(staff)).json()
        self.assertEqual(len(body["top_careers"]), 4)

    def test_empty_database_summary(self):
        staff = User.objects.create_user("staff@example.com", "staff@example.com", "ClaveSegura#2026", is_staff=True)
        body = self.client.get("/api/v1/analytics/summary/", **self.client_for(staff)).json()
        self.assertEqual(body["overview"]["submitted_evaluations"], 0)
        self.assertEqual(body["dimensions"], [])
        self.assertEqual(body["top_careers"], [])