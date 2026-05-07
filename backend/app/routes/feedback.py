from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.models.analytics import UserFeedback
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()


class FeedbackPayload(BaseModel):
    rating: int          # 1–5
    module: Optional[str] = None
    message: Optional[str] = None
    app_version: Optional[str] = None


@router.post("/feedback", status_code=201)
async def submit_feedback(
    payload: FeedbackPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Recibe feedback in-app de un usuario beta."""
    if not 1 <= payload.rating <= 5:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Rating debe ser entre 1 y 5.")

    fb = UserFeedback(
        user_id=current_user.id,
        rating=payload.rating,
        module=payload.module,
        message=payload.message,
        app_version=payload.app_version,
    )
    db.add(fb)
    await db.flush()
    return {"status": "ok", "feedback_id": fb.id, "message": "¡Gracias por tu feedback!"}


@router.post("/feedback/fcm-token")
async def register_fcm_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Registra el FCM token del dispositivo para push notifications."""
    current_user.fcm_token = token
    await db.flush()
    return {"status": "ok"}