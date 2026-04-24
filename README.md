# Medix AI — Plataforma Médica Multiplataforma para Honduras

**Stack:** FastAPI + PostgreSQL + Redis · Flutter (Android/iOS/Web/Desktop) · Claude AI (Anthropic)  
**Deploy:** Railway (MVP) → AWS (Escala)  
**Target:** Estudiantes UNAH/UNICAH · Médicos Generales · Especialistas

---

## 🏗️ Arquitectura

```
medix-ai/
├── backend/                    # FastAPI Python
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py       # Settings Pydantic (env vars)
│   │   │   └── security.py     # JWT + password hashing
│   │   ├── db/
│   │   │   ├── session.py      # AsyncSession SQLAlchemy
│   │   │   └── seed.py         # Seed UNAH + UNICAH currículos
│   │   ├── models/
│   │   │   ├── user.py         # User, roles, suscripciones
│   │   │   ├── curriculum.py   # University, Period, Subject
│   │   │   └── medical.py      # MedicalScan, ChatSession, ChatMessage
│   │   ├── routes/
│   │   │   ├── auth.py         # /register /login /me
│   │   │   ├── upload.py       # /scan (MedScan Vision)
│   │   │   └── analysis.py     # /chat /soap /ecoe /sesal
│   │   ├── schemas/
│   │   │   └── medix.py        # Pydantic schemas validación
│   │   ├── services/
│   │   │   ├── llm.py          # Claude API — chat, SOAP, ECOE
│   │   │   ├── vision.py       # Claude Vision — MedScan
│   │   │   └── sesal_rag.py    # RAG Normas SESAL Honduras
│   │   └── main.py             # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── mobile/                     # Flutter App
│   ├── lib/
│   │   ├── main.dart           # Entry point + auth router
│   │   ├── theme.dart          # MedixTheme + colores
│   │   ├── services/
│   │   │   └── api.dart        # Dio HTTP client + JWT
│   │   └── screens/
│   │       ├── login_screen.dart
│   │       ├── register_screen.dart
│   │       ├── home_screen.dart      # Dashboard + nav
│   │       ├── chat_screen.dart      # Chat IA contextual
│   │       ├── medscan_screen.dart   # Upload + análisis
│   │       ├── guardia_screen.dart   # Calculadoras offline
│   │       ├── soap_screen.dart      # Dictado SOAP
│   │       └── profile_screen.dart
│   └── pubspec.yaml
└── docker-compose.yml
```

---

## 🚀 Setup Rápido

### 1. Clonar y configurar variables de entorno
```bash
git clone https://github.com/TU_USUARIO/medix-ai.git
cd medix-ai/backend
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY y credenciales
```

### 2. Levantar backend con Docker
```bash
docker-compose up --build
```

### 3. Seed de la base de datos (primera vez)
```bash
docker exec medix_backend python -m app.db.seed
```

### 4. Verificar
```
http://localhost:8000/         → Health check
http://localhost:8000/docs     → Swagger UI (desarrollo)
```

### 5. Flutter App
```bash
cd mobile
flutter pub get
flutter run                    # Android/iOS
flutter run -d chrome          # Web
```

---

## 🤖 Módulos de IA

| Módulo | Endpoint | LLM | Plan |
|---|---|---|---|
| Chat IA Contextual | `POST /api/v1/analysis/chat` | Claude Sonnet | Free/Pro |
| Dictado SOAP | `POST /api/v1/analysis/soap` | Claude Sonnet | Pro+ |
| Simulador ECOE | `POST /api/v1/analysis/ecoe/start` | Claude Sonnet | Free |
| MedScan Vision | `POST /api/v1/upload/scan` | Claude Vision | Free(3/día)/Clinical |
| SESAL RAG | `POST /api/v1/analysis/sesal` | Claude + ChromaDB | Todos |

---

## 💰 Planes de Suscripción

| Feature | Free | Pro (L299/mes) | Clinical (L799/mes) |
|---|---|---|---|
| Chat IA | 20/día | 500/día | 500/día |
| MedScan | 3/día | 50/día | Ilimitado |
| Modo Guardia offline | ✅ | ✅ | ✅ |
| Dictado SOAP | ❌ | ✅ | ✅ |
| SESAL RAG | ✅ | ✅ | ✅ |
| Prioridad en respuestas | ❌ | ❌ | ✅ |

---

## 🌍 Deploy en Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli
railway login

# Nuevo proyecto
railway new
railway add postgresql
railway add redis

# Deploy
railway up

# Variables de entorno en Railway dashboard:
# ANTHROPIC_API_KEY, JWT_SECRET_KEY, etc.
```

---

## 📋 Roadmap

### ✅ Sprint 1 (ACTUAL) — Backend + Flutter Base
- [x] FastAPI con auth JWT
- [x] Claude API integrado (chat, SOAP, ECOE, Vision)
- [x] Flutter app: Login, Dashboard, Chat, MedScan, Guardia, SOAP, Perfil
- [x] PostgreSQL schema completo
- [x] Seed UNAH/UNICAH

### 🔲 Sprint 2 — Stripe + SESAL RAG
- [ ] Integración Stripe webhooks
- [ ] Ingestión PDFs SESAL (dengue, malaria, etc.)
- [ ] ChromaDB vector store funcional
- [ ] Push notifications

### 🔲 Sprint 3 — Beta Testing
- [ ] Deploy Railway producción
- [ ] 50 usuarios beta (UNAH/UNICAH)
- [ ] Analytics de uso
- [ ] Correcciones de UX

### 🔲 Fase 2 — Institucional
- [ ] Radar Epidemiológico (B2B SESAL)
- [ ] Red de interconsulta segura
- [ ] Aval CMH para EMC

---

## ⚠️ Disclaimer Médico
Medix AI es una herramienta de apoyo clínico. No reemplaza el juicio del médico responsable.  
Toda decisión diagnóstica y terapéutica es responsabilidad del profesional de salud.
