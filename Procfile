web: find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; cd /app && uvicorn app.main:app --host 0.0.0.0 --port $PORT
