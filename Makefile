# ----- ANY -----
docker-build:
	@echo "generating project requirements..."
	@poetry export --without-hashes --format=requirements.txt > app/requirements.txt
	@echo "building Docker image ...";
	@docker build -t pedroegg/cloud-selenium:latest .
# ---------------

# ----- PROD -----
docker-push:
	@echo "pushing Docker image to registry...";
	@docker push pedroegg/cloud-selenium:latest
# ----------------

# ----- DEV ------
install:
	@sudo apt-get install pipx
	@pipx ensurepath
	@pipx install poetry==2.0.1
	@poetry install

run-dev:
	@cd app; ENV="development" uvicorn api.main:app --host 0.0.0.0 --port 8000

run-docker:
	@docker run --rm -p 8000:8000 pedroegg/cloud-selenium:latest
# ----------------
