#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║         MEDIX AI — Deploy Automatizado en Railway               ║
# ║         bash deploy.sh                                          ║
# ╚══════════════════════════════════════════════════════════════════╝
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
step() { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}\n"; }

echo -e "${BOLD}"
echo "  ███╗   ███╗███████╗██████╗ ██╗██╗  ██╗     █████╗ ██╗"
echo "  ████╗ ████║██╔════╝██╔══██╗██║╚██╗██╔╝    ██╔══██╗██║"
echo "  ██╔████╔██║█████╗  ██║  ██║██║ ╚███╔╝     ███████║██║"
echo "  ██║╚██╔╝██║██╔══╝  ██║  ██║██║ ██╔██╗     ██╔══██║██║"
echo "  ██║ ╚═╝ ██║███████╗██████╔╝██║██╔╝ ██╗    ██║  ██║██║"
echo "  ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝"
echo -e "${NC}"
echo -e "  ${CYAN}Deploy Automatizado — Railway.app${NC}"
echo -e "  ${YELLOW}Honduras 🇭🇳  •  Beta Mode ON  •  v3.0.0${NC}\n"

step "PASO 1 — Verificando herramientas"

check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    warn "$1 no encontrado"
    return 1
  fi
  log "$1 ✓"
}

check_cmd node || { echo "  → Descarga Node.js LTS: https://nodejs.org"; exit 1; }
check_cmd git || { echo "  → Instala Git: https://git-scm.com"; exit 1; }

if ! command -v railway &>/dev/null; then
  info "Instalando Railway CLI..."
  npm install -g @railway/cli@latest
fi
log "Railway CLI ✓"

step "PASO 2 — Variables de entorno"

echo -e "${YELLOW}Solo necesito 2 valores:${NC}\n"

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo -e "1️⃣  ${BOLD}ANTHROPIC_API_KEY${NC}"
  echo "   Consola Anthropic: https://console.anthropic.com → API Keys"
  read -p "   → Pega tu API key (sk-ant-...): " ANTHROPIC_API_KEY
fi
[ -z "$ANTHROPIC_API_KEY" ] && { echo "❌ ANTHROPIC_API_KEY requerida"; exit 1; }
log "ANTHROPIC_API_KEY ✓"

JWT_SECRET=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
REDIS_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)
log "JWT y passwords generados automáticamente ✓"

step "PASO 3 — Git"

if [ ! -d ".git" ]; then
  git init
  git add .
  git commit -m "🚀 Medix AI v3.0 — Beta deploy inicial"
  log "Repositorio Git inicializado"
else
  git add .
  git diff --cached --quiet || git commit -m "🔄 Medix AI — actualizacion"
  log "Git actualizado"
fi

step "PASO 4 — Login Railway"

info "Se abrirá el browser para autenticarte..."
railway login
log "Autenticado en Railway ✓"

step "PASO 5 — Proyecto Railway"

railway init --name medix-ai 2>/dev/null || railway link 2>/dev/null || true
log "Proyecto Railway listo"

step "PASO 6 — Base de datos (PostgreSQL + Redis)"

railway add --plugin postgresql 2>/dev/null || warn "PostgreSQL ya configurado"
log "PostgreSQL ✓"
railway add --plugin redis 2>/dev/null || warn "Redis ya configurado"
log "Redis ✓"

step "PASO 7 — Variables en Railway"

railway variables set \
  ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  JWT_SECRET_KEY="$JWT_SECRET" \
  JWT_ALGORITHM="HS256" \
  JWT_EXPIRE_MINUTES="10080" \
  ENVIRONMENT="production" \
  BETA_MODE="true" \
  BETA_USERS_LIMIT="100" \
  CHROMA_PERSIST_DIR="/app/chroma_db" \
  PAYPAL_CLIENT_ID="" \
  PAYPAL_CLIENT_SECRET="" \
  PAYPAL_MODE="sandbox" \
  FIREBASE_PROJECT_ID="" \
  FIREBASE_SERVICE_ACCOUNT_JSON="" \
  2>/dev/null

log "Variables configuradas ✓"

step "PASO 8 — Deploy del backend"

echo -e "${YELLOW}Desplegando... (3-5 minutos)${NC}"
cd backend
railway up --detach
cd ..
log "Deploy iniciado ✓"

info "Esperando que arranque el servidor..."
sleep 50

step "PASO 9 — Obteniendo URL"

RAILWAY_URL=$(railway domain 2>/dev/null | grep -oE 'https://[^ ]+' | head -1) || true

if [ -z "$RAILWAY_URL" ]; then
  warn "No pude obtener la URL automáticamente."
  echo -e "${YELLOW}Ve a railway.app → tu proyecto → Settings → Domains${NC}"
  read -p "   → Pega la URL (https://...up.railway.app): " RAILWAY_URL
fi
log "URL: $RAILWAY_URL"

step "PASO 10 — Health check"

MAX=8; N=0
while [ $N -lt $MAX ]; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    log "Backend online ✓  →  $RAILWAY_URL"
    break
  fi
  N=$((N+1))
  warn "Intento $N/$MAX — esperando 20s... (HTTP $STATUS)"
  sleep 20
done

step "PASO 11 — Seed UNAH + UNICAH"

railway run python -m app.db.seed 2>/dev/null && log "Seed completado ✓" || \
  warn "Ejecuta manualmente: railway run python -m app.db.seed"

step "PASO 12 — Guías SESAL"

railway run python -m app.services.sesal_ingest --sample 2>/dev/null && \
  log "SESAL RAG cargado (4 guías) ✓" || \
  warn "Ejecuta: railway run python -m app.services.sesal_ingest --sample"

step "PASO 13 — Usuario admin"

echo -e "${YELLOW}Configura tu cuenta de administrador:${NC}"
read -p "   Email: " ADMIN_EMAIL
read -s -p "   Contraseña: " ADMIN_PASS; echo

railway run python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
async def mk():
    async with AsyncSessionLocal() as db:
        u = User(email='$ADMIN_EMAIL', password_hash=hash_password('$ADMIN_PASS'),
                 first_name='Admin', last_name='Medix', role='admin', subscription_tier='clinical')
        db.add(u); await db.commit()
        print('Admin creado:', '$ADMIN_EMAIL')
asyncio.run(mk())
" 2>/dev/null && log "Admin creado ✓" || warn "Crea el admin manualmente después"

step "PASO 14 — Actualizar Flutter"

BACKEND_API="${RAILWAY_URL}/api/v1"
sed -i "s|http://localhost:8000/api/v1|${BACKEND_API}|g" \
  mobile/lib/services/api.dart 2>/dev/null && \
  log "Flutter apuntando a producción ✓" || \
  warn "Actualiza manualmente la URL en mobile/lib/services/api.dart"

cat > .deploy-config << CONF
RAILWAY_URL=$RAILWAY_URL
BACKEND_API=$BACKEND_API
ADMIN_EMAIL=$ADMIN_EMAIL
DEPLOY_DATE=$(date -u +"%Y-%m-%d %H:%M UTC")
CONF

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗"
echo "║       🎉  MEDIX AI EN LÍNEA — HONDURAS 🇭🇳  🎉           ║"
echo "╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}🌐 Backend API:${NC}   $RAILWAY_URL"
echo -e "  ${CYAN}❤️  Health:${NC}       $RAILWAY_URL/health"
echo -e "  ${CYAN}🛡️  Admin:${NC}        Abre admin/dashboard.html"
echo ""
echo -e "${YELLOW}Beta Mode ACTIVO — primeros 100 usuarios reciben Pro gratis${NC}"
echo ""
echo -e "${BOLD}Próximos pasos:${NC}"
echo ""
echo "  1. Build APK Flutter:"
echo "     cd mobile"
echo "     flutter build apk --release \\"
echo "       --dart-define=API_BASE_URL=${BACKEND_API}"
echo ""
echo "  2. Cuando quieras activar pagos reales (PayPal):"
echo "     → developer.paypal.com → crear app"
echo "     → Railway Variables → PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET"
echo "     → Railway Variables → BETA_MODE=false"
echo ""
echo "  3. Admin Dashboard:"
echo "     → Abre admin/dashboard.html"
echo "     → Login: $ADMIN_EMAIL"
echo ""
echo -e "${GREEN}¡Medix AI está LIVE! 🏥🇭🇳${NC}"
