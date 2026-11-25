"""Pruebas del procesador de puntuaciones, los niveles y el resultado de la evaluación."""
from unittest import mock

from django.db import IntegrityError, transaction

from apps.evaluations.models import Evaluation, EvaluationResult, ResultDimensionScore
from apps.questionnaires.models import Question
from core import config
from core.functional import levels
from core.imperative.score_processor import compute_dimension_scores
from django.test import SimpleTestCase

from tests.test_evaluations import (
    INTERESTS,
    SKILLS,
    EvaluationTestCase,
    items_for,
    url,
)


def q(qid, links, lo=1, hi=5):
    return {"id": qid, "min_points": lo, "max_points": hi, "links": links}


class ProcessorTests(SimpleTestCase):
    DIMS = [("INT-A", "INTEREST"), ("HAB-B", "SKILL")]

    def run_one(self, questions, answers, dims=None):
        return compute_dimension_scores(dims or self.DIMS, questions, answers)

    def by_code(self, results):
        return {r["code"]: r for r in results}

    def test_all_max_gives_100(self):
        r = self.by_code(self.run_one([q(1, [("INT-A", 1)]), q(2, [("INT-A", 1)])], {1: 5, 2: 5}))
        self.assertEqual(r["INT-A"]["score"], 100.0)

    def test_all_min_gives_0_not_none(self):
        r = self.by_code(self.run_one([q(1, [("INT-A", 1)]), q(2, [("INT-A", 1)])], {1: 1, 2: 1}))
        self.assertEqual(r["INT-A"]["score"], 0.0)
        self.assertTrue(r["INT-A"]["valid"])

    def test_intermediate(self):
        r = self.by_code(self.run_one([q(1, [("INT-A", 1)])], {1: 3}))
        self.assertEqual(r["INT-A"]["score"], 50.0)

    def test_weights(self):
        qs = [q(1, [("INT-A", 3)]), q(2, [("INT-A", 1)])]
        r = self.by_code(self.run_one(qs, {1: 5, 2: 1}))
        self.assertEqual(r["INT-A"]["score"], 75.0)

    def test_scales_zero_to_one_and_zero_to_two(self):
        qs = [q(1, [("HAB-B", 1)], 0, 1), q(2, [("HAB-B", 1)], 0, 2)]
        r = self.by_code(self.run_one(qs, {1: 1, 2: 1}))
        self.assertEqual(r["HAB-B"]["score"], 75.0)

    def test_omitted_excluded_from_numerator_and_denominator(self):
        qs = [q(1, [("INT-A", 1)]), q(2, [("INT-A", 1)]), q(3, [("INT-A", 1)])]
        r = self.by_code(self.run_one(qs, {1: 5, 2: 5}))
        self.assertEqual(r["INT-A"]["score"], 100.0)
        self.assertEqual((r["INT-A"]["answered"], r["INT-A"]["total"]), (2, 3))
        self.assertEqual(r["INT-A"]["required"], 2)

    def test_too_few_answers_is_invalid_with_no_score(self):
        qs = [q(1, [("INT-A", 1)]), q(2, [("INT-A", 1)]), q(3, [("INT-A", 1)])]
        r = self.by_code(self.run_one(qs, {1: 5}))
        self.assertFalse(r["INT-A"]["valid"])
        self.assertIsNone(r["INT-A"]["score"])

    def test_no_answers_no_division_by_zero(self):
        r = self.by_code(self.run_one([q(1, [("INT-A", 1)])], {}))
        self.assertIsNone(r["INT-A"]["score"])

    def test_dimension_without_questions_is_invalid(self):
        r = self.by_code(self.run_one([q(1, [("INT-A", 1)])], {1: 5}))
        self.assertFalse(r["HAB-B"]["valid"])
        self.assertIsNone(r["HAB-B"]["score"])

    def test_question_feeds_several_dimensions(self):
        r = self.by_code(self.run_one([q(1, [("INT-A", 1), ("HAB-B", 2)])], {1: 5}))
        self.assertEqual(r["INT-A"]["score"], 100.0)
        self.assertEqual(r["HAB-B"]["score"], 100.0)

    def test_order_of_dimensions_preserved(self):
        r = self.run_one([q(1, [("INT-A", 1)])], {1: 5})
        self.assertEqual([x["code"] for x in r], ["INT-A", "HAB-B"])

    def test_points_out_of_range_raise(self):
        with self.assertRaises(ValueError):
            self.run_one([q(1, [("INT-A", 1)])], {1: 9})

    def test_invalid_range_weight_and_unknown_dimension_raise(self):
        with self.assertRaises(ValueError):
            self.run_one([q(1, [("INT-A", 1)], 3, 3)], {1: 3})
        with self.assertRaises(ValueError):
            self.run_one([q(1, [("INT-A", 0)])], {1: 3})
        with self.assertRaises(ValueError):
            self.run_one([q(1, [("XXX", 1)])], {1: 3})

    def test_does_not_mutate_inputs(self):
        qs = [q(1, [("INT-A", 1)])]
        answers = {1: 4}
        self.run_one(qs, answers)
        self.assertEqual(qs, [q(1, [("INT-A", 1)])])
        self.assertEqual(answers, {1: 4})


class LevelsTests(SimpleTestCase):
    def test_boundaries(self):
        self.assertEqual(levels.level_for(100), "HIGH")
        self.assertEqual(levels.level_for(config.LEVEL_HIGH), "HIGH")
        self.assertEqual(levels.level_for(config.LEVEL_HIGH - 0.01), "MEDIUM")
        self.assertEqual(levels.level_for(config.LEVEL_LOW), "MEDIUM")
        self.assertEqual(levels.level_for(config.LEVEL_LOW - 0.01), "LOW")
        self.assertEqual(levels.level_for(0), "LOW")
        self.assertIsNone(levels.level_for(None))

    def sample(self):
        return [
            {"code": "A", "kind": "INTEREST", "score": 90.0, "valid": True},
            {"code": "B", "kind": "INTEREST", "score": 90.0, "valid": True},
            {"code": "C", "kind": "SKILL", "score": 30.0, "valid": True},
            {"code": "D", "kind": "SKILL", "score": None, "valid": False},
        ]

    def test_with_levels_is_pure(self):
        data = self.sample()
        out = levels.with_levels(data)
        self.assertEqual([r["level"] for r in out], ["HIGH", "HIGH", "LOW", None])
        self.assertNotIn("level", data[0])

    def test_filters(self):
        data = self.sample()
        self.assertEqual(len(levels.valid_only(data)), 3)
        self.assertEqual([r["code"] for r in levels.of_kind(data, "SKILL")], ["C", "D"])

    def test_strongest_ties_broken_by_code(self):
        self.assertEqual([r["code"] for r in levels.strongest(self.sample(), 2)], ["A", "B"])
        self.assertEqual(levels.strongest(self.sample(), 5, minimum=50)[-1]["code"], "B")

    def test_average(self):
        self.assertEqual(levels.average_score(self.sample()), 70.0)
        self.assertIsNone(levels.average_score([]))


class ResultIntegrationTests(EvaluationTestCase):
    def complete(self):
        pk = self.start().json()["id"]
        self.assertEqual(self.put(pk, items_for(INTERESTS + SKILLS)).status_code, 200)
        return pk

    def test_submit_stores_result_with_all_dimensions(self):
        pk = self.complete()
        response = self.submit(pk)
        self.assertEqual(response.status_code, 200)
        result = EvaluationResult.objects.get(evaluation_id=pk)
        self.assertEqual(result.scoring_version, config.SCORING_VERSION)
        self.assertEqual(result.config["level_high"], config.LEVEL_HIGH)
        self.assertEqual(result.scores.count(), 14)
        self.assertEqual(result.scores.filter(is_valid=True).count(), 14)
        body = response.json()["result"]
        self.assertEqual(len(body["interests"]), 7)
        self.assertEqual(len(body["skills"]), 7)
        self.assertIn("orientativos", body["notice"])

    def test_first_option_scores_are_consistent(self):
        pk = self.complete()
        self.submit(pk)
        for score in ResultDimensionScore.objects.filter(result__evaluation_id=pk):
            self.assertTrue(0 <= score.score <= 100)
            self.assertEqual(score.level, levels.level_for(float(score.score)))

    def test_result_endpoint(self):
        pk = self.complete()
        self.submit(pk)
        response = self.client.get(url(pk, "result/"), **self.headers(self.ana))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scoring_version"], config.SCORING_VERSION)

    def test_result_of_draft_is_409(self):
        pk = self.start().json()["id"]
        response = self.client.get(url(pk, "result/"), **self.headers(self.ana))
        self.assertEqual(response.status_code, 409)

    def test_result_of_other_user_is_404(self):
        pk = self.complete()
        self.submit(pk)
        response = self.client.get(url(pk, "result/"), **self.headers(self.luis))
        self.assertEqual(response.status_code, 404)

    def test_result_requires_login(self):
        pk = self.complete()
        self.submit(pk)
        self.assertEqual(self.client.get(url(pk, "result/")).status_code, 401)

    def test_draft_detail_has_no_result(self):
        pk = self.start().json()["id"]
        self.assertIsNone(self.client.get(url(pk), **self.headers(self.ana)).json()["result"])

    def test_scoring_failure_rolls_back_submit(self):
        pk = self.complete()
        with mock.patch("apps.evaluations.scoring.store_result", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.submit(pk)
        evaluation = Evaluation.objects.get(pk=pk)
        self.assertEqual(evaluation.status, Evaluation.Status.DRAFT)
        self.assertIsNone(evaluation.submitted_at)
        self.assertFalse(EvaluationResult.objects.filter(evaluation=evaluation).exists())

    def test_result_does_not_leak_question_internals(self):
        pk = self.complete()
        text = self.submit(pk).content.decode().lower()
        for word in ("justification", "bias_notes", "criterion", "points"):
            self.assertNotIn(word, text)

    def test_invalid_dimension_stored_without_score(self):
        pk = self.start().json()["id"]
        self.put(pk, items_for(INTERESTS + SKILLS[:-1]))
        self.submit(pk)
        score = ResultDimensionScore.objects.get(result__evaluation_id=pk, dimension__code="HAB-TEC")
        self.assertFalse(score.is_valid)
        self.assertIsNone(score.score)
        self.assertIsNone(score.level)

    def test_db_rejects_inconsistent_score_rows(self):
        pk = self.complete()
        self.submit(pk)
        row = ResultDimensionScore.objects.filter(result__evaluation_id=pk).first()
        row.score = 150
        with self.assertRaises(IntegrityError), transaction.atomic():
            row.save()