run:
	docker-compose up -d

up:
	docker-compose up

down:
	docker-compose down

test:
	pytest tests/

test-cov:
	pytest --cov=src tests/

test-html:
	pytest --cov=src tests/ --cov-report=html

format:
	black .
