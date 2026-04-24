# Sprint 3 — Guía de Activación

## 🔥 Firebase FCM (Push Notifications)

### 1. Crear proyecto Firebase
1. Ve a [console.firebase.google.com](https://console.firebase.google.com)
2. **Crear proyecto** → Nombre: `medix-ai-hn`
3. Habilita **Cloud Messaging**

### 2. Obtener Service Account
```
Firebase Console → Configuración del proyecto
→ Cuentas de servicio
→ Generar nueva clave privada
→ Descarga el JSON
```

### 3. Configurar en Railway
```bash
# Convertir JSON a una sola línea y agregar en Railway Variables:
FIREBASE_PROJECT_ID=medix-ai-hn
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"medix-ai-hn",...}
```

### 4. Agregar google-services.json a Flutter Android
```
Descarga google-services.json desde Firebase Console
→ Copiarlo a: mobile/android/app/google-services.json
```

---

## 📊 Analytics — Primeros pasos

### Inicializar ChromaDB con datos SESAL de muestra
```bash
make sesal-sample
# Carga 4 guías clínicas hondureñas para testing inmediato
```

### Ver métricas en tiempo real
```bash
# Abrir admin dashboard localmente
open admin/dashboard.html

# O servir en Railway con nginx (ver DEPLOY_RAILWAY.md)
```

### Crear primer usuario admin
```bash
make admin-create
# Te pedirá email y contraseña
# Luego usa esas credenciales en admin/dashboard.html
```

---

## 🛡️ Security Hardening activado

El middleware `security_middleware` ya está activo con:
- Rate limiting por IP: 200 req/min general, 10 req/min en `/auth/login`  
- Security headers automáticos (X-Frame-Options, CSP, HSTS)
- Detección de SQL injection y XSS en inputs
- Logging estructurado de todos los requests con latencia

Para ajustar los límites edita `app/middleware/security.py`:
```python
_IP_MAX_REQUESTS = 200        # req/min por IP (general)
_IP_MAX_AUTH_REQUESTS = 10    # req/min en login (anti brute-force)
```

---

## 📱 Onboarding Flutter

El flujo de onboarding se activa automáticamente en la primera instalación.
Se marca como completado en `SharedPreferences` con clave `onboarding_done`.

Para resetear en desarrollo:
```dart
// En el dispositivo o emulador
SharedPreferences prefs = await SharedPreferences.getInstance();
await prefs.remove('onboarding_done');
// Reinicia la app
```

---

## ⭐ Feedback Beta

El widget `FeedbackWidget` puede activarse desde cualquier pantalla:
```dart
// Al final de una sesión de chat exitosa
showFeedbackSheet(context, 'Chat IA');

// Al completar un ECOE
showFeedbackSheet(context, 'Simulador ECOE');
```

Los feedbacks se ven en el Admin Dashboard → sección **Feedback Beta**.

---

## 🔄 Celery Beat — Tareas programadas

| Tarea | Hora (HN) | Descripción |
|---|---|---|
| `reset_daily_rate_limits` | 00:00 | Resetea contadores de chat/scan |
| `generate_daily_analytics_snapshot` | 00:05 | Snapshot de métricas del día |
| `generate_daily_report` | 06:00 | Log de reporte de uso |

Para ejecutar manualmente cualquier tarea:
```bash
# Desde el Admin Dashboard → Tareas
# O desde el Makefile:
make reset-limits
```

---

## 🚀 Estado del proyecto — Sprint 3 completo

```
Medix AI v3.0 — Sprint 3
├── Backend (FastAPI)          ✅ Production-ready
│   ├── Auth JWT               ✅
│   ├── Claude AI (chat/SOAP/ECOE/Vision) ✅
│   ├── SESAL RAG (ChromaDB)   ✅
│   ├── Stripe Webhooks        ✅
│   ├── Analytics Engine       ✅ NUEVO S3
│   ├── FCM Push Notifications ✅ NUEVO S3
│   ├── Admin Routes           ✅ NUEVO S3
│   ├── Security Middleware    ✅ NUEVO S3
│   └── Celery Beat (4 tareas) ✅
│
├── Flutter App (10 screens)   ✅ Production-ready
│   ├── Onboarding (5 slides)  ✅ NUEVO S3
│   ├── Login / Register       ✅
│   ├── Dashboard              ✅
│   ├── Chat IA                ✅
│   ├── MedScan Vision         ✅
│   ├── Modo Guardia (6 calcs) ✅
│   ├── Dictado SOAP           ✅
│   ├── Simulador ECOE         ✅
│   ├── Normas SESAL           ✅
│   ├── Upgrade (Stripe)       ✅
│   ├── Perfil                 ✅
│   ├── Connectivity offline   ✅ NUEVO S3
│   └── Feedback Widget        ✅ NUEVO S3
│
├── Admin Dashboard (HTML)     ✅ NUEVO S3
│   ├── KPIs tiempo real (12)  ✅
│   ├── Charts históricos      ✅
│   ├── Gestión usuarios       ✅
│   ├── Feedback beta          ✅
│   ├── Broadcast push         ✅
│   └── Tareas manuales        ✅
│
├── DevOps                     ✅
│   ├── Docker Compose (5 svcs)✅
│   ├── GitHub Actions CI/CD   ✅
│   ├── Railway deploy guide   ✅
│   └── Makefile (15 cmds)     ✅
│
└── Tests (17 tests)           ✅
    ├── Auth (7 tests)         ✅
    └── Sprint 3 (10 tests)    ✅
```

### Próximos pasos sugeridos (Sprint 4 / Fase 2):
- 🌐 Red de interconsulta entre médicos (WebSocket)
- 📡 Radar epidemiológico (B2B SESAL)
- 🎓 Aval CMH para créditos de EMC
- 🌍 Expansión a El Salvador y Guatemala
- 📈 Migración Railway → AWS cuando lleguen a 1,000+ usuarios
