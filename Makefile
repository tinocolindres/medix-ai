.PHONY: help up up-dev down logs seed sesal-sample sesal-ingest sesal-status test lint flutter-run flutter-apk reset-limits gen-jwt-secret health admin-create

help:
	@echo ""
	@echo "🏥 Medix AI — Comandos disponibles (Sprint 3)"
	@echo "──────────────────────────────────────────────"
	@echo "  make up              → Levantar todos los servicios"
	@echo "  make up-dev          → Levantar con Stripe CLI (dev)"
	@echo "  make down            → Apagar servicios"
	@echo "  make logs            → Ver logs del backend"
	@echo "  make seed            → Poblar UNAH + UNICAH en DB"
	@echo "  make sesal-sample    → Cargar guías SESAL de muestra (testing)"
	@echo "  make sesal-ingest    → Ingestar PDFs reales en data/sesal/"
	@echo "  make sesal-status    → Ver documentos indexados en ChromaDB"
	@echo "  make test            → Ejecutar todos los tests"
	@echo "  make lint            → Lint Python con Ruff"
	@echo "  make flutter-run     → Correr Flutter en dispositivo"
	@echo "  make flutter-apk     → Build APK release"
	@echo "  make reset-limits    → Resetear rate limits manualmente"
	@echo "  make admin-create    → Crear usuario admin"
	@echo "  make health          → Health check del backend"
	@echo "  make gen-jwt-secret  → Generar JWT_SECRET_KEY seguro"
	@echo ""

up:
	docker-compose up --build -d
	@echo "✅ Medix AI Sprint 3 corriendo"
	@echo "📖 API: http://localhost:8000"
	@echo "📊 Docs: http://localhost:8000/docs"
	@echo "🛡️  Admin: file://$(PWD)/admin/dashboard.html"

up-dev:
	docker-compose --profile dev up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

logs-beat:
	docker-compose logs -f beat

seed:
	docker exec medix_backend python -m app.db.seed
	@echo "✅ Seed completado: UNAH + UNICAH"

sesal-sample:
	docker exec medix_backend python -m app.services.sesal_ingest --sample
	@echo "✅ 4 guías SESAL de muestra cargadas en ChromaDB"

sesal-ingest:
	docker exec medix_backend python -m app.services.sesal_ingest --all

sesal-status:
	docker exec medix_backend python -m app.services.sesal_ingest --status

test:
	cd backend && pip install pytest pytest-asyncio httpx aiosqlite -q && \
	pytest tests/ -v --tb=short

lint:
	cd backend && ruff check app/ --ignore E501 || true

reset-limits:
	docker exec medix_backend python -c "\
	from app.worker.tasks import reset_daily_rate_limits; \
	reset_daily_rate_limits.apply()"
	@echo "✅ Rate limits reseteados"

admin-create:
	@read -p "Email del admin: " email; \
	read -s -p "Contraseña: " pass; echo; \
	docker exec medix_backend python -c "\
	import asyncio; \
	from app.db.session import AsyncSessionLocal; \
	from app.models.user import User; \
	from app.core.security import hash_password; \
	async def create(): \
	    async with AsyncSessionLocal() as db: \
	        u = User(email='$$email', password_hash=hash_password('$$pass'), first_name='Admin', last_name='Medix', role='admin', subscription_tier='clinical'); \
	        db.add(u); await db.commit(); print('✅ Admin creado:', '$$email'); \
	asyncio.run(create())"

flutter-run:
	cd mobile && flutter pub get && flutter run

flutter-run-web:
	cd mobile && flutter run -d chrome

flutter-analyze:
	cd mobile && flutter analyze --no-fatal-infos || true

flutter-apk:
	cd mobile && flutter build apk --release \
		--dart-define=API_BASE_URL=https://your-domain.up.railway.app/api/v1
	@echo "✅ APK: mobile/build/app/outputs/flutter-apk/app-release.apk"

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend no disponible"

gen-jwt-secret:
	@echo "JWT_SECRET_KEY generado:"
	@openssl rand -hex 32
