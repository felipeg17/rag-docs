# RAG-Docs Makefile
# Basic Docker Compose operations

up: docker compose --profile full up -

up-backend: docker compose --profile backend up 

down: docker compose down

build: docker compose build

build-backend: docker compose build rag-docs-backend

rebuild: 
	docker compose build --no-cache
	docker compose --profile full up -d

logs: docker compose logs -f

ps: docker compose ps

clean: docker compose down --remove-orphans

prune:
	docker system prune -af --volumes
	@echo "Docker system pruned"
