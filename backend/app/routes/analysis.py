from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.user import User
from app.models.medical import ChatSession, ChatMessage
from app.models.curriculum import Subject, CurriculumPeriod, University
from app.core.security import get_current_active_user
from app.core.config import settings
from app.services import llm as llm_service
from app.services import sesal_rag
from app.schemas.medix import (
    ChatMessageRequest, ChatMessageResponse,
    SOAPRequest, SOAPResponse,
    ECOEStartRequest, ECOEResponse,
    SESALQueryRequest, SESALQueryResponse,
)

router = APIRouter()


def _check_rate_limit(user: User) -> None:
    """Verifica que el usuario no haya excedido su límite de mensajes hoy."""
    limits = {
        "free": settings.RATE_LIMIT_FREE_CHAT,
        "pro": settings.RATE_LIMIT_PRO_CHAT,
        "clinical": settings.RATE_LIMIT_PRO_CHAT,
    }
    limit = limits.get(user.subscription_tier, settings.RATE_LIMIT_FREE_CHAT)
    if user.chat_count_today >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite diario alcanzado ({limit} mensajes). Actualiza tu plan para continuar.",
        )


@router.post("/chat", response_model=ChatMessageResponse)
async def chat(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Endpoint principal de Chat IA contextual."""
    _check_rate_limit(current_user)

    # ── Obtener o crear sesión ────────────────────────────────────────────────
    if payload.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == payload.session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
    else:
        session = ChatSession(
            user_id=current_user.id,
            title=payload.message[:60] + "..." if len(payload.message) > 60 else payload.message,
            context_subject_id=payload.subject_id,
            mode=payload.mode,
        )
        db.add(session)
        await db.flush()

    # ── Cargar historial de la sesión ─────────────────────────────────────────
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    history = [
        {"sender_type": m.sender_type, "message": m.message}
        for m in msg_result.scalars().all()
    ]

    # ── Obtener contexto curricular si aplica ─────────────────────────────────
    subject_name = None
    subject_ai_hint = None
    period_name = None
    university_acronym = None

    if payload.subject_id or current_user.current_period_id:
        subject_id = payload.subject_id or session.context_subject_id
        if subject_id:
            sub_result = await db.execute(select(Subject).where(Subject.id == subject_id))
            subject = sub_result.scalar_one_or_none()
            if subject:
                subject_name = subject.name
                subject_ai_hint = subject.ai_context_hint

        if current_user.current_period_id:
            period_result = await db.execute(
                select(CurriculumPeriod).where(CurriculumPeriod.id == current_user.current_period_id)
            )
            period = period_result.scalar_one_or_none()
            if period:
                period_name = period.period_name
                univ_result = await db.execute(
                    select(University).where(University.id == period.university_id)
                )
                univ = univ_result.scalar_one_or_none()
                if univ:
                    university_acronym = univ.acronym

    # ── Generar respuesta con Claude ──────────────────────────────────────────
    result = await llm_service.generate_chat_response(
        message=payload.message,
        chat_history=history,
        user_role=current_user.role,
        university_acronym=university_acronym,
        period_name=period_name,
        subject_name=subject_name,
        subject_ai_hint=subject_ai_hint,
        specialty=current_user.specialty,
        mode=payload.mode,
    )

    # ── Guardar mensajes ──────────────────────────────────────────────────────
    user_msg = ChatMessage(
        session_id=session.id,
        sender_type="user",
        message=payload.message,
    )
    ai_msg = ChatMessage(
        session_id=session.id,
        sender_type="ai",
        message=result["response"],
        tokens_used=str(result.get("tokens_output", 0)),
    )
    db.add(user_msg)
    db.add(ai_msg)

    # Incrementar contador de rate limit
    current_user.chat_count_today += 1
    await db.flush()

    return ChatMessageResponse(
        session_id=session.id,
        message_id=ai_msg.id,
        response=result["response"],
        tokens_used=result.get("tokens_output"),
        processing_time_ms=result.get("processing_time_ms"),
    )


@router.post("/soap", response_model=SOAPResponse)
async def soap_dictation(
    payload: SOAPRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Transforma dictado de voz a nota SOAP estructurada."""
    # SOAP disponible para todos los planes durante fase beta
    _check_rate_limit(current_user)

    result = await llm_service.generate_soap_note(
        raw_dictation=payload.dictation,
        user_role=current_user.role,
    )
    return SOAPResponse(soap_note=result["soap_note"], tokens_used=result["tokens_used"])


@router.post("/ecoe/start", response_model=ECOEResponse)
async def start_ecoe(
    payload: ECOEStartRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Inicia simulación de paciente virtual para práctica ECOE/OSCE."""
    result = await llm_service.start_ecoe_simulation(case_id=payload.case_id)
    return ECOEResponse(
        case_id=result["case_id"],
        patient_opening=result["patient_opening"],
    )


@router.post("/sesal", response_model=SESALQueryResponse)
async def query_sesal(
    payload: SESALQueryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Consulta protocolos clínicos oficiales de la SESAL Honduras."""
    result = await sesal_rag.generate_sesal_response(
        query=payload.query,
        user_role=current_user.role,
    )
    return SESALQueryResponse(
        response=result["response"],
        source=result["source"],
        chunks_used=result["chunks_used"],
    )
