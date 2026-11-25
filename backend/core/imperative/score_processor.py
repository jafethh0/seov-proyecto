"""
Procesador de puntuaciones (paradigma IMPERATIVO).

Recorre preguntas y respuestas con ciclos, acumula sumas en variables mutables y decide
con condicionales. Es Python puro: no importa Django ni toca la base de datos; recibe
datos simples y devuelve datos simples, para poder probarlo de forma aislada.

Fórmula (una sola, derivada de los datos de cada pregunta):

    valor de una pregunta  = (puntos - mínimo) / (máximo - mínimo)      -> de 0 a 1
    score de la dimensión  = 100 * suma(peso * valor) / suma(peso)       -> de 0 a 100

Con una escala de 1 a 5 el valor es (p - 1) / 4; con una pregunta de 0 a 1 o de 0 a 2
es p / máximo. Las preguntas omitidas no entran ni en el numerador ni en el denominador.
Una dimensión es válida si se respondió al menos MIN_ANSWERED_RATIO de sus preguntas;
si no, su score es None (no se inventa un cero).
"""
from math import ceil

from core import config


def compute_dimension_scores(dimensions, questions, answers, min_answered_ratio=None):
    """
    dimensions: lista de (código, tipo) en el orden en que se devolverán.
    questions:  lista de dicts {"id", "min_points", "max_points", "links": [(código, peso)]}.
    answers:    dict {id de pregunta: puntos de la opción elegida}.

    Devuelve una lista de dicts, uno por dimensión:
        {"code", "kind", "score", "answered", "total", "required", "valid"}
    """
    if min_answered_ratio is None:
        min_answered_ratio = config.MIN_ANSWERED_RATIO

    # 1) Acumuladores por dimensión.
    accumulators = {}
    for code, kind in dimensions:
        accumulators[code] = {
            "code": code,
            "kind": kind,
            "numerator": 0.0,
            "denominator": 0.0,
            "answered": 0,
            "total": 0,
        }

    # 2) Se recorre cada pregunta y se reparte su aporte entre sus dimensiones.
    for question in questions:
        lowest = question["min_points"]
        highest = question["max_points"]
        span = highest - lowest
        if span <= 0:
            raise ValueError(f"La pregunta {question['id']} no tiene un rango de puntos válido.")

        is_answered = question["id"] in answers
        value = 0.0
        if is_answered:
            points = answers[question["id"]]
            if points < lowest or points > highest:
                raise ValueError(
                    f"Los puntos de la pregunta {question['id']} están fuera de su rango."
                )
            value = (points - lowest) / span

        for code, weight in question["links"]:
            if weight <= 0:
                raise ValueError(f"El peso de la pregunta {question['id']} debe ser positivo.")
            if code not in accumulators:
                raise ValueError(f"Dimensión desconocida: {code}.")
            accumulator = accumulators[code]
            accumulator["total"] += 1
            if is_answered:
                accumulator["answered"] += 1
                accumulator["numerator"] += weight * value
                accumulator["denominator"] += weight

    # 3) Se valida cada dimensión y se calcula su puntuación.
    results = []
    for code, kind in dimensions:
        accumulator = accumulators[code]
        required = ceil(accumulator["total"] * min_answered_ratio)
        is_valid = (
            accumulator["total"] > 0
            and accumulator["answered"] >= required
            and accumulator["denominator"] > 0
        )
        score = None
        if is_valid:
            score = round(100 * accumulator["numerator"] / accumulator["denominator"], 2)
        results.append(
            {
                "code": code,
                "kind": kind,
                "score": score,
                "answered": accumulator["answered"],
                "total": accumulator["total"],
                "required": required,
                "valid": is_valid,
            }
        )
    return results