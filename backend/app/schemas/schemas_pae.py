"""
Medix AI — Módulo Enfermería
Estructura de datos NANDA / NOC / NIC + Plan de Atención de Enfermería (PAE)

Compatible con Pydantic v2 (FastAPI).
Ubicación sugerida en el repo backend: app/schemas/schemas_pae.py

NOTA CLÍNICA / LEGAL:
Las taxonomías NANDA-I, NOC y NIC son propiedad intelectual (Thieme / Elsevier).
Este esquema define SOLO la estructura. Los códigos, definiciones, indicadores y
actividades deben verificarse y completarse contra las ediciones oficiales
licenciadas antes de cualquier uso clínico real.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────
# Tipos base
# ──────────────────────────────────────────────────────────────
TipoDiagnostico = Literal["real", "riesgo", "promocion", "sindrome"]


# ──────────────────────────────────────────────────────────────
# NOC — Resultados (Nursing Outcomes Classification)
# ──────────────────────────────────────────────────────────────
class IndicadorNOC(BaseModel):
    descripcion: str
    # Escala Likert 1-5; el significado depende del indicador
    escala: str = "Likert 1-5"


class ResultadoNOC(BaseModel):
    codigo: str                              # p.ej. "1605"
    etiqueta: str                            # p.ej. "Control del dolor"
    dominio: Optional[str] = None
    clase: Optional[str] = None
    indicadores: list[IndicadorNOC] = Field(default_factory=list)
    escala: str = "Likert 1-5 (1 = peor estado, 5 = mejor estado)"


# ──────────────────────────────────────────────────────────────
# NIC — Intervenciones (Nursing Interventions Classification)
# ──────────────────────────────────────────────────────────────
class IntervencionNIC(BaseModel):
    codigo: str                              # p.ej. "1400"
    etiqueta: str                            # p.ej. "Manejo del dolor"
    campo: Optional[str] = None              # Campo NIC (ej. "Fisiológico complejo")
    clase: Optional[str] = None
    actividades: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# NANDA-I — Diagnósticos
# ──────────────────────────────────────────────────────────────
class DiagnosticoNANDA(BaseModel):
    codigo: str                              # p.ej. "00132"
    etiqueta: str                            # p.ej. "Dolor agudo"
    dominio: int                             # 1-13 (Taxonomía II)
    clase: Optional[str] = None
    tipo: TipoDiagnostico = "real"
    definicion: str = ""
    caracteristicas_definitorias: list[str] = Field(default_factory=list)  # dx reales
    factores_relacionados: list[str] = Field(default_factory=list)         # dx reales
    poblacion_riesgo: list[str] = Field(default_factory=list)              # dx de riesgo
    factores_riesgo: list[str] = Field(default_factory=list)               # dx de riesgo
    # Enlaces NNN — se referencian por código (normalizado)
    noc_sugeridos: list[str] = Field(default_factory=list)
    nic_sugeridos: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Catálogo completo (lo que sirve el endpoint de taxonomías)
# ──────────────────────────────────────────────────────────────
class DominioNANDA(BaseModel):
    id: int
    nombre: str


class CatalogoNNN(BaseModel):
    version: str
    dominios_nanda: list[DominioNANDA] = Field(default_factory=list)
    diagnosticos: list[DiagnosticoNANDA] = Field(default_factory=list)
    noc: list[ResultadoNOC] = Field(default_factory=list)
    nic: list[IntervencionNIC] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# PAE — Plan de Atención de Enfermería (salida del endpoint de IA)
# ──────────────────────────────────────────────────────────────
class CasoClinico(BaseModel):
    edad: Optional[int] = None
    sexo: Optional[str] = None
    motivo_consulta: str
    antecedentes: Optional[str] = None
    valoracion: str                          # datos de la valoración de enfermería
    signos_vitales: Optional[dict] = None


class ObjetivoNOC(BaseModel):
    noc: ResultadoNOC
    puntuacion_basal: Optional[int] = None   # 1-5
    puntuacion_diana: Optional[int] = None   # 1-5
    plazo: Optional[str] = None              # p.ej. "72 h", "al alta"


class PlanCuidados(BaseModel):
    diagnostico: DiagnosticoNANDA
    objetivos_noc: list[ObjetivoNOC] = Field(default_factory=list)
    intervenciones_nic: list[IntervencionNIC] = Field(default_factory=list)
    justificacion: Optional[str] = None      # razonamiento clínico


class PAEResponse(BaseModel):
    caso: CasoClinico
    planes: list[PlanCuidados] = Field(default_factory=list)
    nota_clinica: str = (
        "Plan generado como apoyo a la decisión. Requiere revisión y validación "
        "por profesional de enfermería colegiado antes de su aplicación."
    )
