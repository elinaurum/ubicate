.PHONY: instalar app test lint validar probar migrar kb ci

instalar:
	pip install -r requirements-dev.txt

app:
	streamlit run app.py

test:
	pytest

lint:
	ruff check src tests scripts

probar:
	python scripts/probar_proveedor.py

validar:
	python scripts/validar_datos.py

migrar:
	python scripts/migrar_datos_v0_v1.py

kb:
	python scripts/importar_kb.py

ci: lint test validar
