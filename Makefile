# GrandHotel Agent - Makefile
# Zarządzanie całym stackiem Docker (agent, redis, mock-backend, mock-frontend)

.PHONY: help network build up down restart rebuild logs status clean \
        agent-up agent-down agent-logs agent-build \
        backend-up backend-down backend-logs backend-build \
        frontend-up frontend-down frontend-logs frontend-build

# Kolory dla output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Domyślny target
.DEFAULT_GOAL := help

help: ## Wyświetla pomoc
	@echo "$(CYAN)GrandHotel Agent - Dostępne komendy:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Przykłady użycia:$(RESET)"
	@echo "  make up        # Uruchom cały stack"
	@echo "  make rebuild   # Przebuduj i uruchom wszystko"
	@echo "  make logs      # Pokaż logi wszystkich serwisów"

# =============================================================================
# SIEĆ
# =============================================================================

network: ## Tworzy sieć grandhotel-network (jeśli nie istnieje)
	@echo "$(CYAN)Tworzenie sieci grandhotel-network...$(RESET)"
	@docker network inspect grandhotel-network >/dev/null 2>&1 || \
		docker network create grandhotel-network
	@echo "$(GREEN)✓ Sieć gotowa$(RESET)"

# =============================================================================
# CAŁY STACK
# =============================================================================

build: network ## Buduje wszystkie obrazy
	@echo "$(CYAN)Budowanie wszystkich obrazów...$(RESET)"
	@docker compose build
	@cd mock-backend && docker compose build
	@cd mock-frontend && docker compose build
	@echo "$(GREEN)✓ Wszystkie obrazy zbudowane$(RESET)"

up: network ## Uruchamia cały stack
	@echo "$(CYAN)Uruchamianie całego stacku...$(RESET)"
	@docker compose up -d
	@cd mock-backend && docker compose up -d
	@cd mock-frontend && docker compose up -d
	@echo "$(GREEN)✓ Stack uruchomiony$(RESET)"
	@echo ""
	@echo "$(YELLOW)Dostępne usługi:$(RESET)"
	@echo "  Agent:        http://localhost:8000"
	@echo "  Mock Backend: http://localhost:8081"
	@echo "  Frontend:     http://localhost:3000"

down: ## Zatrzymuje cały stack
	@echo "$(CYAN)Zatrzymywanie całego stacku...$(RESET)"
	@cd mock-frontend && docker compose down 2>/dev/null || true
	@cd mock-backend && docker compose down 2>/dev/null || true
	@docker compose down 2>/dev/null || true
	@echo "$(GREEN)✓ Stack zatrzymany$(RESET)"

restart: down up ## Restartuje cały stack

rebuild: down build up ## Przebudowuje i uruchamia cały stack

logs: ## Pokazuje logi wszystkich serwisów (follow)
	@echo "$(CYAN)Logi wszystkich serwisów (Ctrl+C aby wyjść):$(RESET)"
	@docker compose logs -f & \
		cd mock-backend && docker compose logs -f & \
		cd mock-frontend && docker compose logs -f

status: ## Pokazuje status kontenerów
	@echo "$(CYAN)Status kontenerów:$(RESET)"
	@echo ""
	@echo "$(YELLOW)Agent + Redis:$(RESET)"
	@docker compose ps
	@echo ""
	@echo "$(YELLOW)Mock Backend:$(RESET)"
	@cd mock-backend && docker compose ps
	@echo ""
	@echo "$(YELLOW)Mock Frontend:$(RESET)"
	@cd mock-frontend && docker compose ps

clean: down ## Usuwa kontenery, obrazy i volumes
	@echo "$(RED)Usuwanie kontenerów i obrazów...$(RESET)"
	@docker rmi grandhotel-agent:dev grandhotel-mock:dev grandhotel-frontend:dev 2>/dev/null || true
	@docker volume rm grandhotelagent_redis-data 2>/dev/null || true
	@echo "$(GREEN)✓ Wyczyszczono$(RESET)"

# =============================================================================
# AGENT (główny serwis + redis)
# =============================================================================

agent-build: network ## Buduje obraz agenta
	@echo "$(CYAN)Budowanie agenta...$(RESET)"
	@docker compose build

agent-up: network ## Uruchamia agenta + redis
	@echo "$(CYAN)Uruchamianie agenta + redis...$(RESET)"
	@docker compose up -d
	@echo "$(GREEN)✓ Agent dostępny na http://localhost:8000$(RESET)"

agent-down: ## Zatrzymuje agenta + redis
	@docker compose down

agent-logs: ## Logi agenta
	@docker compose logs -f agent

# =============================================================================
# MOCK BACKEND
# =============================================================================

backend-build: network ## Buduje mock-backend
	@echo "$(CYAN)Budowanie mock-backend...$(RESET)"
	@cd mock-backend && docker compose build

backend-up: network ## Uruchamia mock-backend
	@echo "$(CYAN)Uruchamianie mock-backend...$(RESET)"
	@cd mock-backend && docker compose up -d
	@echo "$(GREEN)✓ Mock backend dostępny na http://localhost:8081$(RESET)"

backend-down: ## Zatrzymuje mock-backend
	@cd mock-backend && docker compose down

backend-logs: ## Logi mock-backend
	@cd mock-backend && docker compose logs -f

# =============================================================================
# MOCK FRONTEND
# =============================================================================

frontend-build: network ## Buduje mock-frontend
	@echo "$(CYAN)Budowanie mock-frontend...$(RESET)"
	@cd mock-frontend && docker compose build

frontend-up: network ## Uruchamia mock-frontend
	@echo "$(CYAN)Uruchamianie mock-frontend...$(RESET)"
	@cd mock-frontend && docker compose up -d
	@echo "$(GREEN)✓ Frontend dostępny na http://localhost:3000$(RESET)"

frontend-down: ## Zatrzymuje mock-frontend
	@cd mock-frontend && docker compose down

frontend-logs: ## Logi mock-frontend
	@cd mock-frontend && docker compose logs -f

# =============================================================================
# DEV HELPERS
# =============================================================================

health: ## Sprawdza health check wszystkich serwisów
	@echo "$(CYAN)Sprawdzanie health check...$(RESET)"
	@echo ""
	@echo -n "Agent:        " && curl -sf http://localhost:8000/agent/health && echo " $(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Mock Backend: " && curl -sf http://localhost:8081/health && echo " $(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Frontend:     " && curl -sf http://localhost:3000 >/dev/null && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"

shell-agent: ## Otwiera shell w kontenerze agenta
	@docker exec -it grandhotel-agent /bin/sh

shell-backend: ## Otwiera shell w kontenerze mock-backend
	@docker exec -it grandhotel-mock /bin/sh

shell-frontend: ## Otwiera shell w kontenerze frontend
	@docker exec -it grandhotel-frontend /bin/sh
