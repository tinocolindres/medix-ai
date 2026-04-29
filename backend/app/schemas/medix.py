from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = "student"
    university_id: Optional[str] = None
    current_period_id: Optional[str] = None
    specialty: Optional[str] = None
    residency_year: Optional[str] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    full_name: str
    subscription_tier: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    subscription_tier: str
    university_id: Optional[str]
    current_period_id: Optional[str]
    specialty: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None      # None = nueva sesión
    subject_id: Optional[str] = None      # Para contexto curricular
    mode: str = "chat"                     # chat | soap_dictation | ecoe_simulator | guardia


class ChatMessageResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    tokens_used: Optional[int]
    processing_time_ms: Optional[float]


class SOAPRequest(BaseModel):
    dictation: str
    patient_context: Optional[str] = None


class SOAPResponse(BaseModel):
    soap_note: str
    tokens_used: int


class ECOEStartRequest(BaseModel):
    case_id: str = "ecoe_001"


class ECOEResponse(BaseModel):
    case_id: str
    patient_opening: str
    session_id: Optional[str] = None
    instructions: str = "Interroga al paciente para llegar al diagnóstico"


# ─────────────────────────────────────────────────────────────────────────────
# MEDSCAN VISION
# ─────────────────────────────────────────────────────────────────────────────

class ScanResponse(BaseModel):
    scan_id: str
    summary: str
    findings: str
    recommendations: str
    urgency_level: str
    confidence_score: float
    processing_time_ms: float


class SESALQueryRequest(BaseModel):
    query: str


class SESALQueryResponse(BaseModel):
    response: str
    source: str
    chunks_used: int


# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM
# ─────────────────────────────────────────────────────────────────────────────

class UniversityResponse(BaseModel):
    id: str
    name: str
    acronym: str
    city: str

    class Config:
        from_attributes = True


class PeriodResponse(BaseModel):
    id: str
    period_name: str
    period_order: int
    year_number: Optional[int]
    is_internship: bool

    class Config:
        from_attributes = True


class SubjectResponse(BaseModel):
    id: str
    code: Optional[str]
    name: str
    credits: Optional[int]

    class Config:
        from_attributes = True