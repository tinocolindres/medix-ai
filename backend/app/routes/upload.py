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
print("UPLOAD_PY_V2_LOADED", flush=True)
MAX_FILE_SIZE_MB = 10

async def upload_to_s3(file_data, file_name, media_type):
    try:
        import boto3
        s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION)
        key = f"scans/{uuid.uuid4()}/{file_name}"
        s3.put_object(Bucket=settings.S3_BUCKET_MEDSCAN, Key=key, Body=file_data, ContentType=media_type)
        return f"https://{settings.S3_BUCKET_MEDSCAN}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except Exception:
        return f"local://{file_name}"

@router.post("/scan", response_model=ScanResponse, status_code=201)
async def upload_scan(file: UploadFile = File(...), scan_type: str = Form(default="other"), patient_context: str = Form(default=None), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    scan_limits = {"free": 20, "pro": settings.RATE_LIMIT_PRO_SCAN, "clinical": settings.RATE_LIMIT_CLINICAL_SCAN}
    limit = scan_limits.get(current_user.subscription_tier, 20)
    if current_user.scan_count_today >= limit:
        raise HTTPException(status_code=429, detail=f"Limite de {limit} scans diarios alcanzado.")
    raw_ct = file.content_type or ""
    if "png" in raw_ct:
        media_type = "image/png"
    elif "webp" in raw_ct:
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"
    file_data = await file.read()
    if len(file_data) / (1024 * 1024) > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"Archivo demasiado grande.")
    file_url = await upload_to_s3(file_data, file.filename or "scan.jpg", media_type)
    scan = MedicalScan(user_id=current_user.id, file_url=file_url, file_name=file.filename, scan_type=scan_type, is_processed=False)
    db.add(scan)
    await db.flush()
    try:
        analysis = await analyze_medical_image(image_data=file_data, media_type=media_type, scan_type=scan_type, user_context=patient_context)
        scan.ai_summary = analysis.get("summary")
        scan.ai_findings = analysis.get("findings")
        scan.ai_recommendations = analysis.get("recommendations")
        scan.urgency_level = analysis.get("urgency_level", "low")
        scan.confidence_score = analysis.get("confidence_score", 0.8)
        scan.is_processed = True
        scan.processing_time_ms = analysis.get("processing_time_ms")
    except Exception as e:
        scan.processing_error = str(e)
        raise HTTPException(status_code=500, detail=f"Error en analisis: {str(e)}")
    current_user.scan_count_today += 1
    await db.flush()
    return ScanResponse(scan_id=scan.id, summary=scan.ai_summary or "", findings=scan.ai_findings or "", recommendations=scan.ai_recommendations or "", urgency_level=scan.urgency_level or "low", confidence_score=scan.confidence_score or 0.8, processing_time_ms=scan.processing_time_ms or 0.0)
