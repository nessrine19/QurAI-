.PHONY: up down build rebuild logs clean

# Start all containers
up:
	docker-compose up -d

# Stop all containers
down:
	docker-compose down

# Build containers
build:
	docker-compose build

# Rebuild and restart containers
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# View logs
logs:
	docker-compose logs -f

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker system prune -f

# Run tests
test:
	docker-compose exec backend poetry run pytest tests/ -v

# Initialize database
init-db:
	docker-compose exec db psql -U postgres -d qurai_db -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Help command
help:
	@echo "Available commands:"
	@echo "  make up        - Start all containers"
	@echo "  make down      - Stop all containers"
	@echo "  make build     - Build containers"
	@echo "  make rebuild   - Rebuild and restart containers"
	@echo "  make logs      - View container logs"
	@echo "  make clean     - Clean up containers and volumes"
	@echo "  make test      - Run tests"
	@echo "  make init-db   - Initialize database" 