"""
Medix AI — Módulo Enfermería
Router NANDA / NOC / NIC (FastAPI)

Ubicación sugerida en el repo backend: app/routers/enfermeria_nnn.py
Catálogo (JSON-en-repo):              app/data/nanda_noc_nic.json

Wiring en main.py:
    from app.routers import enfermeria_nnn
    app.include_router(enfermeria_nnn.router, prefix="/api/v1")
    # -> rutas finales:  /api/v1/enfermeria/nnn/...

NOTA: el catálogo se carga UNA vez y queda cacheado en memoria. Si editas el
JSON, reinicia el proceso (en Railway, un redeploy basta) o llama a /reload.
"""

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Si tu repo NO usa el paquete "app", ajusta este import a tu layout real.
from app.schemas.schemas_pae import (
    DominioNANDA,
    DiagnosticoNANDA,
    ResultadoNOC,
    IntervencionNIC,
)

router = APIRouter(prefix="/enfermeria/nnn", tags=["Enfermería NNN"])

# Ruta al JSON relativa a este archivo: app/routers/ -> app/data/
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nanda_noc_nic.json"


# ──────────────────────────────────────────────────────────────
# Modelo de respuesta hidratada (diagnóstico + NOC/NIC resueltos)
# ──────────────────────────────────────────────────────────────
class DiagnosticoDetalle(BaseModel):
    diagnostico: DiagnosticoNANDA
    noc: list[ResultadoNOC] = []
    nic: list[IntervencionNIC] = []


# ──────────────────────────────────────────────────────────────
# Carga e índices (cacheados)
# ──────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _catalogo() -> dict:
    if not DATA_PATH.exists():
        raise RuntimeError(f"No se encontró el catálogo NNN en {DATA_PATH}")
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _indices():
    data = _catalogo()
    dx_idx = {d["codigo"]: d for d in data.get("diagnosticos", [])}
    noc_idx = {n["codigo"]: n for n in data.get("noc", [])}
    nic_idx = {i["codigo"]: i for i in data.get("nic", [])}
    return dx_idx, noc_idx, nic_idx


def _normalizar(texto: str) -> str:
    """minúsculas + sin acentos, para búsquedas tolerantes."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@router.get("/meta")
def obtener_meta():
    """Versión de taxonomías y avisos del catálogo."""
    return _catalogo().get("meta", {})


@router.get("/dominios", response_model=list[DominioNANDA])
def listar_dominios():
    """Los 13 dominios de la Taxonomía II de NANDA-I."""
    return _catalogo().get("dominios_nanda", [])


@router.get("/diagnosticos", response_model=list[DiagnosticoNANDA])
def listar_diagnosticos(
    dominio: Optional[int] = Query(None, ge=1, le=13, description="Filtrar por dominio 1-13"),
    tipo: Optional[str] = Query(None, description="real | riesgo | promocion | sindrome"),
    q: Optional[str] = Query(None, description="Búsqueda por etiqueta o código (sin acentos)"),
):
    """Lista/filtra diagnósticos NANDA. Combina los filtros opcionales."""
    resultados = _catalogo().get("diagnosticos", [])
    if dominio is not None:
        resultados = [d for d in resultados if d.get("dominio") == dominio]
    if tipo:
        resultados = [d for d in resultados if d.get("tipo") == tipo]
    if q:
        qn = _normalizar(q)
        resultados = [
            d for d in resultados
            if qn in _normalizar(d.get("etiqueta", "")) or qn in d.get("codigo", "")
        ]
    return resultados


@router.get("/diagnosticos/{codigo}", response_model=DiagnosticoDetalle)
def obtener_diagnostico(codigo: str):
    """Diagnóstico + sus NOC y NIC sugeridos ya resueltos (hidratados)."""
    dx_idx, noc_idx, nic_idx = _indices()
    dx = dx_idx.get(codigo)
    if not dx:
        raise HTTPException(status_code=404, detail=f"Diagnóstico '{codigo}' no encontrado")
    noc = [noc_idx[c] for c in dx.get("noc_sugeridos", []) if c in noc_idx]
    nic = [nic_idx[c] for c in dx.get("nic_sugeridos", []) if c in nic_idx]
    return {"diagnostico": dx, "noc": noc, "nic": nic}


@router.get("/noc/{codigo}", response_model=ResultadoNOC)
def obtener_noc(codigo: str):
    _, noc_idx, _ = _indices()
    if codigo not in noc_idx:
        raise HTTPException(status_code=404, detail=f"NOC '{codigo}' no encontrado")
    return noc_idx[codigo]


@router.get("/nic/{codigo}", response_model=IntervencionNIC)
def obtener_nic(codigo: str):
    _, _, nic_idx = _indices()
    if codigo not in nic_idx:
        raise HTTPException(status_code=404, detail=f"NIC '{codigo}' no encontrado")
    return nic_idx[codigo]


@router.post("/reload")
def recargar_catalogo():
    """Limpia la caché para releer el JSON sin reiniciar el proceso."""
    _catalogo.cache_clear()
    _indices.cache_clear()
    data = _catalogo()
    return {
        "ok": True,
        "diagnosticos": len(data.get("diagnosticos", [])),
        "noc": len(data.get("noc", [])),
        "nic": len(data.get("nic", [])),
    }
