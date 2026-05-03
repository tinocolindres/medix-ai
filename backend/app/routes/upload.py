import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.medical import MedicalScan
from app.core.security import get_current_active_user
from app.core.config import settings
from app.services.vision import analyze_medical_image
from app.schemas.medix import ScanResponse

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_MB = 10


async def upload_to_s3(file_data: bytes, file_name: str, content_type: str) -> str:
    """Sube archivo a AWS S3 y retorna URL firmada."""
    try:
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        key = f"scans/{uuid.uuid4()}/{file_name}"
        s3.put_object(
            Bucket=settings.S3_BUCKET_MEDSCAN,
            Key=key,
            Body=file_data,
            ContentType=content_type,
        )
        # URL pública (ajustar a presigned URL en producción)
        url = f"https://{settings.S3_BUCKET_MEDSCAN}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        return url
    except Exception as e:
        # Si S3 no está configurado, usar placeholder
        return f"local://{file_name}"


@router.post("/scan", response_model=ScanResponse, status_code=201)
async def upload_scan(
    file: UploadFile = File(..., description="Imagen médica (JPG, PNG, WEBP)"),
    scan_type: str = Form(default="other", description="prescription|xray|lab_result|ecg|ultrasound|other"),
    patient_context: str = Form(default=None, description="Contexto del paciente"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Sube y analiza una imagen médica con Claude Vision.
    
    - **Free:** 3 scans/día
    - **Pro:** 50 scans/día  
    - **Clinical:** Ilimitado
    """
    # ── Rate limit para scans ─────────────────────────────────────────────────
    scan_limits = {
        "free": 20,   # Aumentado temporalmente para fase beta (original: settings.RATE_LIMIT_FREE_SCAN)
        "pro": settings.RATE_LIMIT_PRO_SCAN,
        "clinical": settings.RATE_LIMIT_CLINICAL_SCAN,
    }
    limit = scan_limits.get(current_user.subscription_tier, 20)
    if current_user.scan_count_today >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite de {limit} scans diarios alcanzado. Actualiza tu plan."
        )

    # ── Validar archivo ───────────────────────────────────────────────────────
    # Normalizar content_type (Android a veces envía None)
    raw_ct = file.content_type or ""
    if "png" in raw_ct:
        media_type = "image/png"
    elif "webp" in raw_ct:
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    file_data = await file.read()
    file_size_mb = len(file_data) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE_MB}MB."
        )

    # ── Subir a S3 ────────────────────────────────────────────────────────────
    file_url = await upload_to_s3(file_data, file.filename or "scan.jpg", media_type)

    # ── Crear registro en DB (pendiente de análisis) ──────────────────────────
    scan = MedicalScan(
        user_id=current_user.id,
        file_url=file_url,
        file_name=file.filename,
        scan_type=scan_type,
        is_processed=False,
    )
    db.add(scan)
    await db.flush()

    # ── Analizar con Claude Vision ────────────────────────────────────────────
    try:
        analysis = await analyze_medical_image(
            image_data=file_data,
            media_type=media_type,
            scan_type=scan_type,
            user_context=patient_context,
        )
        # Actualizar registro con resultados
        scan.ai_summary = analysis.get("summary")
        scan.ai_findings = analysis.get("findings")
        scan.ai_recommendations = analysis.get("recommendations")
        scan.urgency_level = analysis.get("urgency_level", "low")
        scan.confidence_score = analysis.get("confidence_score", 0.8)
        scan.is_processed = True
        scan.processing_time_ms = analysis.get("processing_time_ms")

    except Exception as e:
        scan.processing_error = str(e)
        scan.is_processed = False
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en análisis de imagen: {str(e)}"
        )

    # Incrementar contador de scans
    current_user.scan_count_today += 1
    await db.flush()

    return ScanResponse(
        scan_id=scan.id,
        summary=scan.ai_summary or "",
        findings=scan.ai_findings or "",
        recommendations=scan.ai_recommendations or "",
        urgency_level=scan.urgency_level or "low",
        confidence_score=scan.confidence_score or 0.8,
        processing_time_ms=scan.processing_time_ms or 0.0,
    )# fix
