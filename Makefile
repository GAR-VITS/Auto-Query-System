.PHONY: up down seed index test eval lint demo clean

up:
	docker compose up -d

down:
	docker compose down

seed:
	python backend/db/seed/generate.py

index:
	python -m backend.app.memory.store --reindex

test:
	pytest backend/tests/unit -v

eval:
	python backend/tests/eval/run_eval.py

lint:
	python -m ruff check backend || echo "Ruff check done"

demo: seed index
	@echo "=========================================================="
	@echo " Starting NexusDB in DEMO_MODE"
	@echo " Frontend: http://localhost:5173"
	@echo " Backend:  http://localhost:8000"
	@echo ""
	@echo " Demo Logins (Development only):"
	@echo " - Viewer:         viewer@nexusdb.local / viewer123"
	@echo " - Branch Officer: officer@nexusdb.local / officer123"
	@echo " - Credit Manager: manager@nexusdb.local / manager123"
	@echo " - Admin:          admin@nexusdb.local / admin123"
	@echo "=========================================================="
	python -m uvicorn app.main:app --app-dir backend --port 8000 --reload
