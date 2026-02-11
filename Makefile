# Makefile para extração de infraestrutura GCP para Terraform
# Uso: make extract-all ou make extract PROJECT=infra-sd-host

# ============================================================
# IMPORTAR CONFIGURAÇÕES
# ============================================================
include config.mk

# Projeto específico (usado com make extract PROJECT=nome)
PROJECT ?= 

# Recursos a serem extraídos (usado pelo script Python)
# Opções: networks, firewall, compute, storage, functions, gke, sql, pubsub, bigquery, iam
RESOURCES ?= all

# ============================================================
# VARIÁVEIS E CAMINHOS
# ============================================================
SCRIPT := gcp_to_terraform.py
ORG_SCRIPT := gcp_org_to_terraform.py
PYTHON := python3
TERRAFORM := terraform

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# ============================================================
# TARGETS PRINCIPAIS
# ============================================================

.PHONY: help
help: ## Mostra esta mensagem de ajuda
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Makefile - Extração GCP para Terraform$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Organização:$(NC) $(ORG_ID)"
	@echo "$(GREEN)Projetos configurados:$(NC)"
	@echo "  $(PROJECTS)"
	@echo ""
	@echo "$(GREEN)Targets disponíveis:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Exemplos de uso:$(NC)"
	@echo "  $(YELLOW)Organização:$(NC)"
	@echo "  make extract-org              # Extrai recursos da organização"
	@echo "  make extract-everything       # Extrai organização + projetos"
	@echo ""
	@echo "  $(YELLOW)Projetos:$(NC)"
	@echo "  make extract-all              # Extrai todos os projetos"
	@echo "  make extract PROJECT=teconca-data-dev"
	@echo ""

.DEFAULT_GOAL := help

# ============================================================
# EXTRAÇÃO DE PROJETOS
# ============================================================

.PHONY: extract
extract: ## Extrai um projeto específico (make extract PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@echo "$(YELLOW)Exemplo: make extract PROJECT=infra-sd-host$(NC)"
	@exit 1
endif
	@echo "$(BLUE)🚀 Extraindo projeto: $(PROJECT)$(NC)"
	@$(PYTHON) $(SCRIPT) $(PROJECT)
	@echo "$(GREEN)✅ Projeto $(PROJECT) extraído com sucesso!$(NC)"

.PHONY: extract-all
extract-all: ## Extrai todos os projetos configurados
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Extraindo todos os projetos$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@$(foreach proj,$(PROJECTS), \
		echo ""; \
		echo "$(YELLOW)📦 Processando: $(proj)$(NC)"; \
		$(PYTHON) $(SCRIPT) $(proj) || echo "$(RED)⚠️  Erro ao extrair $(proj)$(NC)"; \
		echo ""; \
	)
	@echo "$(GREEN)✅ Extração de todos os projetos concluída!$(NC)"

.PHONY: re-extract
re-extract: clean extract ## Remove e extrai novamente um projeto (make re-extract PROJECT=nome)

.PHONY: re-extract-all
re-extract-all: clean-all extract-all ## Remove e extrai novamente todos os projetos

.PHONY: extract-specific
extract-specific: ## Extrai recursos específicos (make extract-specific PROJECT=nome RESOURCES=networks,firewall)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
ifndef RESOURCES
	@echo "$(RED)❌ Erro: Especifique os recursos com RESOURCES=networks,firewall$(NC)"
	@echo "$(YELLOW)Recursos disponíveis: $(AVAILABLE_RESOURCES)$(NC)"
	@exit 1
endif
	@echo "$(BLUE)🚀 Extraindo recursos de $(PROJECT): $(RESOURCES)$(NC)"
	@$(PYTHON) $(SCRIPT) $(PROJECT) --resources $(RESOURCES)
	@echo "$(GREEN)✅ Recursos extraídos com sucesso!$(NC)"

.PHONY: extract-region
extract-region: ## Extrai projeto de uma região específica (make extract-region PROJECT=nome REGION=southamerica-east1)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@REGION=$(or $(REGION),$(DEFAULT_REGION)); \
	echo "$(BLUE)🚀 Extraindo projeto $(PROJECT) na região $$REGION$(NC)"; \
	$(PYTHON) $(SCRIPT) $(PROJECT) --region $$REGION
	@echo "$(GREEN)✅ Projeto extraído com sucesso!$(NC)"

# ============================================================
# EXTRAÇÃO DE ORGANIZAÇÃO
# ============================================================

.PHONY: extract-org
extract-org: ## Extrai recursos da organização (folders, policies, IAM, tags)
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Extraindo Organização: $(ORG_ID)$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@$(PYTHON) $(ORG_SCRIPT) $(ORG_ID)
	@echo "$(GREEN)✅ Organização extraída com sucesso!$(NC)"

.PHONY: extract-everything
extract-everything: extract-org extract-all ## Extrai TUDO: organização + todos os projetos
	@echo ""
	@echo "$(GREEN)✅ Extração completa concluída!$(NC)"
	@echo "$(BLUE)📊 Estrutura extraída:$(NC)"
	@echo "  • Organização: org-$(ORG_ID)/"
	@$(foreach proj,$(PROJECTS), \
		echo "  • Projeto: $(proj)/"; \
	)
	@echo ""

.PHONY: init-org
init-org: ## Inicializa Terraform na organização
	@if [ -d "org-$(ORG_ID)" ]; then \
		echo "$(BLUE)🔧 Inicializando Terraform em org-$(ORG_ID)$(NC)"; \
		cd org-$(ORG_ID) && $(TERRAFORM) init; \
		echo "$(GREEN)✅ Terraform inicializado$(NC)"; \
	else \
		echo "$(RED)❌ Diretório org-$(ORG_ID) não encontrado$(NC)"; \
		echo "$(YELLOW)Execute: make extract-org$(NC)"; \
		exit 1; \
	fi

# ============================================================
# TERRAFORM - OPERAÇÕES
# ============================================================

.PHONY: init
init: ## Inicializa Terraform para um projeto (make init PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@if [ -d "$(PROJECT)" ]; then \
		echo "$(BLUE)🔧 Inicializando Terraform em $(PROJECT)$(NC)"; \
		cd $(PROJECT) && $(TERRAFORM) init; \
		echo "$(GREEN)✅ Terraform inicializado em $(PROJECT)$(NC)"; \
	else \
		echo "$(RED)❌ Diretório $(PROJECT) não encontrado$(NC)"; \
		exit 1; \
	fi

.PHONY: init-all
init-all: ## Inicializa Terraform em todos os projetos
	@echo "$(BLUE)🔧 Inicializando Terraform em todos os projetos$(NC)"
	@$(foreach proj,$(PROJECTS), \
		if [ -d "$(proj)" ]; then \
			echo ""; \
			echo "$(YELLOW)📦 Inicializando: $(proj)$(NC)"; \
			cd $(proj) && $(TERRAFORM) init && cd ..; \
		fi; \
	)
	@echo "$(GREEN)✅ Terraform inicializado em todos os projetos$(NC)"

.PHONY: validate
validate: ## Valida configuração Terraform (make validate PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@if [ -d "$(PROJECT)" ]; then \
		echo "$(BLUE)✓ Validando $(PROJECT)$(NC)"; \
		cd $(PROJECT) && $(TERRAFORM) validate; \
	else \
		echo "$(RED)❌ Diretório $(PROJECT) não encontrado$(NC)"; \
		exit 1; \
	fi

.PHONY: validate-all
validate-all: ## Valida todos os projetos
	@$(foreach proj,$(PROJECTS), \
		if [ -d "$(proj)" ]; then \
			echo "$(YELLOW)Validando: $(proj)$(NC)"; \
			cd $(proj) && $(TERRAFORM) validate && cd ..; \
		fi; \
	)

.PHONY: plan
plan: ## Gera plano Terraform (make plan PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@if [ -d "$(PROJECT)" ]; then \
		echo "$(BLUE)📋 Gerando plano para $(PROJECT)$(NC)"; \
		cd $(PROJECT) && $(TERRAFORM) plan; \
	else \
		echo "$(RED)❌ Diretório $(PROJECT) não encontrado$(NC)"; \
		exit 1; \
	fi

.PHONY: plan-all
plan-all: ## Gera plano para todos os projetos
	@$(foreach proj,$(PROJECTS), \
		if [ -d "$(proj)" ]; then \
			echo ""; \
			echo "$(YELLOW)📋 Plano: $(proj)$(NC)"; \
			cd $(proj) && $(TERRAFORM) plan && cd ..; \
		fi; \
	)

.PHONY: fmt
fmt: ## Formata arquivos Terraform (make fmt PROJECT=nome ou fmt-all)
ifdef PROJECT
	@if [ -d "$(PROJECT)" ]; then \
		echo "$(BLUE)✨ Formatando $(PROJECT)$(NC)"; \
		cd $(PROJECT) && $(TERRAFORM) fmt; \
	fi
else
	@echo "$(YELLOW)Use: make fmt PROJECT=nome ou make fmt-all$(NC)"
endif

.PHONY: fmt-all
fmt-all: ## Formata todos os projetos
	@echo "$(BLUE)✨ Formatando todos os arquivos Terraform$(NC)"
	@$(foreach proj,$(PROJECTS), \
		if [ -d "$(proj)" ]; then \
			echo "  Formatando: $(proj)"; \
			cd $(proj) && $(TERRAFORM) fmt && cd ..; \
		fi; \
	)
	@echo "$(GREEN)✅ Formatação concluída$(NC)"

# ============================================================
# INFORMAÇÕES E LISTAGENS
# ============================================================

.PHONY: list
list: ## Lista todos os projetos configurados
	@echo "$(BLUE)📋 Projetos configurados:$(NC)"
	@$(foreach proj,$(PROJECTS), \
		if [ -d "$(proj)" ]; then \
			echo "  $(GREEN)✓ $(proj)$(NC) (extraído)"; \
		else \
			echo "  $(RED)✗ $(proj)$(NC) (não extraído)"; \
		fi; \
	)

.PHONY: status
status: ## Mostra status de todos os projetos
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Status dos Projetos$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@$(foreach proj,$(PROJECTS), \
		echo ""; \
		echo "$(YELLOW)📦 $(proj)$(NC)"; \
		if [ -d "$(proj)" ]; then \
			echo "  Status: $(GREEN)Extraído$(NC)"; \
			if [ -f "$(proj)/README.md" ]; then \
				echo "  Arquivos:"; \
				ls -1 $(proj)/*.tf 2>/dev/null | sed 's|$(proj)/|    - |' || echo "    Nenhum arquivo .tf"; \
			fi; \
			if [ -d "$(proj)/.terraform" ]; then \
				echo "  Terraform: $(GREEN)Inicializado$(NC)"; \
			else \
				echo "  Terraform: $(YELLOW)Não inicializado$(NC)"; \
			fi; \
		else \
			echo "  Status: $(RED)Não extraído$(NC)"; \
		fi; \
	)
	@echo ""

.PHONY: summary
summary: ## Resumo de recursos extraídos
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Resumo de Recursos Extraídos$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@$(foreach proj,$(PROJECTS), \
		if [ -f "$(proj)/README.md" ]; then \
			echo ""; \
			echo "$(YELLOW)📦 $(proj)$(NC)"; \
			grep -A 10 "## Recursos Extraídos" "$(proj)/README.md" | grep "^-" || echo "  Sem informações"; \
		fi; \
	)
	@echo ""

# ============================================================
# LIMPEZA
# ============================================================

.PHONY: clean
clean: ## Remove arquivos gerados de um projeto (make clean PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@echo "$(YELLOW)🗑️  Removendo arquivos de $(PROJECT)$(NC)"
	@if [ -d "$(PROJECT)" ]; then \
		rm -rf $(PROJECT)/.terraform* $(PROJECT)/terraform.tfstate* $(PROJECT)/*.tfplan; \
		echo "$(GREEN)✅ Cache do Terraform removido de $(PROJECT)$(NC)"; \
	fi

.PHONY: clean-all
clean-all: ## Remove cache do Terraform de todos os projetos
	@echo "$(YELLOW)🗑️  Limpando cache do Terraform$(NC)"
	@$(foreach proj,$(PROJECTS), \
		if [ -d "$(proj)" ]; then \
			rm -rf $(proj)/.terraform* $(proj)/terraform.tfstate* $(proj)/*.tfplan; \
			echo "  Limpo: $(proj)"; \
		fi; \
	)
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

.PHONY: destroy-extracted
destroy-extracted: ## Remove completamente um projeto extraído (make destroy-extracted PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@echo "$(RED)⚠️  ATENÇÃO: Isso removerá TODOS os arquivos de $(PROJECT)!$(NC)"
	@read -p "Continuar? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	@rm -rf $(PROJECT)
	@echo "$(GREEN)✅ Projeto $(PROJECT) removido$(NC)"

.PHONY: destroy-all-extracted
destroy-all-extracted: ## Remove TODOS os projetos extraídos
	@echo "$(RED)⚠️  ATENÇÃO: Isso removerá TODOS os projetos extraídos!$(NC)"
	@read -p "Continuar? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	@$(foreach proj,$(PROJECTS), \
		rm -rf $(proj); \
		echo "  Removido: $(proj)"; \
	)
	@echo "$(GREEN)✅ Todos os projetos removidos$(NC)"

# ============================================================
# UTILITÁRIOS
# ============================================================

.PHONY: check-gcloud
check-gcloud: ## Verifica autenticação e projetos GCP
	@echo "$(BLUE)🔍 Verificando autenticação GCP$(NC)"
	@gcloud auth list
	@echo ""
	@echo "$(BLUE)📋 Projetos acessíveis:$(NC)"
	@gcloud projects list --filter="projectId:($(shell echo $(PROJECTS) | tr ' ' ' OR '))" --format="table(projectId,name)"
	@echo ""
	@echo "$(BLUE)🌎 Região padrão configurada: $(DEFAULT_REGION)$(NC)"
	@echo "$(BLUE)📍 Zona padrão configurada: $(DEFAULT_ZONE)$(NC)"

.PHONY: show-config
show-config: ## Mostra configurações do config.mk
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Configurações (config.mk)$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Projetos:$(NC)"
	@echo "  $(PROJECTS)"
	@echo ""
	@echo "$(GREEN)Região/Zona Padrão:$(NC)"
	@echo "  Região: $(DEFAULT_REGION)"
	@echo "  Zona:   $(DEFAULT_ZONE)"
	@echo ""
	@echo "$(GREEN)Regiões Disponíveis:$(NC)"
	@echo "  $(REGIONS)"
	@echo ""
	@echo "$(GREEN)Recursos Disponíveis:$(NC)"
	@echo "  $(AVAILABLE_RESOURCES)"
	@echo ""

.PHONY: check-tools
check-tools: ## Verifica se as ferramentas necessárias estão instaladas
	@echo "$(BLUE)🔧 Verificando ferramentas$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "  $(GREEN)✓ Python3$(NC)" || echo "  $(RED)✗ Python3 não encontrado$(NC)"
	@command -v terraform >/dev/null 2>&1 && echo "  $(GREEN)✓ Terraform$(NC)" || echo "  $(RED)✗ Terraform não encontrado$(NC)"
	@command -v gcloud >/dev/null 2>&1 && echo "  $(GREEN)✓ Google Cloud SDK$(NC)" || echo "  $(RED)✗ gcloud não encontrado$(NC)"
	@[ -f "$(SCRIPT)" ] && echo "  $(GREEN)✓ Script de extração$(NC)" || echo "  $(RED)✗ Script $(SCRIPT) não encontrado$(NC)"

.PHONY: open-docs
open-docs: ## Abre documentação de um projeto (make open-docs PROJECT=nome)
ifndef PROJECT
	@echo "$(RED)❌ Erro: Especifique o projeto com PROJECT=nome$(NC)"
	@exit 1
endif
	@if [ -f "$(PROJECT)/README.md" ]; then \
		open "$(PROJECT)/README.md" || cat "$(PROJECT)/README.md"; \
	else \
		echo "$(RED)❌ README.md não encontrado em $(PROJECT)$(NC)"; \
	fi

# ============================================================
# WORKFLOW COMPLETO
# ============================================================

.PHONY: full-setup
full-setup: extract-everything init-org init-all validate-all ## Workflow completo: extrair tudo + inicializar + validar
	@echo "$(GREEN)✅ Setup completo finalizado!$(NC)"
	@echo "$(YELLOW)Próximo passo: make plan PROJECT=<nome>$(NC)"

.PHONY: quick-start
quick-start: check-tools extract-everything ## Quick start: verifica ferramentas e extrai tudo
	@echo "$(GREEN)✅ Quick start concluído!$(NC)"
	@echo "$(YELLOW)Próximos passos:$(NC)"
	@echo "  1. make init-org"
	@echo "  2. make init-all"
	@echo "  3. make plan PROJECT=<nome>"
