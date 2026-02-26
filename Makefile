.PHONY: all build test lint fmt clean dev help

# Go services that exist under services/
SERVICES := auth-svc oob-svc collab-svc

# Python services that exist under services/
PYTHON_SERVICES := sim-orchestrator cyber-svc cbrn-svc asym-svc terror-svc intel-svc \
                   civilian-svc reporting-svc econ-svc infoops-svc gis-export-svc training-svc

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

## svc-test: Run tests for a single service (usage: make svc-test SVC=cyber-svc)
svc-test:
	@[ -n "$(SVC)" ] || (echo "ERROR: SVC is required. Example: make svc-test SVC=cyber-svc" && exit 1)
	@if [ -f "services/$(SVC)/go.mod" ]; then \
		cd services/$(SVC) && go test ./... -race; \
	else \
		cd services/$(SVC) && python -m pytest; \
	fi

## svc-lint: Lint a single service (usage: make svc-lint SVC=cyber-svc)
svc-lint:
	@[ -n "$(SVC)" ] || (echo "ERROR: SVC is required. Example: make svc-lint SVC=cyber-svc" && exit 1)
	@if [ -f "services/$(SVC)/go.mod" ]; then \
		cd services/$(SVC) && golangci-lint run ./...; \
	else \
		cd services/$(SVC) && ruff check .; \
	fi

## guard-services: Fail if CI service lists drift from services/ directory contents
guard-services:
	@echo "Checking service list consistency..."
	@ACTUAL=$$(ls services/ | sort | tr '\n' ' ' | sed 's/ *$$//'); \
	EXPECTED="agd-shared asym-svc auth-svc cbrn-svc civilian-svc collab-svc cyber-svc econ-svc gis-export-svc infoops-svc intel-svc oob-svc reporting-svc sim-engine sim-orchestrator terror-svc training-svc"; \
	if [ "$$ACTUAL" != "$$EXPECTED" ]; then \
		echo "ERROR: services/ directory contents do not match expected list."; \
		echo "  Actual:   $$ACTUAL"; \
		echo "  Expected: $$EXPECTED"; \
		exit 1; \
	fi
	@echo "OK: service list is consistent."

## docker-build: Build all Docker images
docker-build:
	docker buildx bake

## smoke-test: Run one-command smoke test against a running dev environment
smoke-test:
	bash scripts/smoke-test.sh

## migrate-smoke: Validate DB migration scripts (numbering, non-empty, optional live run)
migrate-smoke:
	bash scripts/db-migrate-smoke.sh

## security-scan: Run Trivy security scan
security-scan:
	trivy fs --exit-code 1 --severity HIGH,CRITICAL .

## proto-lint: Lint protobuf files with buf
proto-lint:
	cd services/sim-engine && buf lint proto/

## sbom: Generate SBOM
sbom:
	syft . -o spdx-json > sbom.json
