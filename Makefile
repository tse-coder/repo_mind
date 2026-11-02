.PHONY: install dev-backend dev-frontend test lint clean

install:
	python -m venv venv
	. venv/bin/activate && pip install -e ".[dev]"

dev-backend:
	. venv/bin/activate && uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	. venv/bin/activate && python -m pytest -v

lint:
	. venv/bin/activate && ruff check backend/ tests/

clean:
	rm -rf __pycache__ .pytest_cache chroma_data/ logs/ *.egg-info dist/ build/
