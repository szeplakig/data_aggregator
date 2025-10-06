

lint:
	poetry run flint format .
	poetry run flint check --fix .
