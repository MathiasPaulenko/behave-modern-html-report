.PHONY: install install-dev test test-cov lint format demo report clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	python -m pytest

test-cov:
	python -m pytest --cov=behave_modern_html_report --cov-report=term-missing

lint:
	python -m ruff check .

format:
	python -m black .
	python -m ruff check --fix .

demo:
	python examples/demo_generator/generate_demo.py

report:
	behave --config-file=examples/behave_project/behave.ini examples/behave_project/features

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
