install:
	poetry install --all-extras

test:
	poetry run pytest -svv --showlocals tests

coverage:
	poetry run coverage run -m pytest tests
	poetry run coverage report -m
	poetry run coverage html

isort:
	poetry run isort tests/ tracker/

black:
	poetry run black .

mutation:
	poetry run mutmut run
	poetry run mutmut browse
