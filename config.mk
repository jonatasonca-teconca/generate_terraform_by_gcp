# ============================================================
# Configuração de Projetos e Recursos para Extração GCP
# ============================================================

# Lista de projetos a serem extraídos
# Adicione ou remova projetos conforme necessário
PROJECTS := \
	infra-sd-host \
	infra-sd-service

# ============================================================
# Configuração de Recursos por Projeto
# ============================================================
# Você pode criar targets personalizados aqui

# Exemplo: Extrair apenas redes de um projeto específico
extract-networks-only:
	@echo "Extraindo apenas recursos de rede..."
	# Customize o script Python para aceitar recursos específicos

# Exemplo: Extrair apenas storage
extract-storage-only:
	@echo "Extraindo apenas buckets de storage..."

# ============================================================
# Recursos Disponíveis
# ============================================================
# O script Python extrai automaticamente:
#
# 🌐 NETWORKING (ANÁLISE COMPLETA DE REDE):
# ✓ Networks (VPCs) - TODOS os parâmetros
#   - Description, MTU, Routing Mode
#   - IPv6 (ULA, ranges, access types)
#   - Delete default routes
#
# ✓ Subnets - TODOS os parâmetros
#   - IP ranges (primary + secondary ranges)
#   - Private Google Access (IPv4 e IPv6)
#   - Purpose, Role (load balancers)
#   - Stack Type, IPv6 configurations
#   - Flow Logs (agregação, sampling, metadata, filtros)
#
# ✓ Firewall Rules - TODOS os parâmetros
#   - Allow & Deny rules
#   - Source/Destination ranges
#   - Source/Target Tags
#   - Source/Target Service Accounts
#   - Priority, Direction, Disabled state
#   - Log Configuration (essencial!)
#
# ✓ Routes (rotas personalizadas)
#   - Next hops: gateway, IP, instance, VPN, ILB
#   - Priority, Tags, Description
#
# ✓ Cloud Routers
#   - BGP configuration (ASN, advertise mode)
#   - Advertised groups e ranges
#
# ✓ VPN Gateways & Tunnels
#   - HA VPN configuration
#   - IKE version, peer IP
#
# ✓ VPC Peering
#   - Export/Import custom routes
#   - Export/Import subnet routes with public IP
#
# 💾 COMPUTE & STORAGE:
# ✓ Compute Instances (VMs)
# ✓ Storage Buckets
# ✓ Cloud Functions
# ✓ GKE Clusters
# ✓ Cloud SQL Instances
# ✓ Pub/Sub Topics
# ✓ BigQuery Datasets
#
# 🔐 IAM:
# ✓ Service Accounts
# ✓ IAM Policies
#
# ============================================================

# Lista de recursos disponíveis para extração
AVAILABLE_RESOURCES := networks firewall compute storage functions gke sql pubsub bigquery iam

# Configurações regionais padrão
DEFAULT_REGION := southamerica-east1
DEFAULT_ZONE := southamerica-east1-a

# Regiões adicionais para verificar recursos
REGIONS := \
	us-central1 \
	us-east1 \
	southamerica-east1

# ============================================================
# Opções de Terraform
# ============================================================
TERRAFORM_VERSION := ~> 5.0
TERRAFORM_BACKEND := local  # Altere para 'gcs' se usar backend remoto

# Backend GCS (se necessário)
# TERRAFORM_BACKEND_BUCKET := my-terraform-state-bucket
# TERRAFORM_BACKEND_PREFIX := terraform/state
