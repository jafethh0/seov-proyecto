"""
Ofertas académicas REALES, cada una con su fuente y fecha de verificación.

Regla del proyecto: aquí solo entra lo que aparece en una fuente oficial de la institución.
Si un dato no está en la fuente (requisitos de ingreso, modalidad distinta, etc.) se deja
vacío; nunca se inventa. `verified_at` es la fecha en que se consultó la fuente.

Cada oferta enlaza una carrera GENÉRICA del catálogo (columna `generic`) con el nombre
oficial que usa la institución (columna `official`). Solo se emparejan carreras que son
la misma formación; si no hay equivalente en el catálogo, la carrera no se carga.
"""
from datetime import date

# ---------------------------------------------------------------------------
# UNAH — Universidad Nacional Autónoma de Honduras (pública)
# Fuente: Dirección de Estadística UNAH, "Oferta educativa 2024 (preliminar)",
# tabla de licenciaturas (Anexo 1.2). Años de duración tal como aparecen en la fuente.
# CU = Ciudad Universitaria (Tegucigalpa, Francisco Morazán)
# VS = UNAH Valle de Sula (San Pedro Sula, Cortés)
# Pendiente: centros regionales (CURLA, CUROC, CURC, CURNO, CURLP) y telecentros.
# ---------------------------------------------------------------------------
UNAH_SOURCE = "https://estadistica.unah.edu.hn/dmsdocument/16563-oferta-educativa-2024-preliminar"
UNAH_VERIFIED_AT = date(2026, 11, 26)

UNAH_INSTITUTION = {
    "name": "Universidad Nacional Autónoma de Honduras",
    "acronym": "UNAH",
    "sector": "PUBLIC",
    "website": "https://www.unah.edu.hn",
}

UNAH_CAMPUSES = {
    "CU": {"name": "Ciudad Universitaria", "department": "Francisco Morazán", "city": "Tegucigalpa"},
    "VS": {"name": "UNAH Valle de Sula", "department": "Cortés", "city": "San Pedro Sula"},
}

# (carrera genérica del catálogo, nombre oficial UNAH, años, sedes)
UNAH_OFFERINGS = [
    ("Ingeniería en Sistemas", "Ingeniería en Sistemas", 5, ["CU", "VS"]),
    ("Ingeniería Civil", "Ingeniería Civil", 5, ["CU", "VS"]),
    ("Ingeniería Industrial", "Ingeniería Industrial", 5, ["CU", "VS"]),
    ("Ingeniería Eléctrica", "Ingeniería Eléctrica Industrial", 5, ["CU", "VS"]),
    ("Ingeniería Mecánica", "Ingeniería Mecánica Industrial", 5, ["CU", "VS"]),
    ("Medicina", "Medicina y Cirugía", 8, ["CU", "VS"]),
    ("Enfermería", "Enfermería", 5, ["CU", "VS"]),
    ("Odontología", "Odontología", 6, ["CU", "VS"]),
    ("Química y Farmacia", "Química y Farmacia", 5, ["CU"]),
    ("Biología", "Biología", 4.5, ["CU", "VS"]),
    ("Pedagogía", "Pedagogía y Ciencias de la Educación", 4.5, ["CU", "VS"]),
    ("Psicología", "Psicología", 4.5, ["CU", "VS"]),
    ("Derecho", "Derecho", 5, ["CU", "VS"]),
    ("Trabajo Social", "Trabajo Social", 5, ["CU"]),
    ("Sociología", "Sociología", 4.5, ["CU", "VS"]),
    ("Administración de Empresas", "Administración y Generación de Empresas", 5, ["CU", "VS"]),
    ("Contaduría Pública", "Contaduría Pública y Finanzas", 4, ["CU", "VS"]),
    ("Economía", "Economía", 4, ["CU", "VS"]),
    ("Mercadotecnia", "Mercadotecnia", 5, ["CU"]),
    ("Arquitectura", "Arquitectura", 5, ["CU"]),
    ("Periodismo", "Periodismo", 4, ["CU", "VS"]),
]