"""
Capa SQL declarativa (paradigma DECLARATIVO).

Las vistas y las consultas viven en archivos .sql (carpeta sql/): describen QUÉ datos se
quieren, no cómo recorrerlos. Este módulo solo las carga y las ejecuta con parámetros
enlazados (nunca se arma SQL concatenando valores).

Las vistas se (re)crean después de cada `migrate` (señal post_migrate), de modo que siempre
reflejan el esquema actual y funcionan igual en PostgreSQL y en SQLite.
"""
import logging
from decimal import Decimal
from pathlib import Path

from django.db import DEFAULT_DB_ALIAS, connections, transaction

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent / "sql"

# Orden de creación: cada vista solo depende de tablas o de vistas anteriores.
VIEWS = ["v_available_offerings", "v_career_weights", "v_result_scores", "v_career_affinity"]

REQUIRED_TABLES = {
    "catalog_programoffering", "catalog_careerprogram", "catalog_careercategory",
    "catalog_campus", "catalog_institution", "catalog_department", "catalog_careerdimension",
    "questionnaires_dimension", "evaluations_evaluation", "evaluations_evaluationresult",
    "evaluations_resultdimensionscore", "evaluations_careerrecommendation",
}


def read_sql(folder, name):
    return (SQL_DIR / folder / f"{name}.sql").read_text(encoding="utf-8")


def create_views(using=DEFAULT_DB_ALIAS):
    """Crea (o recrea) las vistas. Si faltan tablas (migración parcial), no hace nada."""
    connection = connections[using]
    existing = set(connection.introspection.table_names())
    if not REQUIRED_TABLES <= existing:
        logger.warning("Vistas SQL omitidas: faltan tablas %s", sorted(REQUIRED_TABLES - existing))
        return False
    with transaction.atomic(using=using), connection.cursor() as cursor:
        for name in reversed(VIEWS):
            cursor.execute(f"DROP VIEW IF EXISTS {name}")
        for name in VIEWS:
            cursor.execute(read_sql("views", name))
    return True


def _plain(value):
    return float(value) if isinstance(value, Decimal) else value


def fetch_all(name, params=None, using=DEFAULT_DB_ALIAS):
    """Ejecuta sql/queries/<name>.sql y devuelve una lista de diccionarios."""
    with connections[using].cursor() as cursor:
        cursor.execute(read_sql("queries", name), params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, map(_plain, row))) for row in cursor.fetchall()]


def fetch_one(name, params=None, using=DEFAULT_DB_ALIAS):
    rows = fetch_all(name, params, using)
    return rows[0] if rows else None