"""
Base de conocimiento: las reglas del motor experto (versión 1.0).

Las reglas son DATOS (objetos inmutables), no código: el motor (engine.py) las recorre sin
conocer su contenido. Cada una lleva identificador, capa, condiciones (se combinan con Y),
conclusión, prioridad, texto de explicación y estado.
"""
from dataclasses import dataclass

from .facts import area, interest_high, profile, program_type, skill_high

RULESET_VERSION = "1.0"

AREA_TECH = "Tecnología e Informática"
AREA_ENG = "Ingeniería y Construcción"
AREA_HEALTH = "Ciencias de la Salud"
AREA_NATURE = "Ciencias Naturales y Agroindustria"
AREA_EDU = "Educación"
AREA_SOCIAL = "Ciencias Sociales y Jurídicas"
AREA_ADMIN = "Administración y Economía"
AREA_ART = "Artes, Diseño y Arquitectura"
AREA_MEDIA = "Comunicación y Medios"
AREA_TRADES = "Oficios y Técnicos Industriales"
AREA_TOURISM = "Turismo, Hotelería y Servicios"

AREAS = (
    AREA_TECH, AREA_ENG, AREA_HEALTH, AREA_NATURE, AREA_EDU, AREA_SOCIAL,
    AREA_ADMIN, AREA_ART, AREA_MEDIA, AREA_TRADES, AREA_TOURISM,
)


@dataclass(frozen=True)
class Rule:
    id: str
    layer: int  # 1 perfiles, 2 áreas, 3 tipo de programa
    name: str
    conditions: tuple
    conclusion: tuple
    explanation: str
    priority: int = 0
    active: bool = True


def _r(id, layer, name, conditions, conclusion, explanation):
    return Rule(id, layer, name, tuple(conditions), conclusion, explanation)


RULES = (
    # Capa 1: perfiles
    _r("P1", 1, "Perfil analítico", [skill_high("HAB-LOG"), skill_high("HAB-NUM")],
       profile("analitico"),
       "Tu razonamiento lógico y tu pensamiento numérico salieron altos: apuntan a un perfil analítico."),
    _r("P2", 1, "Perfil tecnológico", [interest_high("INT-TEC"), skill_high("HAB-LOG")],
       profile("tecnologico"),
       "Tu interés alto por la tecnología y tu buen razonamiento lógico apuntan a un perfil tecnológico."),
    _r("P3", 1, "Perfil científico", [interest_high("INT-CIE"), skill_high("HAB-LOG")],
       profile("cientifico"),
       "Tu interés alto por la ciencia y tu buen razonamiento lógico apuntan a un perfil científico."),
    _r("P4", 1, "Perfil humanista y social", [interest_high("INT-SOC"), skill_high("HAB-SOC")],
       profile("humanista_social"),
       "Tu interés alto por ayudar y enseñar a otras personas y tu buena comunicación interpersonal apuntan a un perfil humanista y social."),
    _r("P5", 1, "Perfil práctico", [interest_high("INT-PRA"), skill_high("HAB-TEC")],
       profile("practico"),
       "Tu interés alto por el trabajo práctico y tu buena resolución de problemas técnicos apuntan a un perfil práctico."),
    _r("P6", 1, "Perfil creativo", [interest_high("INT-ART"), skill_high("HAB-CRE")],
       profile("creativo"),
       "Tu interés alto por lo artístico y tu creatividad apuntan a un perfil creativo."),
    _r("P7", 1, "Perfil gestor", [interest_high("INT-ADM"), skill_high("HAB-ORG")],
       profile("gestor"),
       "Tu interés alto por organizar y administrar y tu buena organización apuntan a un perfil gestor."),
    _r("P8", 1, "Perfil comunicador", [interest_high("INT-COM"), skill_high("HAB-VER")],
       profile("comunicador"),
       "Tu interés alto por comunicar y tu buena comprensión verbal apuntan a un perfil comunicador."),
    # Capa 2: áreas sugeridas
    _r("A1", 2, "Área de tecnología", [profile("tecnologico")], area(AREA_TECH),
       "Un perfil tecnológico sugiere el área de Tecnología e Informática."),
    _r("A2", 2, "Área de ingeniería (tecnología y números)",
       [profile("tecnologico"), skill_high("HAB-NUM")], area(AREA_ENG),
       "Un perfil tecnológico con buen pensamiento numérico sugiere Ingeniería y Construcción."),
    _r("A3", 2, "Área de ingeniería (práctico y analítico)",
       [profile("practico"), profile("analitico")], area(AREA_ENG),
       "La combinación de perfil práctico y analítico sugiere Ingeniería y Construcción."),
    _r("A4", 2, "Área de salud", [profile("cientifico"), interest_high("INT-SOC")], area(AREA_HEALTH),
       "Un perfil científico con interés alto por las personas sugiere Ciencias de la Salud."),
    _r("A5", 2, "Área de ciencias naturales", [profile("cientifico"), interest_high("INT-PRA")],
       area(AREA_NATURE),
       "Un perfil científico con interés alto por el trabajo práctico sugiere Ciencias Naturales y Agroindustria."),
    _r("A6", 2, "Área de educación", [profile("humanista_social"), skill_high("HAB-VER")], area(AREA_EDU),
       "Un perfil humanista y social con buena comprensión verbal sugiere Educación."),
    _r("A7", 2, "Área de ciencias sociales y jurídicas",
       [profile("humanista_social"), profile("comunicador")], area(AREA_SOCIAL),
       "La combinación de perfil humanista y comunicador sugiere Ciencias Sociales y Jurídicas."),
    _r("A8", 2, "Área de administración y economía", [profile("gestor"), skill_high("HAB-NUM")],
       area(AREA_ADMIN),
       "Un perfil gestor con buen pensamiento numérico sugiere Administración y Economía."),
    _r("A9", 2, "Área de artes y diseño", [profile("creativo")], area(AREA_ART),
       "Un perfil creativo sugiere Artes, Diseño y Arquitectura."),
    _r("A10", 2, "Área de comunicación y medios", [profile("comunicador"), skill_high("HAB-CRE")],
       area(AREA_MEDIA),
       "Un perfil comunicador con buena creatividad sugiere Comunicación y Medios."),
    _r("A11", 2, "Área de oficios y técnicos", [profile("practico")], area(AREA_TRADES),
       "Un perfil práctico sugiere Oficios y Técnicos Industriales."),
    _r("A12", 2, "Área de turismo y servicios", [profile("humanista_social"), profile("gestor")],
       area(AREA_TOURISM),
       "La combinación de perfil humanista y gestor sugiere Turismo, Hotelería y Servicios."),
    # Capa 3: tipo de programa
    _r("T1", 3, "Programa técnico", [profile("practico")], program_type("TECHNICAL"),
       "Un perfil práctico sugiere destacar programas técnicos."),
    _r("T2", 3, "Programa universitario", [profile("analitico")], program_type("UNIVERSITY"),
       "Un perfil analítico sugiere destacar programas universitarios."),
)