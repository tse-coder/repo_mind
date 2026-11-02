.PHONY: install dev-backend dev-frontend test lint clean

install:
	uv sync --all-extras

dev-backend:
	uv run uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	uv run pytest -v

lint:
	uv run ruff check backend/ tests/

clean:
	rm -rf __pycache__ .pytest_cache chroma_data/ logs/ *.egg-info dist/ build/
