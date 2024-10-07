.PHONY: setup run clean

setup:
	uv venv --python 3.12
	uv pip install -r requirements.txt

run:
	uv run python main.py

clean:
	rm -rf .venv __pycache__

