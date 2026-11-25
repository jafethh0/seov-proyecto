"""Pruebas del motor lógico: hechos, reglas, encadenamiento hacia adelante y explicación."""
from django.test import SimpleTestCase

from apps.evaluations.models import ResultInference
from core.logic import explain
from core.logic.engine import Firing, forward_chain
from core.logic.facts import (
    area,
    facts_from_scores,
    format_fact,
    interest_high,
    profile,
    program_type,
    skill_high,
)
from core.logic.rules import AREAS, RULES, RULESET_VERSION, Rule
from tests.test_evaluations import INTERESTS, SKILLS, EvaluationTestCase, url


def rule(id, conditions, conclusion, active=True, priority=0, layer=1):
    return Rule(id, layer, id, tuple(conditions), conclusion, f"texto {id}", priority, active)


A, B, C, D = ("a",), ("b",), ("c",), ("d",)


class EngineTests(SimpleTestCase):
    def test_single_rule(self):
        result = forward_chain({A}, [rule("R1", [A], B)])
        self.assertIn(B, result.facts)
        self.assertEqual(result.trace[0].rule_id, "R1")

    def test_chain_of_layers(self):
        result = forward_chain({A}, [rule("R2", [B], C), rule("R1", [A], B)])
        self.assertIn(C, result.facts)
        self.assertEqual([(f.rule_id, f.iteration) for f in result.trace], [("R1", 1), ("R2", 2)])

    def test_all_conditions_needed(self):
        self.assertNotIn(C, forward_chain({A}, [rule("R1", [A, B], C)]).facts)
        self.assertIn(C, forward_chain({A, B}, [rule("R1", [A, B], C)]).facts)

    def test_no_facts_no_firings(self):
        result = forward_chain(set(), RULES)
        self.assertEqual(result.trace, ())
        self.assertEqual(result.facts, frozenset())

    def test_rule_fires_only_once(self):
        result = forward_chain({A}, [rule("R1", [A], B)])
        self.assertEqual(len(result.trace), 1)

    def test_cycle_terminates(self):
        rules = [rule("R1", [A], B), rule("R2", [B], A)]
        result = forward_chain({A}, rules)
        self.assertEqual({f.rule_id for f in result.trace}, {"R1", "R2"})

    def test_two_rules_same_conclusion_both_recorded(self):
        result = forward_chain({A, B}, [rule("R1", [A], C), rule("R2", [B], C)])
        self.assertEqual([f.new_fact for f in result.trace], [True, False])
        self.assertEqual(explain.rules_supporting(result, C), ["R1", "R2"])

    def test_inactive_rule_ignored(self):
        self.assertNotIn(B, forward_chain({A}, [rule("R1", [A], B, active=False)]).facts)

    def test_priority_orders_firings(self):
        rules = [rule("R1", [A], B, priority=2), rule("R2", [A], C, priority=1)]
        self.assertEqual([f.rule_id for f in forward_chain({A}, rules).trace], ["R2", "R1"])

    def test_iteration_limit(self):
        rules = [rule("R1", [A], B), rule("R2", [B], C), rule("R3", [C], D)]
        result = forward_chain({A}, rules, max_iterations=2)
        self.assertNotIn(D, result.facts)

    def test_does_not_mutate_inputs_and_is_deterministic(self):
        facts = {A}
        rules = [rule("R1", [A], B)]
        first = forward_chain(facts, rules)
        self.assertEqual(facts, {A})
        self.assertEqual(first, forward_chain(facts, rules))
        self.assertIsInstance(first.trace[0], Firing)


class FactsTests(SimpleTestCase):
    def scores(self):
        return [
            {"code": "INT-TEC", "kind": "INTEREST", "score": 85.0, "valid": True, "level": "HIGH"},
            {"code": "INT-ART", "kind": "INTEREST", "score": 55.0, "valid": True, "level": "MEDIUM"},
            {"code": "INT-SOC", "kind": "INTEREST", "score": 10.0, "valid": True, "level": "LOW"},
            {"code": "HAB-LOG", "kind": "SKILL", "score": 100.0, "valid": True, "level": "HIGH"},
            {"code": "HAB-NUM", "kind": "SKILL", "score": 45.0, "valid": True, "level": "MEDIUM"},
            {"code": "HAB-VER", "kind": "SKILL", "score": 20.0, "valid": True, "level": "LOW"},
            {"code": "HAB-CRE", "kind": "SKILL", "score": None, "valid": False, "level": None},
        ]

    def test_level_facts(self):
        facts = facts_from_scores(self.scores())
        for expected in [
            ("interes_alto", "INT-TEC"), ("interes_medio", "INT-ART"), ("interes_bajo", "INT-SOC"),
            ("habilidad_alta", "HAB-LOG"), ("habilidad_media", "HAB-NUM"), ("habilidad_baja", "HAB-VER"),
        ]:
            self.assertIn(expected, facts)

    def test_invalid_dimension_generates_no_fact(self):
        facts = facts_from_scores(self.scores())
        self.assertFalse([f for f in facts if len(f) > 1 and f[1] == "HAB-CRE"])

    def test_dominant_interests_need_minimum_and_limit_two(self):
        facts = facts_from_scores(self.scores())
        dominant = {f[1] for f in facts if f[0] == "interes_dominante"}
        self.assertEqual(dominant, {"INT-TEC", "INT-ART"})  # INT-SOC (10) no llega a 50

    def test_format(self):
        self.assertEqual(format_fact(("habilidad_alta", "HAB-LOG")), "habilidad_alta(HAB-LOG)")
        self.assertEqual(format_fact(("perfil_analitico",)), "perfil_analitico")


class RulesetTests(SimpleTestCase):
    def test_ids_unique_and_counts(self):
        ids = [r.id for r in RULES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([sum(1 for r in RULES if r.layer == n) for n in (1, 2, 3)], [8, 12, 2])

    def test_area_conclusions_use_known_areas(self):
        for r in RULES:
            if r.conclusion[0] == "area":
                self.assertIn(r.conclusion[1], AREAS)
        self.assertEqual(len(AREAS), 11)

    def test_every_rule_has_explanation_and_is_active(self):
        for r in RULES:
            self.assertTrue(r.explanation)
            self.assertTrue(r.active)

    def test_dimension_codes_in_rules_exist(self):
        known = set(INTERESTS + SKILLS)
        for r in RULES:
            for fact in r.conditions:
                if len(fact) > 1 and fact[0] != "area":
                    self.assertIn(fact[1], known)

    def run_rules(self, *facts):
        return forward_chain(set(facts), RULES).facts

    def test_each_profile_rule(self):
        cases = {
            "analitico": [skill_high("HAB-LOG"), skill_high("HAB-NUM")],
            "tecnologico": [interest_high("INT-TEC"), skill_high("HAB-LOG")],
            "cientifico": [interest_high("INT-CIE"), skill_high("HAB-LOG")],
            "humanista_social": [interest_high("INT-SOC"), skill_high("HAB-SOC")],
            "practico": [interest_high("INT-PRA"), skill_high("HAB-TEC")],
            "creativo": [interest_high("INT-ART"), skill_high("HAB-CRE")],
            "gestor": [interest_high("INT-ADM"), skill_high("HAB-ORG")],
            "comunicador": [interest_high("INT-COM"), skill_high("HAB-VER")],
        }
        for name, conditions in cases.items():
            with self.subTest(name):
                self.assertIn(profile(name), self.run_rules(*conditions))
                self.assertNotIn(profile(name), self.run_rules(conditions[0]))
                self.assertNotIn(profile(name), self.run_rules(conditions[1]))

    def test_area_and_type_rules(self):
        cases = [
            ([interest_high("INT-TEC"), skill_high("HAB-LOG")], area("Tecnología e Informática")),
            ([interest_high("INT-TEC"), skill_high("HAB-LOG"), skill_high("HAB-NUM")], area("Ingeniería y Construcción")),
            ([interest_high("INT-PRA"), skill_high("HAB-TEC"), skill_high("HAB-LOG"), skill_high("HAB-NUM")], area("Ingeniería y Construcción")),
            ([interest_high("INT-CIE"), skill_high("HAB-LOG"), interest_high("INT-SOC")], area("Ciencias de la Salud")),
            ([interest_high("INT-CIE"), skill_high("HAB-LOG"), interest_high("INT-PRA")], area("Ciencias Naturales y Agroindustria")),
            ([interest_high("INT-SOC"), skill_high("HAB-SOC"), skill_high("HAB-VER")], area("Educación")),
            ([interest_high("INT-SOC"), skill_high("HAB-SOC"), interest_high("INT-COM"), skill_high("HAB-VER")], area("Ciencias Sociales y Jurídicas")),
            ([interest_high("INT-ADM"), skill_high("HAB-ORG"), skill_high("HAB-NUM")], area("Administración y Economía")),
            ([interest_high("INT-ART"), skill_high("HAB-CRE")], area("Artes, Diseño y Arquitectura")),
            ([interest_high("INT-COM"), skill_high("HAB-VER"), skill_high("HAB-CRE")], area("Comunicación y Medios")),
            ([interest_high("INT-PRA"), skill_high("HAB-TEC")], area("Oficios y Técnicos Industriales")),
            ([interest_high("INT-SOC"), skill_high("HAB-SOC"), interest_high("INT-ADM"), skill_high("HAB-ORG")], area("Turismo, Hotelería y Servicios")),
            ([interest_high("INT-PRA"), skill_high("HAB-TEC")], program_type("TECHNICAL")),
            ([skill_high("HAB-LOG"), skill_high("HAB-NUM")], program_type("UNIVERSITY")),
        ]
        for conditions, expected in cases:
            with self.subTest(expected):
                self.assertIn(expected, self.run_rules(*conditions))

    def test_rules_are_not_exclusive(self):
        facts = self.run_rules(
            interest_high("INT-TEC"), skill_high("HAB-LOG"), skill_high("HAB-NUM"),
            interest_high("INT-ART"), skill_high("HAB-CRE"),
        )
        for expected in (profile("tecnologico"), profile("creativo"), profile("analitico")):
            self.assertIn(expected, facts)
        self.assertIn(area("Tecnología e Informática"), facts)
        self.assertIn(area("Artes, Diseño y Arquitectura"), facts)

    def test_low_skill_or_medium_level_never_fires(self):
        scores = [
            {"code": "INT-TEC", "kind": "INTEREST", "score": 60.0, "valid": True, "level": "MEDIUM"},
            {"code": "HAB-LOG", "kind": "SKILL", "score": 30.0, "valid": True, "level": "LOW"},
        ]
        self.assertEqual(forward_chain(facts_from_scores(scores), RULES).trace, ())


class SummaryTests(SimpleTestCase):
    def test_summary_shape_and_texts(self):
        outcome = forward_chain(
            {interest_high("INT-TEC"), skill_high("HAB-LOG"), skill_high("HAB-NUM")}, RULES
        )
        summary = explain.summarize(outcome)
        self.assertEqual(summary["profiles"], ["analitico", "tecnologico"])
        self.assertEqual([a["name"] for a in summary["areas"]],
                         ["Tecnología e Informática", "Ingeniería y Construcción"])
        self.assertEqual(summary["program_types"], ["UNIVERSITY"])
        step = summary["steps"][0]
        self.assertEqual(set(step), {"rule", "layer", "iteration", "if", "then", "text"})
        self.assertTrue(all(s["text"] for s in summary["steps"]))

    def test_empty_summary(self):
        summary = explain.summarize(forward_chain(set(), RULES))
        self.assertEqual((summary["profiles"], summary["areas"], summary["steps"]), ([], [], []))


class InferenceIntegrationTests(EvaluationTestCase):
    def submitted(self):
        pk = self.start().json()["id"]
        from tests.test_evaluations import items_for
        self.put(pk, items_for(INTERESTS + SKILLS))
        response = self.submit(pk)
        self.assertEqual(response.status_code, 200)
        return pk, response

    def test_submit_stores_inference(self):
        pk, response = self.submitted()
        stored = ResultInference.objects.get(result__evaluation_id=pk)
        self.assertEqual(stored.rules_version, RULESET_VERSION)
        self.assertTrue(stored.facts)
        body = response.json()["result"]["inference"]
        self.assertEqual(body["rules_version"], RULESET_VERSION)
        for key in ("profiles", "areas", "program_types", "steps"):
            self.assertIn(key, body)

    def test_stored_reasoning_is_reproducible(self):
        pk, _ = self.submitted()
        stored = ResultInference.objects.get(result__evaluation_id=pk)
        from apps.evaluations import inference
        again = explain.summarize(
            forward_chain(
                facts_from_scores(inference.scores_as_dicts(stored.result)), RULES
            )
        )
        self.assertEqual(again, stored.summary)

    def test_result_endpoint_includes_inference(self):
        pk, _ = self.submitted()
        body = self.client.get(url(pk, "result/"), **self.headers(self.ana)).json()
        self.assertIn("inference", body)

    def test_inference_failure_rolls_back_submit(self):
        from unittest import mock
        from apps.evaluations.models import Evaluation, EvaluationResult
        pk = self.start().json()["id"]
        from tests.test_evaluations import items_for
        self.put(pk, items_for(INTERESTS + SKILLS))
        with mock.patch("apps.evaluations.inference.store_inference", side_effect=RuntimeError("x")):
            with self.assertRaises(RuntimeError):
                self.submit(pk)
        self.assertEqual(Evaluation.objects.get(pk=pk).status, Evaluation.Status.DRAFT)
        self.assertFalse(EvaluationResult.objects.filter(evaluation_id=pk).exists())