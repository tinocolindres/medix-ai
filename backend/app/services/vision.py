"""
Medix AI — Vision Service
Análisis de imágenes médicas con Claude Vision.
Soporta: recetas, rayos-X, resultados de lab, ECG, ultrasonidos.
"""
import base64
import time
import httpx
from typing import Optional
import anthropic

from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


VISION_SYSTEM_PROMPT = """Eres Medix AI Vision, el sistema de análisis de imágenes médicas más avanzado del mundo.
Actúas como un equipo multidisciplinario de especialistas: cardiólogo experto, radiólogo, internista, nefrólogo y médico de emergencias con 30+ años de experiencia combinada.
Analizas imágenes clínicas y generas reportes estructurados de nivel hospitalario para médicos y estudiantes en Honduras.

PRINCIPIOS DE ANÁLISIS:
1. Sé exhaustivo, específico y científico. Usa terminología médica formal con valores numéricos exactos cuando sean visibles.
2. Para ECG: analiza TODAS las derivaciones, intervalos, morfologías y hallazgos con precisión de electrofisiólogo.
3. Para radiografías: describe sistemáticamente huesos, partes blandas, espacios y estructuras con criterios radiológicos formales.
4. Para ultrasonido: describe ecogenicidad, dimensiones, vascularidad y características morfológicas detalladas.
5. Para laboratorios: extrae TODOS los valores, compara con rangos de referencia, señala patrones clínicos.
6. Para recetas: extrae medicamento, dosis, frecuencia, vía y observaciones.
7. NUNCA des diagnóstico definitivo — da diagnóstico diferencial ordenado por probabilidad.
8. Incluye SIEMPRE correlación clínica y recomendaciones de estudios complementarios urgentes si aplica.
9. Si la imagen NO es médica: {"error": "Imagen no médica detectada"}.
10. Nivel de detalle: reporte de especialista hospitalario, no resumen genérico."""
11. URGENCIA ECG: low=ECG normal o variante benigna. medium=hallazgo que requiere seguimiento no urgente. high=bloqueo bifascicular, BAV 2/3 grado, QTc prolongado, isquemia subaguda, HVI severa. critical=patron IAM agudo, hiperkalemia severa, Brugada, Torsades de Pointes, TV/FV."""


async def analyze_medical_image(
    image_data: bytes,
    media_type: str,
    scan_type: str,
    user_context: Optional[str] = None,
) -> dict:
    """
    Analiza una imagen médica con Claude Vision.
    
    Args:
        image_data: bytes de la imagen
        media_type: "image/jpeg" | "image/png" | "image/webp"
        scan_type: "prescription" | "xray" | "lab_result" | "ecg" | "ultrasound" | "other"
        user_context: contexto adicional del usuario (ej: "Paciente masculino 40 años")
    
    Returns:
        dict con summary, findings, recommendations, urgency_level, confidence_score
    """
    start_time = time.time()

    image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

    # Prompt específico por tipo de imagen
    type_prompts = {
        "prescription": (
          "prescription": (
    "Eres el mejor farmacologo clinico del mundo. Analiza esta RECETA MEDICA:\n"
    "1) MEDICAMENTOS: Nombre generico y comercial, dosis exacta, frecuencia, via, duracion.\n"
    "2) DIAGNOSTICO: Si aparece con CIE-10 inferible.\n"
    "3) INTERACCIONES: Entre medicamentos prescritos.\n"
    "4) ALERTAS: Dosis inusuales, medicamentos alto riesgo, contraindicaciones.\n"
    "5) INDICACIONES: Con/sin alimentos, horario, almacenamiento.\n"
    "6) DATOS: Medico, fecha, validez.\n"
    "7) GENERICOS SESAL: Alternativas en Cuadro Basico Honduras."
),
       "xray": (
    "Eres el mejor radiólogo del mundo con 30 años de experiencia. Analiza esta RADIOGRAFÍA con criterios radiológicos formales:\n"
    "1) TÉCNICA: Proyección (PA, AP, lateral, oblicua), calidad técnica, penetración, rotación.\n"
    "2) ESTRUCTURAS ÓSEAS: Huesos visibles, densidad, cortical, trabéculas, fracturas, lesiones líticas/blásticas.\n"
    "3) PARTES BLANDAS: Tejidos blandos, calcificaciones, masas, edema.\n"
    "4) HALLAZGOS ESPECÍFICOS POR REGIÓN:\n"
    "   - Tórax: ICT, silueta cardíaca, hilios, campos pulmonares, pleura, mediastino, diafragma, senos costofrénicos.\n"
    "   - Abdomen: distribución de gas, niveles hidroaéreos, calcificaciones, órganos sólidos.\n"
    "   - Extremidades: alineación, fracturas, articulaciones, densidad ósea.\n"
    "5) COMPARACIÓN: Con parámetros normales para edad y sexo si inferibles.\n"
    "6) DIAGNÓSTICO DIFERENCIAL: Ordenado por probabilidad con justificación radiológica.\n"
    "7) RECOMENDACIONES: Estudios complementarios (TC, RM, gammagrafía), correlación clínica urgente si aplica."
),
      "lab_result": (
    "Eres el mejor internista y patologo clinico del mundo. Analiza este RESULTADO DE LABORATORIO:\n"
    "1) TIPO DE EXAMEN: Identifica todos los paneles y pruebas presentes.\n"
    "2) VALORES COMPLETOS: Cada valor con unidad y rango de referencia del laboratorio.\n"
    "3) VALORES ALTERADOS: Marca claramente valores ALTOS y BAJOS con magnitud de desviacion.\n"
    "4) INTERPRETACION POR SISTEMA: Hematologia (anemia, leucocitosis), quimica (renal, hepatica, glucemia, electrolitos), lipidos (riesgo CV), inflamacion (PCR, VSG).\n"
    "5) PATRONES DIAGNOSTICOS: Sindrome nefrotico, hepatitis, DM, sepsis, etc.\n"
    "6) VALORES DE PANICO: K+>6.5, glucosa>500, Cr>10 — accion inmediata.\n"
    "7) DIAGNOSTICO DIFERENCIAL: Basado en conjunto de alteraciones.\n"
    "8) RECOMENDACIONES: Estudios complementarios, repeticion de valores urgentes."
),
        "ecg": (
    "Eres el mejor cardiologo y electrofisiologo del mundo con 30 anos de experiencia interpretando ECGs. "
    "Analiza este ELECTROCARDIOGRAMA con la profundidad y precision de un cardiologo experto. "
    "Evalua OBLIGATORIAMENTE cada punto:\n"
    "1) RITMO: Sinusal/FA/flutter/TSV/marcapasos. Frecuencia ventricular y auricular exacta en lpm.\n"
    "2) EJE ELECTRICO: Normal/izquierda/derecha/indeterminado. Grados aproximados.\n"
    "3) ONDAS P: Presencia, morfologia, duracion, amplitud. P mitrale, P pulmonale, ausencia.\n"
    "4) INTERVALO PR: Duracion en ms. Bloqueo AV 1/2/3 grado - Mobitz I o II si aplica.\n"
    "5) QRS: Duracion ms. BRD o BRI completo/incompleto. Hemibloqueos. Onda Q patologica con derivaciones afectadas. Criterios HVI/HVD Sokolow-Lyon y Cornell.\n"
    "6) SEGMENTO ST: Elevacion o depresion por derivacion en mm. Patron lesion/isquemia/pericarditis.\n"
    "7) ONDA T: Hiperagudas simetricas (hiperkalemia o IAM hiperagudo). Inversion por derivacion. Ondas T picudas.\n"
    "8) QT/QTc: Duracion corregida en ms. Prolongado con riesgo Torsades de Pointes.\n"
    "9) ONDA U: Prominente en hipokalemia.\n"
    "10) HALLAZGOS ESPECIALES: WPW, Brugada, hiperkalemia, hipokalemia, efecto digitalis, strain, repolarizacion precoz.\n"
    "11) CORRELACION CLINICA: Diferencial ordenado por probabilidad. Urgencia. Estudios urgentes recomendados.\n"
    "12) IMPRESION DIAGNOSTICA FINAL: Interpretacion global clara y directa como cardiologo experto.\n"
    "Se MUY especifico: menciona derivaciones exactas, valores numericos visibles, no omitas ningun hallazgo sutil."
),
      "ultrasound": (
    "Eres el mejor ecografista y radiólogo del mundo especializado en ultrasonido. Analiza esta ECOGRAFÍA con criterios formales:\n"
    "1) TÉCNICA: Tipo de transductor, ventana acústica, calidad de imagen.\n"
    "2) ÓRGANO/REGIÓN EVALUADA: Identifica claramente qué estructura se visualiza.\n"
    "3) MEDIDAS: Todas las dimensiones visibles en mm/cm con comparación con valores normales.\n"
    "4) ECOGENICIDAD: Hiper/hipo/anecoico, homogéneo/heterogéneo, comparación con órganos de referencia.\n"
    "5) MORFOLOGÍA: Contornos, forma, márgenes (regulares/irregulares/lobulados).\n"
    "6) LESIONES FOCALES: Número, tamaño, localización, características (sólida/quística/mixta), vascularidad al Doppler si visible.\n"
    "7) ESTRUCTURAS ADYACENTES: Ganglios, vasos, líquido libre, otras estructuras involucradas.\n"
    "8) HALLAZGOS DOPPLER: Flujo, índices de resistencia, vascularidad si aplica.\n"
    "9) DIAGNÓSTICO DIFERENCIAL: Ordenado por probabilidad con justificación ecográfica.\n"
    "10) RECOMENDACIONES: Seguimiento ecográfico, estudios complementarios (TC, RM, biopsia), urgencia."
),
        "other": (
            "Analiza esta imagen médica y describe todos los hallazgos relevantes."
        ),
    }

    context_addition = f"\n\nCONTEXTO DEL PACIENTE: {user_context}" if user_context else ""

    user_prompt = f"""{type_prompts.get(scan_type, type_prompts['other'])}{context_addition}

Responde ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "summary": "Resumen ejecutivo en 2-3 oraciones",
  "findings": "Hallazgos detallados en formato de lista Markdown",
  "recommendations": "Recomendaciones clínicas (no diagnóstico definitivo)",
  "urgency_level": "low|medium|high|critical",
  "confidence_score": 0.0-1.0,
  "extracted_data": {{}}
}}"""

    response = await client.messages.create(
        model=settings.CLAUDE_VISION_MODEL,
        max_tokens=3000,
        temperature=0,
        system=VISION_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": user_prompt},
            ],
        }],
    )

    elapsed_ms = (time.time() - start_time) * 1000

    # Parse JSON response
    import json
    try:
        raw_text = response.content[0].text.strip()
        # Limpiar posibles backticks de markdown
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        result = json.loads(raw_text)
    except (json.JSONDecodeError, IndexError):
        result = {
            "summary": response.content[0].text[:500],
            "findings": "Error parseando respuesta estructurada.",
            "recommendations": "Revise la imagen manualmente.",
            "urgency_level": "medium",
            "confidence_score": 0.5,
            "extracted_data": {},
        }

    result["processing_time_ms"] = elapsed_ms
    result["tokens_used"] = response.usage.input_tokens + response.usage.output_tokens
    return result


async def analyze_image_from_url(url: str, scan_type: str, user_context: str = None) -> dict:
    """Descarga imagen desde URL (S3) y la analiza."""
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(url, timeout=30.0)
        resp.raise_for_status()
        image_data = resp.content
        content_type = resp.headers.get("content-type", "image/jpeg")
        # Normalizar content-type
        if "jpeg" in content_type or "jpg" in content_type:
            media_type = "image/jpeg"
        elif "png" in content_type:
            media_type = "image/png"
        elif "webp" in content_type:
            media_type = "image/webp"
        else:
            media_type = "image/jpeg"

    return await analyze_medical_image(image_data, media_type, scan_type, user_context)
