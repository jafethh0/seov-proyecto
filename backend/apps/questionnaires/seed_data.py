"""
Banco de preguntas del cuestionario SEOV, versión 1.0 (con los ajustes del documento
de recomendaciones v1.1).

Este archivo es la ÚNICA fuente del contenido: ni el frontend ni el procesador
escriben preguntas, pesos o puntos en el código.

Cada opción es una tupla (texto, puntos) o (texto, puntos, criterio).
"""

VERSION = "1.0"
TITLE = "Cuestionario de orientación vocacional"
DESCRIPTION = (
    "Este cuestionario es una guía para explorar opciones. No es un examen ni decide tu futuro."
)
INTERESTS_INSTRUCTIONS = (
    "¿Qué tanto te gustaría hacer cada una de estas actividades? "
    "Elige la opción que más se acerque a lo que sientes. No hay respuestas buenas ni malas."
)
SKILLS_INSTRUCTIONS = (
    "Responde con lo que harías o con la respuesta que consideres correcta. "
    "Puedes usar lápiz y papel."
)

# (tipo, código, nombre, descripción)
DIMENSIONS = [
    ("INTEREST", "INT-CIE", "Científico e investigación", "Interés por investigar, experimentar y analizar datos."),
    ("INTEREST", "INT-TEC", "Tecnológico", "Interés por computadoras, programación y herramientas digitales."),
    ("INTEREST", "INT-SOC", "Social y educativo", "Interés por ayudar, enseñar y trabajar con la comunidad."),
    ("INTEREST", "INT-ART", "Artístico y creativo", "Interés por el arte, el diseño y las ideas originales."),
    ("INTEREST", "INT-ADM", "Administrativo y organizacional", "Interés por organizar equipos, recursos y negocios."),
    ("INTEREST", "INT-PRA", "Práctico y técnico", "Interés por reparar, construir y trabajar con herramientas."),
    ("INTEREST", "INT-COM", "Comunicativo", "Interés por escribir, hablar en público y trabajar con medios."),
    ("SKILL", "HAB-LOG", "Razonamiento lógico", "Series, deducciones y ordenamientos."),
    ("SKILL", "HAB-NUM", "Pensamiento numérico", "Porcentajes, proporciones y lectura de cantidades."),
    ("SKILL", "HAB-VER", "Comprensión verbal", "Vocabulario, analogías y comprensión de lectura."),
    ("SKILL", "HAB-CRE", "Creatividad", "Generar y adaptar alternativas ante un problema."),
    ("SKILL", "HAB-SOC", "Comunicación interpersonal", "Escucha, claridad, límites y búsqueda de acuerdos."),
    ("SKILL", "HAB-ORG", "Organización", "Priorización, estimación de tiempos y planificación."),
    ("SKILL", "HAB-TEC", "Resolución de problemas técnicos", "Razonamiento mecánico y diagnóstico de fallas."),
]

LIKERT_OPTIONS = [("Nada", 1), ("Poco", 2), ("Algo", 3), ("Bastante", 4), ("Mucho", 5)]

LIKERT_JUSTIFICATION = (
    "Ítem de interés declarado en escala de 1 a 5. No tiene respuesta correcta: "
    "1 equivale a 0 % de afinidad y 5 a 100 %."
)
LIKERT_BIAS = (
    "El interés declarado puede depender de las experiencias y oportunidades que la persona "
    "ha tenido; no mide capacidad."
)

# Intereses: 4 actividades por dimensión (se presentan mezcladas, ver build_questions).
INTEREST_ITEMS = {
    "CIE": [
        "Investigar por qué ocurren los fenómenos naturales.",
        "Hacer experimentos para comprobar una idea.",
        "Leer sobre descubrimientos científicos nuevos.",
        "Analizar datos para encontrar patrones o explicaciones.",
    ],
    "TEC": [
        "Aprender cómo funcionan las computadoras, las aplicaciones o los dispositivos electrónicos.",
        "Crear programas, aplicaciones o sitios web.",
        "Probar tecnologías y herramientas digitales nuevas.",
        "Automatizar tareas repetitivas con ayuda de tecnología.",
    ],
    "SOC": [
        "Ayudar a otras personas a aprender algo nuevo.",
        "Participar en proyectos que mejoren la vida de mi comunidad.",
        "Acompañar a personas que atraviesan una situación difícil (de salud, emocional o social).",
        "Explicar temas a niños, jóvenes o adultos.",
    ],
    "ART": [
        "Dibujar, diseñar o crear piezas visuales.",
        "Tocar o componer música, actuar o bailar.",
        "Inventar historias, ideas originales o conceptos nuevos.",
        "Diseñar cómo se ve y cómo se usa un producto, un espacio o una pantalla.",
    ],
    "ADM": [
        "Organizar un equipo o unos recursos para lograr una meta.",
        "Aprender cómo se administra un negocio o una empresa.",
        "Planificar presupuestos, horarios o procesos.",
        "Dirigir un proyecto y decidir qué se hace primero.",
    ],
    "PRA": [
        "Reparar o armar objetos, equipos o instalaciones.",
        "Hacer trabajos cuyos resultados pueda ver y tocar.",
        "Usar herramientas o máquinas (eléctricas, mecánicas, de carpintería, etc.).",
        "Trabajar al aire libre, en un taller, en el campo o en una obra.",
    ],
    "COM": [
        "Escribir textos, artículos o guiones.",
        "Hablar frente a un grupo o presentar ideas.",
        "Trabajar con medios de comunicación: radio, televisión, redes sociales o periodismo.",
        "Convencer o negociar con otras personas usando argumentos.",
    ],
}

# Habilidades: dos tipos de ítem.
#  - Con respuesta correcta: una opción vale 1 y las demás 0.
#  - Situacional (por criterio): opciones de 0, 1 o 2 puntos; el criterio de cada opción
#    describe una conducta observable. Puede haber más de una opción de 2 puntos.
SKILL_ITEMS = {
    "LOG": [
        {
            "text": "¿Qué número sigue en la serie? 2, 6, 12, 20, 30, …",
            "options": [("38", 0), ("40", 0), ("42", 1), ("44", 0)],
            "justification": "Las diferencias entre términos consecutivos son +4, +6, +8 y +10; la siguiente es +12 (30 + 12 = 42).",
            "bias": "Reconocimiento de patrones numéricos; la familiaridad con series puede ayudar, pero no requiere contenido escolar específico.",
        },
        {
            "text": "Todos los técnicos de laboratorio usan guantes. Marta es técnica de laboratorio. Entonces:",
            "options": [
                ("Marta no usa guantes", 0),
                ("Marta usa guantes", 1),
                ("Todos los que usan guantes son técnicos de laboratorio", 0),
                ("No se puede saber nada sobre Marta", 0),
            ],
            "justification": "Deducción directa: si todos los técnicos usan guantes y Marta es técnica, usa guantes. La opción 3 invierte la premisa.",
            "bias": "Lenguaje cotidiano; evita términos técnicos del laboratorio.",
        },
        {
            "text": "Cuatro personas hacen fila. Diego está primero. Ana está antes que Beto. Carla está después de Beto. ¿Quién está en tercer lugar?",
            "options": [("Carla", 0), ("Diego", 0), ("Ana", 0), ("Beto", 1)],
            "justification": "Orden único: Diego, Ana, Beto, Carla. El tercer lugar es Beto.",
            "bias": "Ordenamiento lógico; no depende de conocimientos previos.",
        },
    ],
    "NUM": [
        {
            "text": "Un producto cuesta L 800 y tiene 15 % de descuento. ¿Cuánto se paga?",
            "options": [("L 680", 1), ("L 700", 0), ("L 720", 0), ("L 640", 0)],
            "justification": "15 % de 800 = 120; 800 − 120 = 680. Los distractores equivalen a descuentos de 12.5 %, 10 % y 20 %.",
            "bias": "Situación de compra cotidiana; requiere manejo de porcentajes.",
        },
        {
            "text": "Una máquina empaca 45 cajas en 9 minutos. A ese ritmo, ¿cuántas cajas empaca en 1 hora?",
            "options": [("180", 0), ("270", 0), ("300", 1), ("405", 0)],
            "justification": "45 / 9 = 5 cajas por minuto; 5 × 60 = 300.",
            "bias": "Proporcionalidad con unidades de tiempo.",
        },
        {
            "text": "Un negocio vendió esta cantidad de unidades de lunes a viernes: 12, 15, 9, 18 y 6. ¿Cuál es el promedio diario?",
            "options": [("10", 0), ("12", 1), ("13", 0), ("15", 0)],
            "justification": "Suma = 60; 60 / 5 = 12.",
            "bias": "Lectura de cantidades y promedio simple.",
        },
    ],
    "VER": [
        {
            "text": "¿Qué palabra tiene el significado más cercano a «escasez»?",
            "options": [("abundancia", 0), ("variedad", 0), ("exceso", 0), ("carencia", 1)],
            "justification": "Escasez = falta o poca disponibilidad de algo; carencia es el sinónimo más cercano.",
            "bias": "Vocabulario de uso general.",
        },
        {
            "text": "Médico es a hospital como maestro es a:",
            "options": [("libro", 0), ("examen", 0), ("escuela", 1), ("pizarra", 0)],
            "justification": "Analogía profesión–lugar de trabajo.",
            "bias": "Vocabulario cotidiano; no requiere conocimiento especializado.",
        },
        {
            "passage": "Una cooperativa agrícola decidió guardar parte de su cosecha de maíz en lugar de venderla de inmediato. Meses después, cuando el precio subió, vendió el grano y obtuvo mayores ingresos, aunque tuvo que pagar por el almacenamiento.",
            "text": "¿Cuál es la idea principal del texto?",
            "options": [
                ("La cooperativa perdió dinero por guardar el maíz", 0),
                ("Esperar para vender permitió obtener mejores ingresos pese al costo de almacenar", 1),
                ("El maíz se echó a perder en la bodega", 0),
                ("El precio del maíz bajó durante el año", 0),
            ],
            "justification": "La idea principal resume el hecho central y su condición (mayores ingresos a pesar del costo).",
            "bias": "Contexto agrícola familiar en Honduras; no exige conocimiento técnico agrícola.",
        },
    ],
    "CRE": [
        {
            "text": "Una pulpería (tienda de barrio) vende cada vez menos y quieres recuperar clientes. ¿Cuál sería tu primer paso?",
            "options": [
                ("Copiar exactamente lo que hace la tienda vecina", 1, "Toma una referencia, pero sin adaptarla ni generar alternativas propias."),
                ("Esperar a que las ventas mejoren solas", 0, "No explora ninguna alternativa."),
                ("Anotar muchas ideas distintas, sin descartar ninguna al principio, y luego elegir las que se puedan probar", 2, "Genera variedad de alternativas antes de evaluarlas."),
                ("Fijarme en lo que funciona en otras tiendas y adaptarlo a los clientes de mi barrio", 2, "Adapta soluciones existentes al contexto propio; es una forma válida de creatividad aplicada."),
            ],
            "justification": "Se puntúa la exploración de alternativas (generar o adaptar), no el tipo de idea.",
            "bias": "Requiere familiaridad con pequeños negocios; no depende de conocimientos artísticos.",
        },
        {
            "text": "En tu colegio se recicla muy poco y no hay presupuesto para campañas. ¿Cómo abordas el problema?",
            "options": [
                ("Pongo avisos pidiendo que se recicle", 1, "Propone una acción, pero única y habitual, sin explorar alternativas."),
                ("Pienso varias formas distintas (un reto entre secciones, puntos de recolección, usar materiales reciclados) y pruebo una a pequeña escala", 2, "Genera varias alternativas y las prueba antes de generalizar."),
                ("Espero a que las autoridades hagan algo", 0, "No propone ninguna acción."),
                ("Busco cómo lo resolvieron en otro colegio y adapto lo que sirva al mío", 2, "Adapta una solución existente al contexto propio."),
            ],
            "justification": "Se puntúa la variedad y la adaptación, sin exigir una solución artística o de diseño.",
            "bias": "Escenario escolar conocido; supone cierta autonomía para proponer iniciativas.",
        },
        {
            "text": "Aplicaste el método habitual para resolver un problema y no funcionó. ¿Qué haces?",
            "options": [
                ("Repito el mismo método con más esfuerzo", 0, "No cambia el enfoque."),
                ("Pido ayuda y aplico exactamente la solución de otra persona", 1, "Busca apoyo y otra vía, pero no la adapta al problema propio."),
                ("Dejo el problema sin resolver", 0, "Abandona el problema."),
                ("Reformulo el problema, busco enfoques usados en otros campos y pruebo uno distinto", 2, "Reformula el problema y explora un enfoque nuevo."),
            ],
            "justification": "Se puntúa la reformulación y la exploración de enfoques distintos.",
            "bias": "Escenario genérico; la persona puede responder según lo que cree que se espera.",
        },
    ],
    "SOC": [
        {
            "text": "Un compañero de equipo no entregó su parte y el trabajo vence mañana. ¿Qué haces primero?",
            "options": [
                ("Hago su parte sin decirle nada para evitar problemas", 0, "Evita la conversación: no comunica la necesidad ni su límite."),
                ("Hablo con él en privado para entender qué pasó y acordamos cómo cubrir lo pendiente", 2, "Escucha, pregunta y acuerda una solución de forma directa y respetuosa."),
                ("Escribo al grupo lo que falta y propongo repartirlo, pidiendo que todos confirmen", 2, "Comunica la necesidad con claridad y busca un acuerdo del equipo."),
                ("Aviso al profesor lo ocurrido sin haber hablado antes con mi compañero", 1, "Pide apoyo, pero omite el diálogo directo que podría resolverlo."),
                ("Le reclamo delante de todos", 0, "Comunica con hostilidad y expone a la persona."),
            ],
            "justification": "Se puntúan conductas observables: comunicar la necesidad, escuchar y buscar acuerdos. Hay más de una respuesta razonable.",
            "bias": "Responde a un escenario hipotético; no demuestra cómo actuaría la persona en la realidad.",
        },
        {
            "text": "Un cliente se molesta porque su pedido llegó con un error. ¿Cómo respondes?",
            "options": [
                ("Le explico que el error no fue mío", 1, "Aclara los hechos, pero no atiende la molestia ni propone una solución."),
                ("Lo escucho sin interrumpir, reconozco el problema y le propongo una solución concreta", 2, "Escucha, reconoce y propone un siguiente paso."),
                ("Le pido que se calme y espere", 0, "Minimiza la molestia y no ofrece solución."),
                ("Lo escucho y, si no puedo resolverlo yo, consulto de inmediato con quien sí puede y le informo el siguiente paso", 2, "Escucha, reconoce el límite de su alcance, pide apoyo y comunica lo que sigue."),
            ],
            "justification": "Se puntúan escucha, reconocimiento del problema y comunicación del siguiente paso, ya sea resolviendo o pidiendo apoyo.",
            "bias": "Supone experiencia previa de atención a clientes; la respuesta esperada puede variar según el entorno.",
        },
        {
            "text": "Por tercera vez este mes, un compañero te pide que le hagas su tarea. ¿Qué haces?",
            "options": [
                ("Acepto para evitar problemas", 0, "Evita el conflicto sin comunicar su límite."),
                ("Le digo que no, sin más explicaciones", 1, "Establece el límite, pero sin explicar el motivo ni ofrecer una alternativa."),
                ("Dejo de hablarle", 0, "Evita la comunicación y deteriora la relación."),
                ("Le digo con respeto que esta vez no puedo, le explico mi motivo y le ofrezco ayudarlo a entender el tema", 2, "Comunica su límite con respeto y propone una alternativa."),
            ],
            "justification": "Incluye una situación donde poner un límite es lo apropiado, para no premiar automáticamente evitar el conflicto.",
            "bias": "Depende de la cultura del grupo escolar y de la relación con el compañero.",
        },
    ],
    "ORG": [
        {
            "text": "Tienes tres tareas: A dura 2 horas y vence en 3 horas; B dura 1 hora y vence en 1 hora; C dura 1 hora y vence en 5 horas. Si empiezas ahora y haces una a la vez, ¿qué orden permite cumplir todos los plazos?",
            "options": [("A, B, C", 0), ("B, A, C", 1), ("C, B, A", 0), ("A, C, B", 0)],
            "justification": "Solo B, A, C cumple: B termina en la hora 1 (plazo 1), A en la hora 3 (plazo 3) y C en la hora 4 (plazo 5). Verificado enumerando los 6 órdenes posibles.",
            "bias": "Ejercicio de planificación con datos completos; no depende de interpretaciones.",
        },
        {
            "text": "Tienes un examen en 3 días, un trabajo para entregar en 5 días y una actividad de voluntariado mañana. ¿Cómo organizas la semana?",
            "options": [
                ("Hago primero lo que me parece más fácil y luego veo qué pasa", 1, "Avanza, pero sin priorizar por fechas ni estimar tiempos."),
                ("Anoto las fechas, estimo el tiempo de cada cosa, reparto el estudio en bloques diarios y reservo tiempo para el trabajo y el voluntariado", 2, "Planifica con fechas y tiempos estimados."),
                ("Dejo cada cosa para el último día", 0, "No planifica."),
                ("Aviso con tiempo a quienes organizan el voluntariado que solo podré ayudar parte del tiempo, y dedico el resto a estudiar y avanzar el trabajo", 2, "Prioriza con realismo y comunica el ajuste."),
            ],
            "justification": "Se puntúan la priorización y la planificación; hay más de una estrategia razonable.",
            "bias": "Supone disponibilidad de tiempo propia; no considera obligaciones familiares o laborales.",
        },
        {
            "text": "Un proyecto necesita 24 horas de trabajo. Si trabajas 3 horas por día, de lunes a viernes, ¿en cuántas semanas (de lunes a viernes) quedará terminado?",
            "options": [("1", 0), ("2", 1), ("3", 0), ("4", 0)],
            "justification": "15 horas por semana: 24 / 15 = 1.6, por lo que se completa durante la segunda semana.",
            "bias": "Se aclaró «de lunes a viernes» para evitar interpretaciones distintas de las fechas.",
        },
    ],
    "TEC": [
        {
            "text": "Un engranaje de 20 dientes mueve a otro de 40 dientes. Si el primero da 10 vueltas, ¿cuántas vueltas da el segundo?",
            "options": [("5", 1), ("10", 0), ("20", 0), ("40", 0)],
            "justification": "20 dientes × 10 vueltas = 200 dientes avanzan; 200 / 40 = 5 vueltas.",
            "bias": "Razonamiento mecánico; puede favorecer a quienes han visto engranajes, aunque se resuelve con proporciones.",
        },
        {
            "text": "Un foco no enciende. Ya comprobaste que el foco funciona y que el interruptor está en buen estado. ¿Qué revisas ahora?",
            "options": [
                ("Cambiar el interruptor por uno nuevo", 0),
                ("Comprar otro foco", 0),
                ("Si llega corriente al portalámparas y si las conexiones están firmes", 1),
                ("Cambiar todo el cableado de la casa", 0),
            ],
            "justification": "Diagnóstico: descartados foco e interruptor, lo lógico es revisar el siguiente elemento del circuito.",
            "bias": "Puede favorecer a quien ha visto instalaciones eléctricas; se resuelve por eliminación de causas.",
        },
        {
            "text": "Una bomba de agua que ayer funcionaba hoy no arranca. ¿Cuál es la forma más ordenada de encontrar la falla?",
            "options": [
                ("Revisar uno por uno los elementos, empezando por lo más simple (energía, llaves abiertas, conexiones), y anotar lo que se descarta", 1),
                ("Desarmar toda la bomba de inmediato", 0),
                ("Comprar una bomba nueva", 0),
                ("Esperar a ver si arranca sola", 0),
            ],
            "justification": "Diagnóstico sistemático: de lo simple a lo complejo, descartando causas. No requiere conocimientos de bombas.",
            "bias": "Problema cotidiano que no exige conocimientos eléctricos ni mecánicos específicos.",
        },
    ],
}

INTEREST_ORDER = ["CIE", "TEC", "SOC", "ART", "ADM", "PRA", "COM"]
SKILL_ORDER = ["LOG", "NUM", "VER", "CRE", "SOC", "ORG", "TEC"]


def _options(raw):
    """Normaliza a (texto, puntos, criterio)."""
    return [(o + ("",))[:3] for o in raw]


def build_questions():
    """
    Devuelve la lista de preguntas con su orden de presentación. Las preguntas se
    mezclan entre dimensiones (CIE-1, TEC-1, SOC-1, ... CIE-2, ...) para que el
    estudiante no vea bloques por dimensión.
    """
    questions = []

    order = 0
    for index in range(4):
        for key in INTEREST_ORDER:
            order += 1
            questions.append(
                {
                    "code": f"I-{key}-{index + 1}",
                    "section": "INTERESTS",
                    "kind": "LIKERT",
                    "order": order,
                    "text": INTEREST_ITEMS[key][index],
                    "passage": "",
                    "justification": LIKERT_JUSTIFICATION,
                    "bias_notes": LIKERT_BIAS,
                    "dimension": f"INT-{key}",
                    "options": _options(LIKERT_OPTIONS),
                }
            )

    order = 0
    for index in range(3):
        for key in SKILL_ORDER:
            order += 1
            item = SKILL_ITEMS[key][index]
            questions.append(
                {
                    "code": f"S-{key}-{index + 1}",
                    "section": "SKILLS",
                    "kind": "CHOICE",
                    "order": order,
                    "text": item["text"],
                    "passage": item.get("passage", ""),
                    "justification": item["justification"],
                    "bias_notes": item["bias"],
                    "dimension": f"HAB-{key}",
                    "options": _options(item["options"]),
                }
            )
    return questions