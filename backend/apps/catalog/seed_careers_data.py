"""
Carreras y programas técnicos GENÉRICOS (no ligados a una institución) y sus pesos.

Cada carrera hereda los pesos de su área (core/domain/areas.py) y puede ajustarlos con
`overrides` ({código: peso}; None quita la dimensión). Las descripciones son orientativas.
IMPORTANTE: aquí NO hay instituciones ni sedes: las ofertas reales (con fuente y fecha de
verificación) se cargan aparte, desde el admin o con un comando de ofertas verificadas.
"""

VERSION = "1.0"

U, T = "UNIVERSITY", "TECHNICAL"
TEC, ENG, SAL, NAT = (
    "Tecnología e Informática",
    "Ingeniería y Construcción",
    "Ciencias de la Salud",
    "Ciencias Naturales y Agroindustria",
)
EDU, SOC, ADM, ART = (
    "Educación",
    "Ciencias Sociales y Jurídicas",
    "Administración y Economía",
    "Artes, Diseño y Arquitectura",
)
MED, OFI, TUR = (
    "Comunicación y Medios",
    "Oficios y Técnicos Industriales",
    "Turismo, Hotelería y Servicios",
)

# (nombre, tipo, área, descripción, campo laboral, overrides)
CAREERS = [
    # Tecnología e Informática
    ("Ingeniería en Sistemas", U, TEC, "Diseño, desarrollo y mantenimiento de sistemas de información y software.", "Desarrollo de software, análisis de sistemas, administración de bases de datos, gestión de proyectos de TI.", {"HAB-NUM": 3}),
    ("Ciencias de la Computación", U, TEC, "Fundamentos teóricos de la computación, algoritmos y programación avanzada.", "Desarrollo de software, investigación, análisis de datos.", {"INT-CIE": 2, "HAB-LOG": 3}),
    ("Ingeniería en Ciberseguridad", U, TEC, "Protección de sistemas, redes e información frente a amenazas.", "Seguridad informática, auditoría de sistemas, respuesta a incidentes.", {"HAB-TEC": 2}),
    ("Técnico en Soporte Informático", T, TEC, "Instalación, mantenimiento y soporte de equipos de cómputo y redes pequeñas.", "Soporte técnico, mantenimiento de equipos, administración básica de redes.", {"HAB-TEC": 3, "INT-PRA": 1, "HAB-NUM": None}),
    ("Técnico en Programación", T, TEC, "Programación de aplicaciones y sitios web a nivel técnico.", "Desarrollo web y de aplicaciones, soporte de sistemas.", {"HAB-NUM": 1}),
    # Ingeniería y Construcción
    ("Ingeniería Civil", U, ENG, "Diseño, construcción y supervisión de obras de infraestructura.", "Construcción, supervisión de obras, diseño estructural, proyectos viales e hidráulicos.", {"INT-PRA": 2}),
    ("Ingeniería Industrial", U, ENG, "Optimización de procesos, producción y recursos en empresas.", "Producción, calidad, logística, mejora de procesos.", {"INT-ADM": 1, "HAB-ORG": 2}),
    ("Ingeniería Eléctrica", U, ENG, "Generación, distribución y uso de la energía eléctrica.", "Energía, instalaciones eléctricas, automatización industrial.", {"HAB-TEC": 3, "INT-CIE": 2}),
    ("Ingeniería Mecánica", U, ENG, "Diseño y mantenimiento de máquinas y sistemas mecánicos.", "Industria, mantenimiento, diseño de equipos.", {"HAB-TEC": 3, "INT-PRA": 3}),
    ("Técnico en Construcción", T, ENG, "Apoyo técnico en obras de construcción: planos, materiales y supervisión básica.", "Obras civiles, topografía básica, supervisión de obra.", {"INT-PRA": 3, "HAB-NUM": 2}),
    # Ciencias de la Salud
    ("Medicina", U, SAL, "Prevención, diagnóstico y tratamiento de enfermedades.", "Atención clínica, salud pública, investigación médica.", {"INT-CIE": 3, "HAB-VER": 3}),
    ("Enfermería", U, SAL, "Cuidado integral de pacientes y apoyo en la atención de salud.", "Hospitales, centros de salud, atención comunitaria.", {"INT-SOC": 3, "HAB-SOC": 3, "INT-CIE": 2}),
    ("Odontología", U, SAL, "Salud bucal: prevención, diagnóstico y tratamiento.", "Consulta odontológica, salud pública.", {"INT-PRA": 1, "HAB-TEC": 1}),
    ("Química y Farmacia", U, SAL, "Medicamentos: su composición, producción y uso adecuado.", "Farmacias, laboratorios, industria farmacéutica.", {"INT-CIE": 3, "HAB-NUM": 2, "INT-SOC": 1}),
    ("Técnico en Laboratorio Clínico", T, SAL, "Análisis de muestras clínicas como apoyo al diagnóstico.", "Laboratorios clínicos, hospitales.", {"INT-PRA": 1, "HAB-ORG": 1, "INT-SOC": 1}),
    # Ciencias Naturales y Agroindustria
    ("Ingeniería Agronómica", U, NAT, "Producción agrícola sostenible y manejo de cultivos.", "Producción agrícola, asistencia técnica, agroindustria.", {"INT-PRA": 3}),
    ("Biología", U, NAT, "Estudio de los seres vivos y su entorno.", "Investigación, conservación, laboratorios, educación ambiental.", {"INT-CIE": 3, "INT-PRA": 1}),
    ("Ingeniería Ambiental", U, NAT, "Gestión y protección de los recursos naturales y el ambiente.", "Gestión ambiental, consultoría, instituciones públicas.", {"HAB-NUM": 2}),
    ("Técnico en Producción Agrícola", T, NAT, "Manejo práctico de cultivos y de la producción agropecuaria.", "Fincas, cooperativas, asistencia técnica.", {"INT-PRA": 3, "HAB-TEC": 2, "INT-CIE": 2}),
    # Educación
    ("Pedagogía", U, EDU, "Formación de docentes y diseño de procesos de enseñanza.", "Docencia, coordinación educativa, orientación.", {}),
    ("Educación Básica", U, EDU, "Formación de docentes para los niveles básicos de enseñanza.", "Docencia en escuelas y centros educativos.", {"HAB-SOC": 3}),
    ("Psicología", U, EDU, "Estudio del comportamiento y los procesos mentales.", "Psicología clínica, educativa y organizacional.", {"INT-CIE": 2, "HAB-SOC": 3, "HAB-ORG": None}),
    # Ciencias Sociales y Jurídicas
    ("Derecho", U, SOC, "Estudio de las leyes y su aplicación para resolver conflictos.", "Abogacía, notariado, sector público, asesoría legal.", {"HAB-VER": 3, "HAB-LOG": 2}),
    ("Trabajo Social", U, SOC, "Atención a personas y comunidades para mejorar sus condiciones de vida.", "Instituciones públicas, ONG, programas comunitarios.", {"INT-SOC": 3, "HAB-SOC": 3}),
    ("Sociología", U, SOC, "Análisis de la sociedad, sus grupos y sus cambios.", "Investigación social, consultoría, sector público.", {"INT-CIE": 2}),
    # Administración y Economía
    ("Administración de Empresas", U, ADM, "Planificación y dirección de organizaciones.", "Gerencia, emprendimiento, administración pública y privada.", {}),
    ("Contaduría Pública", U, ADM, "Registro, análisis y control de la información financiera.", "Contabilidad, auditoría, finanzas.", {"HAB-NUM": 3, "HAB-ORG": 3, "INT-COM": None}),
    ("Economía", U, ADM, "Estudio de cómo se producen, distribuyen y consumen los recursos.", "Análisis económico, banca, sector público, consultoría.", {"HAB-LOG": 2, "INT-CIE": 1}),
    ("Mercadotecnia", U, ADM, "Estudio de mercados y promoción de productos y servicios.", "Publicidad, ventas, investigación de mercados.", {"INT-COM": 2, "HAB-CRE": 1}),
    ("Técnico en Contabilidad", T, ADM, "Apoyo contable y administrativo en empresas.", "Auxiliar contable, administración de oficinas.", {"INT-COM": None}),
    # Artes, Diseño y Arquitectura
    ("Arquitectura", U, ART, "Diseño de espacios y edificaciones.", "Diseño arquitectónico, urbanismo, construcción.", {"HAB-LOG": 2, "INT-TEC": 1}),
    ("Diseño Gráfico", U, ART, "Comunicación visual: identidad, publicidad y medios digitales.", "Agencias, medios, empresas, freelance.", {"INT-TEC": 2}),
    ("Artes Plásticas", U, ART, "Expresión artística con pintura, escultura y otras técnicas.", "Arte, docencia artística, galerías.", {"INT-TEC": None, "HAB-LOG": None}),
    # Comunicación y Medios
    ("Periodismo", U, MED, "Investigación y comunicación de noticias en distintos medios.", "Prensa, radio, televisión, medios digitales.", {"HAB-VER": 3, "INT-COM": 3}),
    ("Comunicación Audiovisual", U, MED, "Producción de contenidos de video, audio y medios digitales.", "Televisión, cine, productoras, redes sociales.", {"INT-ART": 2, "HAB-CRE": 3}),
    # Oficios y Técnicos Industriales
    ("Técnico en Electricidad", T, OFI, "Instalación y mantenimiento de sistemas eléctricos.", "Instalaciones eléctricas, mantenimiento industrial.", {"HAB-TEC": 3}),
    ("Técnico en Mecánica Automotriz", T, OFI, "Diagnóstico y reparación de vehículos.", "Talleres, concesionarias, mantenimiento de flotas.", {"INT-PRA": 3}),
    ("Técnico en Refrigeración y Aire Acondicionado", T, OFI, "Instalación y mantenimiento de equipos de climatización.", "Servicios de mantenimiento, comercios, industria.", {}),
    # Turismo, Hotelería y Servicios
    ("Turismo y Hotelería", U, TUR, "Gestión de servicios turísticos y de alojamiento.", "Hoteles, agencias, turismo sostenible.", {}),
    ("Técnico en Gastronomía", T, TUR, "Preparación de alimentos y gestión básica de cocinas.", "Restaurantes, hoteles, emprendimiento.", {"INT-PRA": 2, "HAB-CRE": 2, "INT-ADM": 1}),
]