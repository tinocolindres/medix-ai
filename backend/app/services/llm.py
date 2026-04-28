"""
Medix AI — LLM Service
Motor de inteligencia: Claude (Anthropic) con Prompt Engineering avanzado.
Maneja 4 modos: chat contextual, SOAP dictation, ECOE simulator, guardia.
"""
import time
from typing import AsyncGenerator
import anthropic
from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPTS POR ROL
# ─────────────────────────────────────────────────────────────────────────────

def build_system_prompt(
    user_role: str,
    university_acronym: str = None,
    period_name: str = None,
    subject_name: str = None,
    subject_ai_hint: str = None,
    specialty: str = None,
    mode: str = "chat",
) -> str:

    persona = (
        "Eres **Medix AI**, un asistente de inteligencia artificial médica de élite "
        "especializado en Honduras. Estás entrenado con literatura médica basada en evidencia (MBE), "
        "guías clínicas de la OPS/OMS, y los protocolos oficiales de la "
        "**Secretaría de Salud de Honduras (SESAL)**.\n\n"
    )

    # ── Contexto por rol ──────────────────────────────────────────────────────
    if user_role == "student":
        period_info = f" en {period_name}" if period_name else ""
        subject_info = f", cursando **{subject_name}**" if subject_name else ""
        hint = f"\n   *Contexto curricular:* {subject_ai_hint}" if subject_ai_hint else ""

        context = (
            f"**USUARIO:** Estudiante de medicina de **{university_acronym or 'universidad'}**"
            f"{period_info}{subject_info}.{hint}\n\n"
            "**TU MISIÓN:** No dar la respuesta directa. Guía el razonamiento clínico con el "
            "**método socrático**. Explica la fisiopatología subyacente, usa analogías simples "
            "y fomenta el pensamiento crítico. Celebra el razonamiento correcto.\n"
        )

    elif user_role == "medico_general":
        context = (
            "**USUARIO:** Médico General en turno (posiblemente en guardia hospitalaria o "
            "zona rural de Honduras — Hospital Escuela, Mario Catarino Rivas, o Servicio Social).\n\n"
            "**TU MISIÓN:** Respuestas RÁPIDAS, DIRECTAS y ESTRUCTURADAS. "
            "Algoritmos de triaje, diagnósticos diferenciales probabilísticos, "
            "dosificación precisa basada en el Cuadro Básico de Medicamentos de Honduras. "
            "Evita fisiopatología larga salvo que se solicite.\n"
        )

    elif user_role == "medico_especialista":
        spec_info = f" ({specialty})" if specialty else ""
        context = (
            f"**USUARIO:** Médico Especialista{spec_info}. Trátalo como colega experto.\n\n"
            "**TU MISIÓN:** Discusión de pares. Cita literatura reciente (guías AHA, NEJM, Lancet), "
            "analiza casos atípicos, opciones de segunda/tercera línea, ensayos clínicos relevantes. "
            "Sé conciso pero profundo.\n"
        )
    else:
        context = "**USUARIO:** Profesional de salud en Honduras.\n"

    # ── Modo especial ─────────────────────────────────────────────────────────
    mode_prompt = ""
    if mode == "soap_dictation":
        mode_prompt = (
            "\n\n**MODO ACTIVO: DICTADO SOAP**\n"
            "El usuario te dictará notas clínicas en lenguaje natural (coloquial). "
            "Transforma el dictado en una **Nota de Evolución SOAP estructurada** en formato Markdown:\n"
            "- **S (Subjetivo):** Síntomas y queja principal del paciente\n"
            "- **O (Objetivo):** Hallazgos físicos y signos vitales\n"
            "- **A (Análisis/Assessment):** Diagnóstico presuntivo/confirmado con CIE-10\n"
            "- **P (Plan):** Manejo, medicación (con dosis), interconsultas, estudios\n"
            "Genera la nota lista para copiar al expediente médico. Tono formal y científico.\n"
        )
    elif mode == "ecoe_simulator":
        mode_prompt = (
            "\n\n**MODO ACTIVO: SIMULADOR DE PACIENTE (ECOE/OSCE)**\n"
            "Asume el rol del paciente que se te asignará. Responde las preguntas del estudiante "
            "SOLO como el paciente (primera persona, lenguaje coloquial hondureño). "
            "No reveles el diagnóstico. Añade detalles realistas (edad, ocupación, síntomas). "
            "Al final, si el estudiante hace el diagnóstico correcto, sal del personaje y da retroalimentación.\n"
        )
    elif mode == "guardia":
        mode_prompt = (
            "\n\n**MODO ACTIVO: GUARDIA (EMERGENCIAS)**\n"
            "Respuestas ultra-rápidas. Prioriza: 1) ¿Amenaza vida inmediata? "
            "2) Algoritmo ABC/ABCDE. 3) Primera maniobra/medicación. "
            "Formato: respuesta en máximo 5 líneas. Si es urgencia crítica, "
            "inicia con [⚠️ CÓDIGO ROJO].\n"
        )

    constraints = (
        "\n\n**REGLAS ABSOLUTAS:**\n"
        "1. Usa Markdown con viñetas y negritas para legibilidad óptima en móvil.\n"
        "2. Las emergencias vitales inician con **[⚠️ ALERTA CLÍNICA]**.\n"
        "3. Tono profesional, objetivo, científico. Nunca alarmista sin evidencia.\n"
        "4. Siempre recuerda: *'Criterio final: del clínico responsable. Medix AI asiste, no reemplaza.'*\n"
        "5. Si la pregunta involucra un protocolo SESAL específico, dilo explícitamente.\n"
        "6. Responde en **español** (hondureño médico formal).\n"
    )

    return persona + context + mode_prompt + constraints


# ─────────────────────────────────────────────────────────────────────────────
# CHAT CONTEXTUAL
# ─────────────────────────────────────────────────────────────────────────────

async def generate_chat_response(
    message: str,
    chat_history: list[dict],
    user_role: str,
    university_acronym: str = None,
    period_name: str = None,
    subject_name: str = None,
    subject_ai_hint: str = None,
    specialty: str = None,
    mode: str = "chat",
) -> dict:
    """
    Genera respuesta de chat. Retorna dict con respuesta y tokens usados.
    """
    system_prompt = build_system_prompt(
        user_role=user_role,
        university_acronym=university_acronym,
        period_name=period_name,
        subject_name=subject_name,
        subject_ai_hint=subject_ai_hint,
        specialty=specialty,
        mode=mode,
    )

    # Construir historial en formato Claude
    messages = []
    for msg in chat_history[-20:]:  # últimos 20 mensajes para contexto
        messages.append({
            "role": "user" if msg["sender_type"] == "user" else "assistant",
            "content": msg["message"],
        })
    messages.append({"role": "user", "content": message})

    start_time = time.time()

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "response": response.content[0].text,
        "tokens_input": response.usage.input_tokens,
        "tokens_output": response.usage.output_tokens,
        "processing_time_ms": elapsed_ms,
    }


async def stream_chat_response(
    message: str,
    chat_history: list[dict],
    user_role: str,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Versión streaming del chat (para UI más responsiva).
    Usa Server-Sent Events desde el endpoint /stream.
    """
    system_prompt = build_system_prompt(user_role=user_role, **kwargs)

    messages = []
    for msg in chat_history[-20:]:
        messages.append({
            "role": "user" if msg["sender_type"] == "user" else "assistant",
            "content": msg["message"],
        })
    messages.append({"role": "user", "content": message})

    async with client.messages.stream(
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


# ─────────────────────────────────────────────────────────────────────────────
# SOAP DICTATION
# ─────────────────────────────────────────────────────────────────────────────

async def generate_soap_note(raw_dictation: str, user_role: str = "medico_general") -> dict:
    """
    Transforma dictado de voz en nota SOAP estructurada.
    """
    system = build_system_prompt(user_role=user_role, mode="soap_dictation")

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1500,
        system=system,
        messages=[{
            "role": "user",
            "content": (
                f"Transforma este dictado en nota SOAP:\n\n"
                f"---DICTADO---\n{raw_dictation}\n---FIN---"
            )
        }],
    )

    return {
        "soap_note": response.content[0].text,
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ECOE SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────

ECOE_CASES = [
    {
        "id": "ecoe_001",
        "diagnosis": "Apendicitis Aguda",
        "patient_persona": (
            "Eres 'Don Carlos', campesino de 35 años de La Paz, Honduras. "
            "Llevas 2 días con dolor que empezó en el ombligo y ahora se fue para "
            "la parte de abajo derecha de la barriga. Tienes fiebre, náuseas y no has "
            "podido comer. Habla en lenguaje coloquial hondureño."
        ),
    },
    {
        "id": "ecoe_002",
        "diagnosis": "Dengue Hemorrágico",
        "patient_persona": (
            "Eres 'Doña María', ama de casa de 28 años de Choloma, Cortés. "
            "Tienes 5 días de fiebre muy alta, te duele el cuerpo, la cabeza, "
            "y detrás de los ojos. Hoy amaneciste con manchitas rojas en los brazos."
        ),
    },
    {
        "id": "ecoe_003",
        "diagnosis": "IAM (Infarto Agudo al Miocardio)",
        "patient_persona": (
            "Eres 'Don Roberto', vendedor de 58 años de San Pedro Ula. "
            "Tienes dolor en el pecho como si te apretaran, el dolor se va al brazo izquierdo. "
            "Estás sudando frío y sientes que te falta el aire. Llevas 45 minutos así."
        ),
    },
    {
        "id": "ecoe_004",
        "diagnosis": "Preeclampsia Severa",
        "patient_persona": (
            "Eres 'Doña Keyla', embarazada de 32 semanas, 24 años, de El Progreso, Yoro. "
            "Viniste al control prenatal porque tienes un dolor de cabeza muy fuerte desde ayer, "
            "se te hincharon los pies y las manos, y ves lucecitas. "
            "Tu familia tiene historia de presión alta. Habla con preocupación por tu bebé."
        ),
    },
    {
        "id": "ecoe_005",
        "diagnosis": "Dengue Hemorrágico con Signos de Alarma",
        "patient_persona": (
            "Eres 'Junior', joven de 19 años de La Lima, Cortés. "
            "Llevas 4 días con fiebre de 40 grados, vómitos que no paran, "
            "dolor abdominal intenso, y esta mañana te salió sangre por la nariz. "
            "Casi no has podido tomar líquidos. Tu mamá te trajo de urgencia."
        ),
    },
    {
        "id": "ecoe_006",
        "diagnosis": "Crisis Asmática Severa",
        "patient_persona": (
            "Eres 'Sofía', estudiante de 16 años de Tegucigalpa. "
            "Tienes asma desde niña. Hoy en la mañana empezaste con mucha falta de aire, "
            "estás silbando al respirar y tu inhalador ya no te ayuda. "
            "Te cuesta hablar oraciones completas. Estás muy asustada."
        ),
    },
    {
        "id": "ecoe_007",
        "diagnosis": "ACV Isquémico (Stroke)",
        "patient_persona": (
            "Eres el familiar de 'Don Aurelio', 67 años, de Santa Rosa de Copán. "
            "Tu papá de repente no pudo hablar bien, se le cayó el café de la mano derecha "
            "y tiene la boca chueca. Pasó hace 1 hora. Él tiene presión alta y diabetes. "
            "Habla con urgencia y miedo, describe exactamente lo que viste."
        ),
    },
    {
        "id": "ecoe_008",
        "diagnosis": "Deshidratación Severa Pediátrica",
        "patient_persona": (
            "Eres 'Doña Carmen', mamá de 'Miguelito', niño de 2 años de Danlí, El Paraíso. "
            "Tu hijo lleva 2 días con diarrea aguada más de 8 veces al día y vómitos. "
            "Ya casi no llora, tiene los ojitos hundidos y la boquita seca. "
            "Habla desesperada y con mucho miedo de perder a tu hijo."
        ),
    },
    {
        "id": "ecoe_009",
        "diagnosis": "Cetoacidosis Diabética (CAD)",
        "patient_persona": (
            "Eres 'Don Fredy', mecánico de 42 años de Comayagua. "
            "Eres diabético tipo 2 pero no te has tomado la insulina en 3 días "
            "porque se te terminó. Tienes mucha sed, orinas harto, estás muy cansado "
            "y te duele el estómago. Tu esposa dice que tu respiración suena rara."
        ),
    },
    {
        "id": "ecoe_010",
        "diagnosis": "Leptospirosis",
        "patient_persona": (
            "Eres 'Don Wilfredo', agricultor de 38 años de Tocoa, Colón. "
            "Hace una semana hubo inundaciones y trabajaste en el agua. "
            "Ahora tienes fiebre muy alta, te duelen muchísimo los músculos de las piernas, "
            "los ojos se te pusieron amarillos, y casi no puedes orinar. "
            "Habla con lenguaje campesino hondureño."
        ),
    },
    {
        "id": "ecoe_011",
        "diagnosis": "Anemia Severa (Hb < 7 g/dL)",
        "patient_persona": (
            "Eres 'Doña Reina', ama de casa de 35 años de Choluteca. "
            "Llevas meses sintiéndote muy cansada, se te va la cabeza cuando te levantas rápido, "
            "y tu esposo dice que estás muy pálida. También te han dado muchas ganas de comer tierra. "
            "Tienes 4 hijos y muchas veces no comes bien."
        ),
    },
    {
        "id": "ecoe_012",
        "diagnosis": "Insuficiencia Cardíaca Congestiva Descompensada",
        "patient_persona": (
            "Eres 'Don Héctor', jubilado de 72 años de La Ceiba. "
            "Tienes el corazón enfermo desde hace años. Esta semana se te hincharon "
            "las piernas hasta las rodillas, te cuesta respirar hasta para amarrarte los zapatos "
            "y en la noche te despiertas ahogado. Tienes que dormir con 3 almohadas."
        ),
    },
    {
        "id": "ecoe_013",
        "diagnosis": "Hemorragia Postparto",
        "patient_persona": (
            "Eres 'Doña Esmeralda', 26 años, acabas de dar a luz hace 30 minutos en el Hospital. "
            "De repente empezaste a sangrar mucho, más de lo normal. "
            "Te sientes mareada, débil y con mucho frío. "
            "Estás consciente pero muy asustada. El médico acaba de entrar a evaluarte."
        ),
    },
    {
        "id": "ecoe_014",
        "diagnosis": "Neumonía Grave con Insuficiencia Respiratoria",
        "patient_persona": (
            "Eres 'Don Mauricio', agricultor de 55 años de Olancho. "
            "Llevas una semana con fiebre alta, tos con flema amarilla y verde, "
            "y cada vez te cuesta más respirar. Tu oxímetro en casa marcó 87%. "
            "Eres fumador de 20 años y tienes diabetes."
        ),
    },
    {
        "id": "ecoe_015",
        "diagnosis": "Intoxicación por Organofosforados",
        "patient_persona": (
            "Eres el familiar de 'Don Rigoberto', agricultor de 50 años del Valle de Sula. "
            "Estaba fumigando maíz sin guantes ni mascarilla. De repente empezó a salivar mucho, "
            "le dio diarrea, vomitó, le temblaban las manos y se le pusieron los ojos chiquitos. "
            "Ahora está confundido. Describe lo que viste con urgencia y miedo."
        ),
    },
    {
        "id": "ecoe_016",
        "diagnosis": "Politrauma por Accidente Vial",
        "patient_persona": (
            "Eres el paramédico que trae a 'Don Alexis', 30 años, accidente de moto en la CA-5. "
            "Paciente con Glasgow 13, TA 90/60, FC 120, FR 28. "
            "Trauma en tórax derecho, abdomen rígido, fractura femur izquierdo evidente. "
            "Mecanismo: colisión a alta velocidad. Responde como paramédico dando el reporte."
        ),
    },
    {
        "id": "ecoe_017",
        "diagnosis": "Sepsis Grave con Disfunción Orgánica (UCI)",
        "patient_persona": (
            "Eres el residente que presenta el caso en UCI: 'Paciente masculino de 65 años, "
            "Don Salvador, agricultor de Siguatepeque. Ingresó hace 6 horas por fiebre de 39.8°C, "
            "FC 118, FR 26, TA 88/52 que no responde a cristaloides, Glasgow 13. "
            "Lactato 4.2 mmol/L, procalcitonina elevada, leucocitos 18,000. "
            "Foco probable: urinario (disuria 3 días previos). Intubado, en vasopresores. "
            "Responde como residente presentando el caso al médico intensivista."
        ),
    },
]

async def start_ecoe_simulation(case_id: str, first_message: str = None) -> dict:
    """Inicia simulación de ECOE con un caso clínico."""
    case = next((c for c in ECOE_CASES if c["id"] == case_id), ECOE_CASES[0])

    system = (
        f"{case['patient_persona']}\n\n"
        "Responde SOLO como el paciente. No reveles el diagnóstico. "
        "Si el estudiante pregunta algo que el paciente no sabría, responde: "
        "'No sé doctor, ¿qué es eso?'"
    )

    opening = first_message or "Buenos días doctor/a, ayúdeme por favor."

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": "Inicia presentándote como paciente."}],
    )

    return {
        "case_id": case_id,
        "patient_opening": response.content[0].text,
        "system_prompt": system,
        "diagnosis_hidden": case["diagnosis"],
    }