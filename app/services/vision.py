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


VISION_SYSTEM_PROMPT = """Eres Medix AI Vision, un analizador de imágenes médicas de alta precisión.
Analizas imágenes clínicas y generas reportes estructurados para médicos y estudiantes en Honduras.

REGLAS ESTRICTAS:
1. Sé objetivo y científico. Usa terminología médica formal.
2. Para imágenes de diagnóstico (RX, ECG, ultrasonido): describe hallazgos, NO diagnostiques definitivamente.
3. Para recetas médicas: extrae medicamentos, dosis y frecuencia.
4. Para resultados de laboratorio: identifica valores y marca los fuera de rango.
5. Si la imagen NO es médica, responde: {"error": "Imagen no médica detectada"}.
6. Siempre incluye nivel de urgencia: low/medium/high/critical.
7. Responde ÚNICAMENTE en JSON válido según el schema solicitado.
"""


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
            "Analiza esta RECETA MÉDICA. Extrae: "
            "1) Lista de medicamentos con dosis y frecuencia, "
            "2) Diagnóstico si aparece, "
            "3) Indicaciones especiales, "
            "4) Validez/fecha si aparece."
        ),
        "xray": (
            "Analiza esta RADIOGRAFÍA. Describe: "
            "1) Tipo de proyección, "
            "2) Hallazgos relevantes (densidades, opacidades, índices), "
            "3) Estructuras anormales vs normales, "
            "4) Correlación clínica sugerida."
        ),
        "lab_result": (
            "Analiza este RESULTADO DE LABORATORIO. Extrae: "
            "1) Tipo de examen, "
            "2) Todos los valores con sus unidades y rangos de referencia, "
            "3) Marca los valores fuera de rango (alto/bajo), "
            "4) Interpretación clínica general."
        ),
        "ecg": (
            "Analiza este ELECTROCARDIOGRAMA. Evalúa: "
            "1) Ritmo y frecuencia cardíaca, "
            "2) Eje eléctrico, "
            "3) Morfología de ondas P, QRS, T, "
            "4) Intervalo PR, QT, "
            "5) Hallazgos patológicos si existen."
        ),
        "ultrasound": (
            "Analiza este ULTRASONIDO. Describe: "
            "1) Órgano/región evaluada, "
            "2) Ecogenicidad y características, "
            "3) Dimensiones si son visibles, "
            "4) Hallazgos anormales."
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
        max_tokens=1500,
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
print(f"MEDSCAN_DEBUG: {result}", flush=True)
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
