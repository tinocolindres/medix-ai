"""
Medix AI — SESAL Ingestion Pipeline
Ingesta PDFs oficiales de la Secretaría de Salud de Honduras al vector store.

Uso:
    python -m app.services.sesal_ingest --all          # Ingesta todos los PDFs en /data/sesal/
    python -m app.services.sesal_ingest --file ruta.pdf --name "Manejo Dengue 2024"
    python -m app.services.sesal_ingest --status       # Ver documentos indexados
"""
import argparse
import asyncio
import os
from pathlib import Path

# ── Documentos SESAL a ingestar ────────────────────────────────
# Descarga los PDFs oficiales de: https://www.salud.gob.hn/site/index.php/guias-clinicas
SESAL_DOCUMENTS = [
    {
        "filename": "guia_dengue_2023.pdf",
        "name": "Guía Nacional para el Manejo del Dengue 2023 — SESAL Honduras",
        "category": "infectologia",
        "keywords": ["dengue", "dengue hemorrágico", "ns1", "plaquetas", "shock dengue"],
    },
    {
        "filename": "guia_malaria_2022.pdf",
        "name": "Guía Clínica de Malaria — SESAL Honduras 2022",
        "category": "infectologia",
        "keywords": ["malaria", "paludismo", "plasmodium", "cloroquina", "primaquina"],
    },
    {
        "filename": "cuadro_basico_medicamentos_2023.pdf",
        "name": "Cuadro Básico de Medicamentos Honduras 2023",
        "category": "farmacologia",
        "keywords": ["medicamentos", "formulario", "genéricos", "dosis", "presentación"],
    },
    {
        "filename": "guia_hipertension_2022.pdf",
        "name": "Guía de Práctica Clínica Hipertensión Arterial — SESAL 2022",
        "category": "cardiologia",
        "keywords": ["hipertensión", "presión arterial", "antihipertensivos", "captopril", "amlodipino"],
    },
    {
        "filename": "guia_diabetes_2021.pdf",
        "name": "Guía de Práctica Clínica Diabetes Mellitus — SESAL 2021",
        "category": "endocrinologia",
        "keywords": ["diabetes", "glucosa", "insulina", "metformina", "hipoglucemia"],
    },
    {
        "filename": "guia_tb_2023.pdf",
        "name": "Guía de Tuberculosis Honduras 2023 — SESAL/PNCT",
        "category": "infectologia",
        "keywords": ["tuberculosis", "tb", "rifampicina", "isoniacida", "baciloscopia", "dots"],
    },
    {
        "filename": "guia_vih_2022.pdf",
        "name": "Guía de Atención Integral VIH/SIDA — SESAL 2022",
        "category": "infectologia",
        "keywords": ["vih", "sida", "antirretrovirales", "tar", "cd4", "carga viral"],
    },
    {
        "filename": "guia_prenatal_2022.pdf",
        "name": "Norma de Atención Materno-Perinatal — SESAL Honduras",
        "category": "ginecologia",
        "keywords": ["prenatal", "embarazo", "control prenatal", "parto", "eclampsia", "preeclampsia"],
    },
    {
        "filename": "guia_aiepi_2020.pdf",
        "name": "AIEPI — Atención Integrada a Enfermedades Prevalentes de la Infancia",
        "category": "pediatria",
        "keywords": ["aiepi", "pediatría", "neumonía pediátrica", "diarrea", "desnutrición"],
    },
    {
        "filename": "guia_covid_2022.pdf",
        "name": "Protocolo COVID-19 Honduras — SESAL 2022",
        "category": "infectologia",
        "keywords": ["covid", "coronavirus", "sars-cov-2", "saturación", "dexametasona"],
    },
]

DATA_DIR = Path("./data/sesal")


async def ingest_all_pdfs(verbose: bool = True):
    """Ingesta todos los PDFs disponibles en DATA_DIR."""
    from app.services.sesal_rag import ingest_sesal_pdf

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for doc in SESAL_DOCUMENTS:
        pdf_path = DATA_DIR / doc["filename"]

        if not pdf_path.exists():
            if verbose:
                print(f"⚠️  Archivo no encontrado: {pdf_path}")
                print(f"   Descarga desde https://www.salud.gob.hn y coloca en {DATA_DIR}/")
            results.append({"document": doc["name"], "status": "file_missing"})
            continue

        if verbose:
            print(f"📄 Ingiriendo: {doc['name']}...")

        try:
            result = await ingest_sesal_pdf(str(pdf_path), doc["name"])
            results.append({
                "document": doc["name"],
                "status": "ok",
                "chunks": result["chunks_ingested"],
            })
            if verbose:
                print(f"   ✅ {result['chunks_ingested']} chunks indexados")
        except Exception as e:
            results.append({"document": doc["name"], "status": "error", "error": str(e)})
            if verbose:
                print(f"   ❌ Error: {e}")

    # Resumen
    ok = sum(1 for r in results if r["status"] == "ok")
    missing = sum(1 for r in results if r["status"] == "file_missing")
    errors = sum(1 for r in results if r["status"] == "error")

    if verbose:
        print(f"\n{'='*50}")
        print(f"✅ Exitosos: {ok}/{len(SESAL_DOCUMENTS)}")
        print(f"⚠️  Faltantes: {missing}")
        print(f"❌ Errores: {errors}")
        print(f"{'='*50}")
        if missing > 0:
            print("\n📥 Para descargar los PDFs faltantes:")
            print("   https://www.salud.gob.hn/site/index.php/guias-clinicas")
            print("   https://www.ihss.hn/guias-clinicas")

    return results


async def show_status():
    """Muestra el estado actual del vector store SESAL."""
    from app.services.sesal_rag import get_chroma_collection

    collection = get_chroma_collection()
    count = collection.count()
    print(f"\n📊 Estado ChromaDB — SESAL RAG")
    print(f"   Total chunks indexados: {count}")

    if count > 0:
        # Muestra los primeros documentos únicos
        results = collection.get(limit=100, include=["metadatas"])
        sources = set()
        for meta in results["metadatas"]:
            sources.add(meta.get("source", "desconocido"))

        print(f"   Documentos indexados ({len(sources)}):")
        for src in sorted(sources):
            print(f"     • {src}")
    else:
        print("   ⚠️  Vector store vacío. Ejecuta: python -m app.services.sesal_ingest --all")


async def create_sample_sesal_content():
    """
    Crea contenido de muestra de SESAL para testing cuando no hay PDFs reales.
    Usa guías reales embebidas como texto.
    """
    import chromadb
    from sentence_transformers import SentenceTransformer
    from app.core.config import settings

    SAMPLE_CONTENT = [
        {
            "source": "Guía Nacional Dengue 2023 — SESAL Honduras",
            "content": """MANEJO DEL DENGUE — SESAL HONDURAS 2023

CLASIFICACIÓN CLÍNICA:
1. Dengue sin señales de alarma: Fiebre + 2 criterios (náuseas, rash, dolor, prueba torniquete positiva)
2. Dengue con señales de alarma: Dolor abdominal intenso, vómitos persistentes, acumulación líquidos, sangrado mucosas, letargia, hepatomegalia >2cm, incremento hematocrito con rápida disminución de plaquetas
3. Dengue grave: Fuga plasmática severa, hemorragia grave, daño orgánico grave

MANEJO AMBULATORIO (Grupo A — sin señales de alarma):
- Reposo en cama
- Hidratación oral: mínimo 5 vasos/día en adultos
- Acetaminofén 500mg c/6h (NO AINEs, NO Aspirina — riesgo de sangrado)
- Monitoreo de señales de alarma
- Control médico en 24-48h

MANEJO HOSPITALARIO (Grupo B — señales de alarma):
- Hospitalización OBLIGATORIA
- Cristaloides IV: Solución Hartmann o SSN 0.9% — bolo 10mL/kg en 1 hora
- Monitoreo de hematocrito c/4-6h
- Control de plaquetas c/24h
- Si plaquetas <20,000 sin sangrado: monitoreo
- Si plaquetas <10,000 o sangrado activo: considerar transfusión

DENGUE GRAVE (Grupo C):
- UCI inmediata
- Bolo IV 20mL/kg en 15-30 minutos
- Si no mejora: repetir bolo, evaluar coloides
- Transfusión GRE si Hto <30% con inestabilidad hemodinámica""",
        },
        {
            "source": "Cuadro Básico de Medicamentos Honduras 2023",
            "content": """CUADRO BÁSICO DE MEDICAMENTOS ESENCIALES — HONDURAS 2023
SESAL / Secretaría de Salud

ANTIBIÓTICOS DISPONIBLES EN HOSPITALES PÚBLICOS:
- Amoxicilina 500mg cápsulas / 250mg/5mL suspensión
- Ampicilina 500mg cápsulas / 1g ampolla IV
- Bencilpenicilina sódica (Penicilina G) 1,000,000 UI / 5,000,000 UI ampolla
- Ceftriaxona 1g / 500mg ampolla IV (disponible en nivel II y III)
- Ciprofloxacina 500mg tabletas / 200mg/100mL bolsa IV
- Clindamicina 300mg cápsulas / 600mg ampolla
- Eritromicina 500mg tabletas
- Gentamicina 80mg/2mL ampolla
- Metronidazol 500mg tabletas / 500mg/100mL bolsa IV
- Trimetoprim/Sulfametoxazol 80/400mg tabletas

ANALGÉSICOS Y ANTIPIRÉTICOS:
- Acetaminofén 500mg tabletas / 125mg/5mL jarabe / 1g/100mL IV
- Ibuprofeno 400mg / 600mg tabletas
- Ketorolaco 30mg/mL ampolla
- Morfina 10mg/mL ampolla (uso controlado, nivel III)
- Tramadol 50mg cápsulas / 100mg/2mL ampolla

ANTIHIPERTENSIVOS:
- Amlodipino 5mg / 10mg tabletas
- Captopril 25mg / 50mg tabletas
- Enalapril 10mg / 20mg tabletas
- Hidralazina 20mg/mL ampolla (emergencia hipertensiva)
- Losartán 50mg / 100mg tabletas
- Metoprolol 50mg / 100mg tabletas""",
        },
        {
            "source": "Guía Práctica Clínica Hipertensión Arterial — SESAL 2022",
            "content": """HIPERTENSIÓN ARTERIAL — GUÍA CLÍNICA SESAL HONDURAS 2022

CLASIFICACIÓN JNC 8 / AHA-ACC 2017 (adoptada por SESAL):
- Normal: <120/80 mmHg
- Elevada: 120-129/<80 mmHg
- HTA Estadio 1: 130-139/80-89 mmHg
- HTA Estadio 2: ≥140/≥90 mmHg
- Crisis hipertensiva: >180/120 mmHg

TRATAMIENTO FARMACOLÓGICO INICIAL (según Cuadro Básico HN):
- HTA Estadio 1 sin comorbilidades: Amlodipino 5mg QD ó Enalapril 10mg BID
- HTA Estadio 2: Biterapia — Amlodipino + IECA/ARA II
- Diabetes + HTA: IECA preferido (Enalapril/Captopril) — protección renal
- IRC + HTA: IECA o ARA II (Losartán)

CRISIS HIPERTENSIVA URGENTE (>180/120 sin daño órgano):
- Captopril sublingual 25mg (inicio acción 15-30 min)
- Meta: reducir PA 25% en 1-2 horas
- NO reducir abruptamente (riesgo de isquemia cerebral)

CRISIS HIPERTENSIVA EMERGENTE (con daño órgano agudo):
- Hospitalización en UCI
- Hidralazina 20mg IV en bolo (disponible Cuadro Básico)
- Labetalol (si disponible) 20mg IV cada 10 min
- Nitroprusiato de sodio si está disponible (nivel III)""",
        },
        {
            "source": "Protocolo AIEPI — Atención Integrada Enfermedades Prevalentes Infancia",
            "content": """AIEPI — PROTOCOLO HONDURAS (SESAL/OPS)
Atención del niño de 2 meses a 5 años

EVALUAR SIGNOS GENERALES DE PELIGRO:
- ¿Puede beber o tomar el pecho?
- ¿Vomita todo?
- ¿Tuvo convulsiones?
- ¿Está letárgico o inconsciente?
SI → REFERENCIA URGENTE

CLASIFICAR NEUMONÍA:
- NEUMONÍA GRAVE: Tiraje subcostal → Amoxicilina 40mg/kg/día ÷ 2 dosis x 5 días + referencia
- NEUMONÍA: FR elevada (≥50 rpm <1año; ≥40 rpm 1-5años) → Amoxicilina oral x 5 días
- NO NEUMONÍA (tos o resfriado): Tratamiento sintomático

DESHIDRATACIÓN:
- Plan A: Sin deshidratación — LHO en casa, zinc 20mg/día x 10 días
- Plan B: Deshidratación — SRO 75mL/kg en 4 horas en establecimiento
- Plan C: Deshidratación grave — SSN 0.9% 100mL/kg IV, referencia urgente

DESNUTRICIÓN AGUDA SEVERA:
- MUAC <11.5cm o edema bilateral → Hospitalización
- F-75 → F-100 → ATLU según protocolo SESAL""",
        },
    ]

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection = chroma_client.get_or_create_collection(name=settings.SESAL_COLLECTION)

    documents = [c["content"] for c in SAMPLE_CONTENT]
    metadatas = [{"source": c["source"], "chunk_index": 0} for c in SAMPLE_CONTENT]
    ids = [f"sample_{i}" for i in range(len(SAMPLE_CONTENT))]
    embeddings = model.encode(documents).tolist()

    collection.upsert(documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas)
    print(f"✅ {len(SAMPLE_CONTENT)} documentos SESAL de muestra cargados en ChromaDB")
    print("   (Reemplaza con PDFs reales usando --all)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SESAL RAG Ingestion Tool — Medix AI")
    parser.add_argument("--all", action="store_true", help="Ingestar todos los PDFs en ./data/sesal/")
    parser.add_argument("--file", type=str, help="Ruta a un PDF específico")
    parser.add_argument("--name", type=str, help="Nombre del documento (requerido con --file)")
    parser.add_argument("--status", action="store_true", help="Ver documentos indexados")
    parser.add_argument("--sample", action="store_true", help="Cargar contenido de muestra para testing")
    args = parser.parse_args()

    if args.status:
        asyncio.run(show_status())
    elif args.sample:
        asyncio.run(create_sample_sesal_content())
    elif args.all:
        asyncio.run(ingest_all_pdfs())
    elif args.file and args.name:
        from app.services.sesal_rag import ingest_sesal_pdf
        result = asyncio.run(ingest_sesal_pdf(args.file, args.name))
        print(f"✅ {result['chunks_ingested']} chunks indexados para: {args.name}")
    else:
        parser.print_help()
