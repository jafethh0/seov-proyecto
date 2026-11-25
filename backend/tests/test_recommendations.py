"""Pruebas de afinidad, dominio, recomendador, carga de carreras y recomendaciones por API."""
import json
from datetime import date
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from apps.catalog.models import (
    Campus,
    CareerDimension,
    CareerProgram,
    Department,
    Institution,
    ProgramOffering,
)
from apps.evaluations.models import CareerRecommendation, Evaluation, EvaluationResult
from apps.questionnaires.models import Dimension
from core import config
from core.domain.areas import AREA_WEIGHTS
from core.domain.career import Career, StudentProfile
from core.functional import affinity
from core.imperative.recommender import rank_areas, recommend
from tests.test_evaluations import INTERESTS, SKILLS, EvaluationTestCase, items_for, url


class AffinityTests(SimpleTestCase):
    def test_weighted_average(self):
        self.assertEqual(affinity.weighted_average([(3, 100), (1, 0)]), 75)
        self.assertIsNone(affinity.weighted_average([]))

    def test_documented_example(self):
        weights = {"INT-TEC": 3, "INT-CIE": 1, "HAB-LOG": 3, "HAB-NUM": 2, "HAB-TEC": 1}
        scores = {"INT-TEC": 85, "INT-CIE": 60, "HAB-LOG": 100, "HAB-NUM": 66.7, "HAB-TEC": 66.7}
        interest = affinity.section_affinity(weights, scores, "INTEREST")
        skill = affinity.section_affinity(weights, scores, "SKILL")
        self.assertAlmostEqual(interest, 78.75)
        self.assertAlmostEqual(skill, 83.35)
        index, case = affinity.compat_index(interest, skill)
        self.assertEqual((index, case), (80.59, "A"))

    def test_missing_dimensions_are_ignored_not_zero(self):
        weights = {"INT-TEC": 3, "INT-CIE": 1}
        self.assertEqual(affinity.section_affinity(weights, {"INT-TEC": 80}, "INTEREST"), 80)

    def test_cases_b_c_d(self):
        self.assertEqual(affinity.compat_index(80, None), (80, "B"))
        self.assertEqual(affinity.compat_index(None, 60), (60, "C"))
        self.assertEqual(affinity.compat_index(None, None), (None, "D"))

    def test_zero_is_a_real_value(self):
        self.assertEqual(affinity.compat_index(0, 0), (0, "A"))

    def test_levels(self):
        self.assertEqual(affinity.affinity_level(70), "HIGH")
        self.assertEqual(affinity.affinity_level(69.99), "MEDIUM")
        self.assertEqual(affinity.affinity_level(50), "MEDIUM")
        self.assertEqual(affinity.affinity_level(49.99), "EXPLORATORY")
        self.assertIsNone(affinity.affinity_level(None))

    def test_rank_ties_by_name(self):
        rows = [{"name": "B", "v": 5}, {"name": "A", "v": 5}, {"name": "C", "v": 9}]
        self.assertEqual([r["name"] for r in affinity.rank(rows, key=lambda r: r["v"])], ["C", "A", "B"])


def profile_of(**scores):
    levels = {c: ("HIGH" if v >= 70 else "MEDIUM" if v >= 40 else "LOW") for c, v in scores.items()}
    return StudentProfile({k.replace("_", "-"): v for k, v in scores.items()},
                          {k.replace("_", "-"): v for k, v in levels.items()})


class DomainTests(SimpleTestCase):
    def test_profile_drops_invalid(self):
        items = [
            {"code": "INT-TEC", "score": 80.0, "valid": True, "level": "HIGH"},
            {"code": "HAB-LOG", "score": None, "valid": False, "level": None},
        ]
        self.assertEqual(StudentProfile.from_scores(items).scores, {"INT-TEC": 80.0})

    def test_career_compatibility_and_reinforce(self):
        career = Career(1, "X", "UNIVERSITY", "Tecnología e Informática",
                        {"INT-TEC": 3, "HAB-LOG": 3, "HAB-NUM": 2})
        profile = profile_of(**{"INT_TEC": 90, "HAB_LOG": 20, "HAB_NUM": 80})
        index, case, interest, skill = career.compatibility(profile)
        self.assertEqual(case, "A")
        self.assertEqual(interest, 90)
        self.assertEqual(skill, (3 * 20 + 2 * 80) / 5)
        self.assertEqual(career.to_reinforce(profile), ["HAB-LOG"])
        self.assertIsNotNone(index)  # una habilidad baja no excluye la carrera

    def test_strengths_sorted_and_limited(self):
        career = Career(1, "X", "UNIVERSITY", "A", {"INT-TEC": 3, "HAB-LOG": 3, "HAB-NUM": 2, "INT-CIE": 1})
        profile = profile_of(**{"INT_TEC": 90, "HAB_LOG": 60, "HAB_NUM": 80, "INT_CIE": 30})
        self.assertEqual([s["code"] for s in career.strengths(profile)], ["INT-TEC", "HAB-LOG", "HAB-NUM"])

    def test_career_is_immutable(self):
        career = Career(1, "X", "UNIVERSITY", "A", {})
        with self.assertRaises(Exception):
            career.name = "Y"


class RecommenderTests(SimpleTestCase):
    def careers(self):
        return [
            Career(1, "Sistemas", "UNIVERSITY", "Tecnología e Informática", AREA_WEIGHTS["Tecnología e Informática"]),
            Career(2, "Derecho", "UNIVERSITY", "Ciencias Sociales y Jurídicas", AREA_WEIGHTS["Ciencias Sociales y Jurídicas"]),
            Career(3, "Electricidad", "TECHNICAL", "Oficios y Técnicos Industriales", AREA_WEIGHTS["Oficios y Técnicos Industriales"]),
            Career(4, "Turismo", "UNIVERSITY", "Turismo, Hotelería y Servicios", AREA_WEIGHTS["Turismo, Hotelería y Servicios"]),
        ]

    def tech_profile(self):
        return profile_of(**{"INT_TEC": 90, "INT_CIE": 60, "HAB_LOG": 100, "HAB_NUM": 70, "HAB_TEC": 70,
                             "INT_SOC": 20, "HAB_SOC": 30})

    def test_rule_area_marked_and_ranked_first(self):
        result = recommend(self.tech_profile(), self.careers(),
                           {"Tecnología e Informática": ["A1"]}, ["UNIVERSITY"], fallback=0)
        self.assertEqual([r["name"] for r in result], ["Sistemas"])
        self.assertEqual(result[0]["origin"], "RULE")
        self.assertEqual(result[0]["rules"], ["A1"])
        self.assertTrue(result[0]["type_highlighted"])

    def test_fallback_by_affinity_when_no_rules(self):
        result = recommend(self.tech_profile(), self.careers(), {}, [], fallback=2)
        self.assertTrue(result)
        self.assertTrue(all(r["origin"] == "AFFINITY" for r in result))

    def test_sorted_by_compat_descending(self):
        result = recommend(self.tech_profile(), self.careers(), {}, [], fallback=11, limit=10)
        compats = [r["compat"] for r in result]
        self.assertEqual(compats, sorted(compats, reverse=True))
        self.assertEqual(result[0]["name"], "Sistemas")

    def test_limit(self):
        self.assertEqual(len(recommend(self.tech_profile(), self.careers(), {}, [], fallback=11, limit=2)), 2)

    def test_no_data_gives_no_recommendations(self):
        empty = StudentProfile({}, {})
        self.assertEqual(recommend(empty, self.careers(), {}, []), [])
        self.assertEqual(rank_areas(empty), [])

    def test_low_skill_does_not_exclude(self):
        low = profile_of(**{"INT_TEC": 90, "HAB_LOG": 10})
        names = [r["name"] for r in recommend(low, self.careers(), {"Tecnología e Informática": ["A1"]}, [])]
        self.assertIn("Sistemas", names)

    def test_type_not_highlighted_when_not_suggested(self):
        result = recommend(self.tech_profile(), self.careers(), {"Tecnología e Informática": ["A1"]}, ["TECHNICAL"], fallback=0)
        self.assertFalse(result[0]["type_highlighted"])


class SeedCareersTests(TestCase):
    def setUp(self):
        call_command("seed_questionnaire", stdout=StringIO())

    def test_requires_questionnaire_dimensions(self):

        call_command("seed_careers", stdout=StringIO())
        self.assertEqual(CareerProgram.objects.count(), 40)

    def test_idempotent(self):
        call_command("seed_careers", stdout=StringIO())
        weights = CareerDimension.objects.count()
        call_command("seed_careers", stdout=StringIO())
        self.assertEqual(CareerProgram.objects.count(), 40)
        self.assertEqual(CareerDimension.objects.count(), weights)

    def test_areas_and_weights(self):
        call_command("seed_careers", stdout=StringIO())
        from apps.catalog.models import CareerCategory
        self.assertEqual(CareerCategory.objects.count(), 11)
        sistemas = CareerProgram.objects.get(name="Ingeniería en Sistemas")
        weights = {w.dimension.code: w.weight for w in sistemas.dimension_weights.all()}
        self.assertEqual(weights["INT-TEC"], 3)
        self.assertEqual(weights["HAB-NUM"], 3)  # override
        soporte = CareerProgram.objects.get(name="Técnico en Soporte Informático")
        self.assertNotIn("HAB-NUM", {w.dimension.code for w in soporte.dimension_weights.all()})

    def test_every_program_has_both_sections_and_valid_weights(self):
        call_command("seed_careers", stdout=StringIO())
        for program in CareerProgram.objects.all():
            kinds = {w.dimension.kind for w in program.dimension_weights.all()}
            self.assertEqual(kinds, {"INTEREST", "SKILL"}, program.name)
            for w in program.dimension_weights.all():
                self.assertTrue(1 <= w.weight <= 3)

    def test_weight_constraints(self):
        call_command("seed_careers", stdout=StringIO())
        program = CareerProgram.objects.first()
        row = program.dimension_weights.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            CareerDimension.objects.create(program=program, dimension=row.dimension, weight=2)
        free = Dimension.objects.exclude(pk__in=program.dimension_weights.values("dimension")).first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            CareerDimension.objects.create(program=program, dimension=free, weight=4)

    def test_no_institutions_or_offerings_created(self):
        call_command("seed_careers", stdout=StringIO())
        self.assertEqual(Institution.objects.count(), 0)
        self.assertEqual(ProgramOffering.objects.count(), 0)


class RecommendationApiTests(EvaluationTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("seed_departments", stdout=StringIO())
        call_command("seed_careers", stdout=StringIO())

    def submitted(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(INTERESTS + SKILLS))
        self.assertEqual(self.submit(pk).status_code, 200)
        return pk

    def get(self, pk, query="", user=None):
        return self.client.get(url(pk, "recommendations/") + query, **self.headers(user or self.ana))

    def make_offering(self, program, dept_slug, modality="IN_PERSON", **extra):
        institution, _ = Institution.objects.get_or_create(name="Institución de prueba", defaults={"sector": "PUBLIC"})
        campus, _ = Campus.objects.get_or_create(
            institution=institution, name=f"Sede {dept_slug}",
            defaults={"department": Department.objects.get(slug=dept_slug)},
        )
        return ProgramOffering.objects.create(
            program=program, campus=campus, official_name=program.name, modality=modality,
            source_url="https://example.org/fuente", verified_at=date(2026, 11, 1), is_active=True, **extra,
        )

    def test_recommendations_stored_ordered_and_limited(self):
        pk = self.submitted()
        rows = list(CareerRecommendation.objects.filter(result__evaluation_id=pk))
        self.assertTrue(0 < len(rows) <= config.RESULT_LIMIT)
        self.assertEqual([r.rank for r in rows], list(range(1, len(rows) + 1)))
        compats = [r.compat for r in rows]
        self.assertEqual(compats, sorted(compats, reverse=True))

    def test_catalog_version_in_config(self):
        pk = self.submitted()
        version = EvaluationResult.objects.get(evaluation_id=pk).config["catalog_version"]
        self.assertTrue(version.startswith("40@"))

    def test_api_all_departments(self):
        pk = self.submitted()
        response = self.get(pk, "?department=all")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["department"])
        self.assertEqual(body["also_interesting"], [])
        self.assertTrue(body["recommendations"])
        self.assertIn("probabilidad", body["notice"])
        first = body["recommendations"][0]
        for key in ("rank", "program", "compat", "level", "origin", "why", "offerings"):
            self.assertIn(key, first)

    def test_department_split_between_main_and_also_interesting(self):
        pk = self.submitted()
        top = CareerRecommendation.objects.filter(result__evaluation_id=pk).first().program
        self.make_offering(top, "francisco-morazan")
        body = self.get(pk, "?department=francisco-morazan").json()
        self.assertEqual([i["program"]["id"] for i in body["recommendations"]], [top.id])
        self.assertEqual(body["recommendations"][0]["offerings"][0]["department"], "Francisco Morazán")
        self.assertTrue(body["also_interesting"])
        other = self.get(pk, "?department=cortes").json()
        self.assertEqual(other["recommendations"], [])

    def test_online_offer_shown_in_any_department_unless_excluded(self):
        pk = self.submitted()
        top = CareerRecommendation.objects.filter(result__evaluation_id=pk).first().program
        self.make_offering(top, "francisco-morazan", modality="ONLINE")
        self.assertEqual(len(self.get(pk, "?department=cortes").json()["recommendations"]), 1)
        self.assertEqual(self.get(pk, "?department=cortes&include_online=false").json()["recommendations"], [])

    def test_outdated_or_unverified_offer_not_shown(self):
        pk = self.submitted()
        top = CareerRecommendation.objects.filter(result__evaluation_id=pk).first().program
        offering = self.make_offering(top, "cortes")
        offering.verification_status = ProgramOffering.VerificationStatus.OUTDATED
        offering.save()
        self.assertEqual(self.get(pk, "?department=cortes").json()["recommendations"], [])

    def test_default_department_is_profile_preference(self):
        pk = self.submitted()
        top = CareerRecommendation.objects.filter(result__evaluation_id=pk).first().program
        self.make_offering(top, "cortes")
        from apps.accounts.models import StudentProfile as Profile
        Profile.objects.update_or_create(
            user=self.ana,
            defaults={"education_level": "HIGH_SCHOOL", "preferred_department": Department.objects.get(slug="cortes")},
        )
        body = self.get(pk).json()
        self.assertEqual(body["department"]["slug"], "cortes")
        self.assertEqual(len(body["recommendations"]), 1)

    def test_unknown_department_404(self):
        pk = self.submitted()
        self.assertEqual(self.get(pk, "?department=narnia").status_code, 404)

    def test_draft_409_other_user_404_anonymous_401(self):
        draft = self.start().json()["id"]
        self.assertEqual(self.get(draft).status_code, 409)
        pk = self.submitted_other()
        self.assertEqual(self.get(pk, user=self.luis).status_code, 404)
        self.assertEqual(self.client.get(url(pk, "recommendations/")).status_code, 401)

    def submitted_other(self):
        # ana ya tiene un borrador: se envía y se consulta con luis
        pk = Evaluation.objects.filter(user=self.ana).first().id
        self.put(pk, items_for(INTERESTS + SKILLS))
        self.assertEqual(self.submit(pk).status_code, 200)
        return pk

    def test_no_internals_exposed(self):
        pk = self.submitted()
        text = self.get(pk, "?department=all").content.decode().lower()
        for word in ("justification", "bias_notes", "criterion"):
            self.assertNotIn(word, text)

    def test_recommendation_failure_rolls_back_submit(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(INTERESTS + SKILLS))
        with mock.patch("apps.evaluations.recommendations.store_recommendations", side_effect=RuntimeError("x")):
            with self.assertRaises(RuntimeError):
                self.submit(pk)
        self.assertEqual(Evaluation.objects.get(pk=pk).status, Evaluation.Status.DRAFT)
        self.assertFalse(EvaluationResult.objects.filter(evaluation_id=pk).exists())

    def test_submit_works_with_empty_catalog(self):
        CareerProgram.objects.all().delete()
        pk = self.submitted()
        body = self.get(pk, "?department=all").json()
        self.assertEqual(body["recommendations"], [])

    def test_stored_history_survives_catalog_changes(self):
        pk = self.submitted()
        before = [r.program_id for r in CareerRecommendation.objects.filter(result__evaluation_id=pk)]
        CareerDimension.objects.all().update(weight=1)
        after = [r.program_id for r in CareerRecommendation.objects.filter(result__evaluation_id=pk)]
        self.assertEqual(before, after)