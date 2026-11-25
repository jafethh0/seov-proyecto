"""
Clases del dominio (paradigma ORIENTADO A OBJETOS).

`StudentProfile` agrupa las puntuaciones válidas de una evaluación; `Career` representa
una carrera con sus pesos y sabe calcular su propia compatibilidad con un perfil. No dependen
de Django: se construyen desde la base de datos en apps/evaluations/recommendations.py.
"""
from dataclasses import dataclass, field

from core.functional import affinity


@dataclass(frozen=True)
class StudentProfile:
    scores: dict  # código -> puntuación 0-100 (solo dimensiones válidas)
    levels: dict = field(default_factory=dict)  # código -> HIGH/MEDIUM/LOW

    @classmethod
    def from_scores(cls, items):
        """items: dicts {"code", "score", "valid", "level"} como los del procesador."""
        valid = [i for i in items if i["valid"] and i["score"] is not None]
        return cls(
            scores={i["code"]: i["score"] for i in valid},
            levels={i["code"]: i["level"] for i in valid},
        )


@dataclass(frozen=True)
class Career:
    id: int
    name: str
    program_type: str
    area: str
    weights: dict  # código de dimensión -> peso 1..3

    def interest_affinity(self, profile):
        return affinity.section_affinity(self.weights, profile.scores, "INTEREST")

    def skill_affinity(self, profile):
        return affinity.section_affinity(self.weights, profile.scores, "SKILL")

    def compatibility(self, profile):
        """(índice, caso, afinidad de intereses, afinidad de habilidades)."""
        interest = self.interest_affinity(profile)
        skill = self.skill_affinity(profile)
        index, case = affinity.compat_index(interest, skill)
        return index, case, interest, skill

    def strengths(self, profile, count=3):
        """Dimensiones que más aportan: mayor peso·puntuación, con puntuación ≥ 50."""
        rows = [
            {"code": code, "weight": weight, "score": profile.scores[code]}
            for code, weight in self.weights.items()
            if code in profile.scores and profile.scores[code] >= 50
        ]
        return sorted(rows, key=lambda r: (-(r["weight"] * r["score"]), r["code"]))[:count]

    def to_reinforce(self, profile):
        """Habilidades núcleo (peso 3) con nivel bajo. Informa; nunca excluye la carrera."""
        return sorted(
            code
            for code, weight in self.weights.items()
            if weight == 3
            and affinity.kind_of(code) == "SKILL"
            and profile.levels.get(code) == "LOW"
        )