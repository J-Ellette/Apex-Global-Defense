.PHONY: all build test lint fmt clean dev help

SERVICES := auth-svc oob-svc map-svc collab-svc notify-svc audit-svc
PYTHON_SERVICES := sim-orchestrator intel-svc ai-svc reporting-svc cbrn-svc cyber-svc

## help: Show this help message
help:
	@echo "Apex Global Defense — Makefile targets"
	@echo ""
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' | sed -e 's/^/ /'

## all: Build all services and frontend
all: build

## build: Build all Go services and frontend
build: build-go build-frontend

## build-go: Build all Go services
build-go:
	@for svc in $(SERVICES); do \
		echo "Building $$svc..."; \
		cd services/$$svc && go build ./... && cd ../..; \
	done

## build-frontend: Build the React frontend
build-frontend:
	cd frontend && npm ci && npm run build

## test: Run all tests
test: test-go test-python test-frontend

## test-go: Run Go service tests
test-go:
	@for svc in $(SERVICES); do \
		echo "Testing $$svc..."; \
		cd services/$$svc && go test ./... -race -coverprofile=coverage.out && cd ../..; \
	done

## test-python: Run Python service tests
test-python:
	@for svc in $(PYTHON_SERVICES); do \
		echo "Testing $$svc..."; \
		cd services/$$svc && python -m pytest && cd ../..; \
	done

## test-frontend: Run frontend tests
test-frontend:
	cd frontend && npm test -- --watchAll=false

## lint: Lint all services
lint: lint-go lint-python lint-frontend

## lint-go: Lint Go services
lint-go:
	@for svc in $(SERVICES); do \
		cd services/$$svc && golangci-lint run ./... && cd ../..; \
	done

## lint-python: Lint Python services
lint-python:
	@for svc in $(PYTHON_SERVICES); do \
		cd services/$$svc && ruff check . && cd ../..; \
	done

## lint-frontend: Lint frontend
lint-frontend:
	cd frontend && npm run lint

## fmt: Format all code
fmt: fmt-go fmt-python fmt-frontend

## fmt-go: Format Go code
fmt-go:
	@for svc in $(SERVICES); do \
		cd services/$$svc && gofmt -w . && cd ../..; \
	done

## fmt-python: Format Python code
fmt-python:
	@for svc in $(PYTHON_SERVICES); do \
		cd services/$$svc && ruff format . && cd ../..; \
	done

## fmt-frontend: Format frontend code
fmt-frontend:
	cd frontend && npm run format

## dev: Start local development environment
dev:
	docker compose -f docker-compose.dev.yml up --build

## dev-down: Stop local development environment
dev-down:
	docker compose -f docker-compose.dev.yml down -v

## db-migrate: Run database migrations
db-migrate:
	@echo "Running database migrations..."
	docker compose -f docker-compose.dev.yml exec postgres psql -U agd -d agd_dev -f /docker-entrypoint-initdb.d/001_schema.sql

## clean: Remove build artifacts
clean:
	@for svc in $(SERVICES); do \
		cd services/$$svc && go clean ./... && rm -f coverage.out && cd ../..; \
	done
	cd frontend && rm -rf dist node_modules

## docker-build: Build all Docker images
docker-build:
	docker buildx bake

## security-scan: Run Trivy security scan
security-scan:
	trivy fs --exit-code 1 --severity HIGH,CRITICAL .

## sbom: Generate SBOM
sbom:
	syft . -o spdx-json > sbom.json
