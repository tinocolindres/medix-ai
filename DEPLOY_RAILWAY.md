# 🚂 Guía de Deploy — Medix AI en Railway
## De cero a producción en 20 minutos

---

## Prerequisitos
- Cuenta en [Railway.app](https://railway.app)
- CLI Railway: `npm install -g @railway/cli`
- API Key de Anthropic: [console.anthropic.com](https://console.anthropic.com)
- Cuenta Stripe (para pagos): [stripe.com](https://stripe.com)

---

## Paso 1 — Crear proyecto Railway

```bash
# Instalar CLI
npm install -g @railway/cli

# Login
railway login

# Crear proyecto nuevo
railway new
# Escoge: Empty Project
# Nombre: medix-ai
```

---

## Paso 2 — Agregar PostgreSQL y Redis

En el dashboard de Railway:
1. Click **+ New Service** → **Database** → **PostgreSQL**
2. Click **+ New Service** → **Database** → **Redis**

O por CLI:
```bash
railway add --plugin postgresql
railway add --plugin redis
```

---

## Paso 3 — Configurar variables de entorno

En Railway Dashboard → Tu servicio → **Variables**:

```
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET_KEY=<genera con: openssl rand -hex 32>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_CLINICAL=price_...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_MEDSCAN=medix-scans-prod
ENVIRONMENT=production
```

Railway inyecta automáticamente:
- `DATABASE_URL` (desde el plugin PostgreSQL)
- `REDIS_URL` (desde el plugin Redis)
- `PORT` (Railway lo asigna automáticamente)

---

## Paso 4 — Deploy del backend

```bash
# Desde la raíz del proyecto
cd /ruta/a/medix-ai

# Conectar al proyecto
railway link

# Deploy
railway up --service medix-backend

# Ver logs en tiempo real
railway logs --service medix-backend
```

---

## Paso 5 — Seed de la base de datos

```bash
# Ejecutar seed una sola vez
railway run python -m app.db.seed
```

---

## Paso 6 — Cargar SESAL RAG (contenido de muestra)

```bash
# Cargar 4 guías de muestra para testing inmediato
railway run python -m app.services.sesal_ingest --sample

# Verificar
railway run python -m app.services.sesal_ingest --status
```

Para cargar PDFs reales de SESAL:
```bash
# Subir el PDF al servidor
railway run bash -c "mkdir -p data/sesal && wget -O data/sesal/guia_dengue_2023.pdf <URL>"

# Ingestar
railway run python -m app.services.sesal_ingest --all
```

---

## Paso 7 — Configurar Stripe Webhook

```bash
# Obtener la URL de tu servicio Railway
railway domain  # Ej: medix-backend-production.up.railway.app

# En Stripe Dashboard → Webhooks → Add Endpoint:
# URL: https://medix-backend-production.up.railway.app/api/v1/subscription/webhook
# Eventos a escuchar:
#   ✅ checkout.session.completed
#   ✅ customer.subscription.updated
#   ✅ customer.subscription.deleted

# Copiar el Signing Secret → agregar como STRIPE_WEBHOOK_SECRET en Railway
```

---

## Paso 8 — Deploy de Workers (Celery)

Crear un segundo servicio en Railway para el worker:

```bash
railway up --service medix-worker
```

En las variables del servicio worker, agregar:
```
START_COMMAND=celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
```

---

## Paso 9 — Configurar Flutter app para producción

```bash
cd mobile

# Reemplazar la URL del backend
# En lib/services/api.dart, cambiar defaultValue:
# 'https://TU-DOMINIO.up.railway.app/api/v1'

# Build APK de release
flutter build apk --release \
  --dart-define=API_BASE_URL=https://medix-backend-production.up.railway.app/api/v1
```

---

## Paso 10 — Verificar todo

```bash
# Health check
curl https://medix-backend-production.up.railway.app/health
# Esperado: {"status":"ok","service":"medix-api"}

# Docs (desactivado en prod — ok)
# curl https://...up.railway.app/docs → 404

# Test de registro
curl -X POST https://medix-backend-production.up.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@unah.edu.hn","password":"test1234","first_name":"Test","last_name":"User","role":"student"}'
```

---

## Costos estimados Railway

| Servicio | Plan | Costo/mes |
|---|---|---|
| FastAPI Backend | Starter | ~$5-10 |
| PostgreSQL | Starter | ~$5 |
| Redis | Starter | ~$3 |
| Celery Worker | Starter | ~$5 |
| **Total MVP** | | **~$18-23/mes** |

**A partir de 300 usuarios Pro:** Migrar a AWS (ECS + RDS Aurora + ElastiCache).

---

## Variables GitHub Actions necesarias

En tu repositorio → Settings → Secrets:
```
RAILWAY_TOKEN        # railway whoami --token
RAILWAY_DOMAIN       # medix-backend-production.up.railway.app
ANTHROPIC_API_KEY    # para tests
ANDROID_KEYSTORE_BASE64  # keystore en base64 para APK firmado
```

---

## Estructura de deploy completa

```
Railway Project: medix-ai
├── medix-backend     (FastAPI — puerto 8000)
├── medix-worker      (Celery worker)
├── medix-beat        (Celery beat — reset rate limits a medianoche)
├── PostgreSQL        (plugin nativo Railway)
└── Redis             (plugin nativo Railway)
```
