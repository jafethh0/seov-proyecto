"""
Pesos por área (sección 9 del diseño): 3 = núcleo, 2 = importante, 1 = complementario.
Sirven para (a) dar pesos iniciales a las carreras de cada área y (b) calcular la afinidad
de la persona con cada área cuando las reglas no bastan (áreas «por afinidad»).
"""

AREA_WEIGHTS = {
    "Tecnología e Informática": {"INT-TEC": 3, "INT-CIE": 1, "HAB-LOG": 3, "HAB-NUM": 2, "HAB-TEC": 1},
    "Ingeniería y Construcción": {"INT-TEC": 2, "INT-PRA": 2, "INT-CIE": 1, "HAB-NUM": 3, "HAB-LOG": 2, "HAB-TEC": 2},
    "Ciencias de la Salud": {"INT-CIE": 3, "INT-SOC": 2, "HAB-VER": 2, "HAB-SOC": 2, "HAB-LOG": 1, "HAB-NUM": 1},
    "Ciencias Naturales y Agroindustria": {"INT-CIE": 3, "INT-PRA": 2, "HAB-LOG": 2, "HAB-NUM": 1, "HAB-TEC": 1},
    "Educación": {"INT-SOC": 3, "INT-COM": 2, "HAB-VER": 3, "HAB-SOC": 3, "HAB-ORG": 1},
    "Ciencias Sociales y Jurídicas": {"INT-SOC": 2, "INT-COM": 2, "INT-CIE": 1, "HAB-VER": 3, "HAB-LOG": 2, "HAB-SOC": 1},
    "Administración y Economía": {"INT-ADM": 3, "INT-COM": 1, "HAB-NUM": 3, "HAB-ORG": 3, "HAB-LOG": 1},
    "Artes, Diseño y Arquitectura": {"INT-ART": 3, "INT-TEC": 1, "HAB-CRE": 3, "HAB-LOG": 1},
    "Comunicación y Medios": {"INT-COM": 3, "INT-ART": 1, "HAB-VER": 3, "HAB-CRE": 2, "HAB-SOC": 1},
    "Oficios y Técnicos Industriales": {"INT-PRA": 3, "INT-TEC": 1, "HAB-TEC": 3, "HAB-ORG": 1},
    "Turismo, Hotelería y Servicios": {"INT-SOC": 2, "INT-ADM": 2, "INT-COM": 1, "HAB-SOC": 3, "HAB-ORG": 2, "HAB-VER": 1},
}