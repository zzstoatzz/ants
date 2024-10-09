.PHONY: init setup dev run clean

init:
	uv venv --python 3.12
	uv pip install -r requirements.txt

setup: init
	uv pip install ./ants_rs

dev: init
	uv pip install ./ants_rs

run: setup
	uv run python main.py

clean:
	rm -rf .venv __pycache__
	rm -rf ants_rs/target

