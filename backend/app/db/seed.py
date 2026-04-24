"""
Medix AI — Seed Script
Pobla la base de datos con los currículos completos de UNAH y UNICAH.
Ejecutar una sola vez: python -m app.db.seed
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.curriculum import University, CurriculumPeriod, Subject


UNAH_DATA = {
    "name": "Universidad Nacional Autónoma de Honduras",
    "acronym": "UNAH",
    "city": "Tegucigalpa",
    "periods": [
        {
            "period_name": "PRIMER AÑO",
            "period_order": 1,
            "year_number": 1,
            "subjects": [
                {"name": "Morfología I (Anatomía)", "code": "MED-101", "credits": 6,
                 "ai_context_hint": "Anatomía macroscópica básica. Nivel introductorio. Usa términos anatómicos simples y analogías visuales."},
                {"name": "Morfología II (Histología)", "code": "MED-102", "credits": 5,
                 "ai_context_hint": "Histología y citología. Describe estructuras microscópicas. Relaciona morfología con función."},
                {"name": "Bioquímica Médica I", "code": "MED-103", "credits": 5,
                 "ai_context_hint": "Bioquímica básica: carbohidratos, lípidos, proteínas. Nivel pre-clínico."},
                {"name": "Biología Celular y Molecular", "code": "MED-104", "credits": 4,
                 "ai_context_hint": "Genética y biología molecular básica. Enfoca en implicaciones médicas."},
                {"name": "Introducción a la Medicina", "code": "MED-105", "credits": 3,
                 "ai_context_hint": "Introducción al campo médico. Nivel muy básico, motivacional."},
            ],
        },
        {
            "period_name": "SEGUNDO AÑO",
            "period_order": 2,
            "year_number": 2,
            "subjects": [
                {"name": "Fisiología I", "code": "MED-201", "credits": 6,
                 "ai_context_hint": "Fisiología de sistemas: cardiovascular, respiratorio. Usa diagramas en texto y fisiopatología básica."},
                {"name": "Fisiología II", "code": "MED-202", "credits": 6,
                 "ai_context_hint": "Fisiología renal, digestiva, endocrina. Enfoca mecanismos homeostáticos."},
                {"name": "Farmacología I", "code": "MED-203", "credits": 5,
                 "ai_context_hint": "Farmacocinética y farmacodinámica básica. Enfoca en conceptos de absorción y metabolismo."},
                {"name": "Microbiología y Parasitología", "code": "MED-204", "credits": 5,
                 "ai_context_hint": "Bacterias, virus, parásitos. Énfasis en enfermedades endémicas de Honduras: Dengue, Malaria, Chagas, Leptospira."},
                {"name": "Patología General", "code": "MED-205", "credits": 5,
                 "ai_context_hint": "Procesos patológicos básicos: inflamación, neoplasia, necrosis."},
            ],
        },
        {
            "period_name": "TERCER AÑO",
            "period_order": 3,
            "year_number": 3,
            "subjects": [
                {"name": "Semiología Médica y Quirúrgica", "code": "MED-301", "credits": 7,
                 "ai_context_hint": "Interrogatorio clínico y examen físico. Enseña técnica semiológica paso a paso. Es el año donde el estudiante comienza contacto con pacientes."},
                {"name": "Patología Sistémica", "code": "MED-302", "credits": 6,
                 "ai_context_hint": "Patología por sistemas. Correlaciona con manifestaciones clínicas."},
                {"name": "Farmacología II", "code": "MED-303", "credits": 5,
                 "ai_context_hint": "Fármacos por sistemas. Incluye antibióticos disponibles en el Cuadro Básico HN."},
                {"name": "Salud Pública I", "code": "MED-304", "credits": 4,
                 "ai_context_hint": "Epidemiología básica y salud comunitaria en Honduras. Contexto de SESAL."},
            ],
        },
        {
            "period_name": "CUARTO AÑO",
            "period_order": 4,
            "year_number": 4,
            "subjects": [
                {"name": "Medicina Interna I", "code": "MED-401", "credits": 8,
                 "ai_context_hint": "Clínica médica. Diagnóstico diferencial. Manejo en hospitales hondureños como Hospital Escuela."},
                {"name": "Cirugía General I", "code": "MED-402", "credits": 7,
                 "ai_context_hint": "Cirugía básica. Protocolo pre y postoperatorio. Emergencias quirúrgicas."},
                {"name": "Pediatría I", "code": "MED-403", "credits": 7,
                 "ai_context_hint": "Pediatría básica. Incluye escalas APGAR, Silverman, dosis pediátricas por kg."},
                {"name": "Ginecología y Obstetricia I", "code": "MED-404", "credits": 7,
                 "ai_context_hint": "Obstetricia y ginecología. Atención del parto. Control prenatal según normas SESAL."},
            ],
        },
        {
            "period_name": "QUINTO AÑO",
            "period_order": 5,
            "year_number": 5,
            "subjects": [
                {"name": "Medicina Interna II", "code": "MED-501", "credits": 8, "ai_context_hint": "Medicina interna avanzada. Manejo de enfermedades crónicas."},
                {"name": "Cirugía General II", "code": "MED-502", "credits": 7, "ai_context_hint": "Cirugía avanzada. Trauma y emergencias."},
                {"name": "Psiquiatría", "code": "MED-503", "credits": 5, "ai_context_hint": "Salud mental. Enfermedades psiquiátricas prevalentes en Honduras."},
                {"name": "Neurología", "code": "MED-504", "credits": 5, "ai_context_hint": "Neurología clínica. Síndromes neurológicos comunes."},
                {"name": "Medicina Legal", "code": "MED-505", "credits": 4, "ai_context_hint": "Aspectos legales de la práctica médica en Honduras. Ley de Salud."},
            ],
        },
        {
            "period_name": "SEXTO AÑO",
            "period_order": 6,
            "year_number": 6,
            "subjects": [
                {"name": "Urología", "code": "MED-601", "credits": 4, "ai_context_hint": "Urología básica y clínica."},
                {"name": "Dermatología", "code": "MED-602", "credits": 4, "ai_context_hint": "Dermatología. Lesiones elementales, diagnóstico visual."},
                {"name": "Oftalmología", "code": "MED-603", "credits": 3, "ai_context_hint": "Oftalmología básica."},
                {"name": "Otorrinolaringología", "code": "MED-604", "credits": 3, "ai_context_hint": "ORL básica."},
                {"name": "Medicina de Emergencias", "code": "MED-605", "credits": 6,
                 "ai_context_hint": "Urgencias y emergencias. Protocolos ABCDE, RCP, manejo de shock. Crítico para guardia."},
            ],
        },
        {
            "period_name": "INTERNADO ROTATORIO",
            "period_order": 7,
            "year_number": 7,
            "is_internship": True,
            "subjects": [
                {"name": "Rotación Medicina Interna", "code": "INT-701", "credits": 8,
                 "ai_context_hint": "Interno en sala de medicina. Respuestas clínicas directas, algoritmos de manejo, diagnóstico diferencial probabilístico. NO explicaciones básicas."},
                {"name": "Rotación Cirugía", "code": "INT-702", "credits": 8,
                 "ai_context_hint": "Interno en cirugía. Manejo de paciente quirúrgico, indicaciones operatorias."},
                {"name": "Rotación Pediatría", "code": "INT-703", "credits": 8,
                 "ai_context_hint": "Interno en pediatría. Dosis pediátricas, emergencias neonatales, AIEPI."},
                {"name": "Rotación Ginecología/Obstetricia", "code": "INT-704", "credits": 8,
                 "ai_context_hint": "Interno en GINO. Atención del parto, emergencias obstétricas."},
            ],
        },
        {
            "period_name": "SERVICIO SOCIAL",
            "period_order": 8,
            "year_number": 8,
            "is_social_service": True,
            "subjects": [
                {"name": "Medicina Rural / Comunitaria", "code": "SS-801", "credits": 10,
                 "ai_context_hint": "Médico en zona rural Honduras. SIN especialistas cercanos, recursos limitados. Prioriza atención primaria, referencia oportuna, protocolos SESAL locales. Offline es clave aquí."},
            ],
        },
    ],
}

UNICAH_DATA = {
    "name": "Universidad Católica de Honduras",
    "acronym": "UNICAH",
    "city": "Tegucigalpa",
    "periods": [
        {"period_name": "I PERÍODO", "period_order": 1, "year_number": 1, "subjects": [
            {"name": "Filosofía", "code": "UC-101", "credits": 3, "ai_context_hint": "Introducción filosófica. Estudiante en primer período de medicina."},
            {"name": "Biología General", "code": "UC-102", "credits": 4, "ai_context_hint": "Biología celular básica."},
            {"name": "Química General", "code": "UC-103", "credits": 4, "ai_context_hint": "Química para ciencias de la salud."},
            {"name": "Inglés Técnico I", "code": "UC-104", "credits": 2, "ai_context_hint": "Inglés médico básico."},
        ]},
        {"period_name": "II PERÍODO", "period_order": 2, "year_number": 1, "subjects": [
            {"name": "Doctrina Social de la Iglesia", "code": "UC-201", "credits": 3, "ai_context_hint": "Ética y doctrina social. Enfoca en bioética médica."},
            {"name": "Anatomía Humana I", "code": "UC-202", "credits": 6, "ai_context_hint": "Anatomía macroscópica. Primer contacto con nomenclatura anatómica."},
            {"name": "Bioética", "code": "UC-203", "credits": 3, "ai_context_hint": "Bioética médica. Dilemas éticos en medicina hondureña."},
        ]},
        {"period_name": "III PERÍODO", "period_order": 3, "year_number": 2, "subjects": [
            {"name": "Anatomía Humana II", "code": "UC-301", "credits": 6, "ai_context_hint": "Anatomía avanzada: tórax, abdomen, pelvis."},
            {"name": "Histología", "code": "UC-302", "credits": 5, "ai_context_hint": "Histología básica."},
            {"name": "Fisiología Humana I", "code": "UC-303", "credits": 5, "ai_context_hint": "Fisiología cardiovascular y respiratoria básica."},
        ]},
    ],
}


async def seed():
    print("🌱 Iniciando seed de currículos Medix AI...")
    async with AsyncSessionLocal() as db:
        try:
            for data in [UNAH_DATA, UNICAH_DATA]:
                # Crear universidad
                univ = University(
                    name=data["name"],
                    acronym=data["acronym"],
                    city=data["city"],
                )
                db.add(univ)
                await db.flush()
                print(f"  ✅ Universidad: {data['acronym']}")

                for pd in data["periods"]:
                    period = CurriculumPeriod(
                        university_id=univ.id,
                        period_name=pd["period_name"],
                        period_order=pd["period_order"],
                        year_number=pd.get("year_number"),
                        is_internship=pd.get("is_internship", False),
                        is_social_service=pd.get("is_social_service", False),
                    )
                    db.add(period)
                    await db.flush()

                    for sub in pd.get("subjects", []):
                        subject = Subject(
                            period_id=period.id,
                            code=sub.get("code"),
                            name=sub["name"],
                            credits=sub.get("credits"),
                            ai_context_hint=sub.get("ai_context_hint"),
                        )
                        db.add(subject)

                await db.flush()
                print(f"  ✅ Períodos y materias creados para {data['acronym']}")

            await db.commit()
            print("\n🎉 Seed completado exitosamente!")
            print("   UNAH: 8 años, 35+ materias")
            print("   UNICAH: 19 períodos, laboratorios y seminarios")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error en seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())
