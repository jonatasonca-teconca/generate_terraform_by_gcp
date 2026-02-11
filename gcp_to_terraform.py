#!/usr/bin/env python3
"""
Script para extrair infraestrutura do GCP e gerar arquivos Terraform
Uso: python3 gcp_to_terraform.py <project-id>
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Any


class GCPToTerraform:
    def __init__(self, project_id: str, output_dir: str = None):
        self.project_id = project_id
        self.output_dir = output_dir or f"./{project_id}"
        self.resources = {}
        
    def run_gcloud(self, command: str) -> Dict:
        """Executa comando gcloud e retorna JSON"""
        try:
            full_cmd = f"gcloud {command} --project={self.project_id} --format=json"
            result = subprocess.run(
                full_cmd.split(),
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout) if result.stdout else []
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Erro ao executar: {command}")
            print(f"    {e.stderr}")
            return []
        except json.JSONDecodeError:
            return []
    
    def extract_networks(self):
        """Extrai VPCs e Subnets"""
        print("📡 Extraindo Networks...")
        networks = self.run_gcloud("compute networks list")
        self.resources['networks'] = networks
        
        subnets = self.run_gcloud("compute networks subnets list")
        self.resources['subnets'] = subnets
        
        print(f"   ✓ {len(networks)} VPCs encontradas")
        print(f"   ✓ {len(subnets)} Subnets encontradas")
    
    def extract_firewall(self):
        """Extrai regras de firewall"""
        print("🔥 Extraindo Firewall Rules...")
        firewalls = self.run_gcloud("compute firewall-rules list")
        self.resources['firewalls'] = firewalls
        print(f"   ✓ {len(firewalls)} regras encontradas")
    
    def extract_routes(self):
        """Extrai rotas personalizadas"""
        print("🛣️  Extraindo Routes...")
        routes = self.run_gcloud("compute routes list")
        self.resources['routes'] = routes
        print(f"   ✓ {len(routes)} rotas encontradas")
    
    def extract_routers(self):
        """Extrai Cloud Routers (para Cloud NAT, VPN, etc.)"""
        print("🔀 Extraindo Cloud Routers...")
        routers = self.run_gcloud("compute routers list")
        self.resources['routers'] = routers
        print(f"   ✓ {len(routers)} routers encontrados")
    
    def extract_vpn_gateways(self):
        """Extrai VPN Gateways"""
        print("🔐 Extraindo VPN Gateways...")
        vpn_gateways = self.run_gcloud("compute vpn-gateways list")
        self.resources['vpn_gateways'] = vpn_gateways
        print(f"   ✓ {len(vpn_gateways)} VPN gateways encontrados")
        
        # VPN Tunnels
        vpn_tunnels = self.run_gcloud("compute vpn-tunnels list")
        self.resources['vpn_tunnels'] = vpn_tunnels
        print(f"   ✓ {len(vpn_tunnels)} VPN tunnels encontrados")
    
    def extract_peering(self):
        """Extrai VPC Peering connections"""
        print("🔗 Extraindo VPC Peering...")
        peerings = []
        for net in self.resources.get('networks', []):
            net_name = net.get('name', '')
            if net.get('peerings'):
                for peering in net['peerings']:
                    peerings.append({
                        'network': net_name,
                        'peering': peering
                    })
        self.resources['peerings'] = peerings
        print(f"   ✓ {len(peerings)} peering connections encontradas")
    
    def extract_compute(self):
        """Extrai instâncias Compute Engine"""
        print("💻 Extraindo Compute Instances...")
        instances = self.run_gcloud("compute instances list")
        self.resources['instances'] = instances
        print(f"   ✓ {len(instances)} instâncias encontradas")
    
    def extract_storage(self):
        """Extrai buckets Cloud Storage"""
        print("🗄️  Extraindo Storage Buckets...")
        buckets = self.run_gcloud("storage buckets list")
        self.resources['buckets'] = buckets
        print(f"   ✓ {len(buckets)} buckets encontrados")
    
    def extract_functions(self):
        """Extrai Cloud Functions"""
        print("⚡ Extraindo Cloud Functions...")
        functions = self.run_gcloud("functions list")
        self.resources['functions'] = functions
        print(f"   ✓ {len(functions)} functions encontradas")
    
    def extract_gke(self):
        """Extrai clusters GKE"""
        print("☸️  Extraindo GKE Clusters...")
        clusters = self.run_gcloud("container clusters list")
        self.resources['gke_clusters'] = clusters
        print(f"   ✓ {len(clusters)} clusters encontrados")
    
    def extract_sql(self):
        """Extrai instâncias Cloud SQL"""
        print("🗃️  Extraindo Cloud SQL...")
        instances = self.run_gcloud("sql instances list")
        self.resources['sql_instances'] = instances
        print(f"   ✓ {len(instances)} instâncias SQL encontradas")
    
    def extract_pubsub(self):
        """Extrai tópicos e subscriptions Pub/Sub"""
        print("📬 Extraindo Pub/Sub...")
        topics = self.run_gcloud("pubsub topics list")
        self.resources['pubsub_topics'] = topics
        print(f"   ✓ {len(topics)} tópicos encontrados")
    
    def extract_bigquery(self):
        """Extrai datasets BigQuery"""
        print("📊 Extraindo BigQuery Datasets...")
        datasets = self.run_gcloud("bq ls --project_id")
        self.resources['bigquery_datasets'] = datasets
        print(f"   ✓ {len(datasets)} datasets encontrados")
    
    def extract_service_accounts(self):
        """Extrai Service Accounts"""
        print("🔑 Extraindo Service Accounts...")
        sas = self.run_gcloud("iam service-accounts list")
        self.resources['service_accounts'] = sas
        print(f"   ✓ {len(sas)} service accounts encontradas")
    
    def extract_cloud_run(self):
        """Extrai Cloud Run services"""
        print("🏃 Extraindo Cloud Run...")
        services = self.run_gcloud("run services list")
        self.resources['cloud_run_services'] = services
        print(f"   ✓ {len(services)} services encontrados")
    
    def extract_cloud_scheduler(self):
        """Extrai Cloud Scheduler jobs"""
        print("⏰ Extraindo Cloud Scheduler...")
        jobs = self.run_gcloud("scheduler jobs list")
        self.resources['scheduler_jobs'] = jobs
        print(f"   ✓ {len(jobs)} jobs encontrados")
    
    def extract_secrets(self):
        """Extrai Secret Manager secrets"""
        print("🔒 Extraindo Secret Manager...")
        secrets = self.run_gcloud("secrets list")
        self.resources['secrets'] = secrets
        print(f"   ✓ {len(secrets)} secrets encontrados")
    
    def extract_kms(self):
        """Extrai KMS keyrings e keys"""
        print("🔐 Extraindo KMS...")
        # KMS requer região/location
        keyrings = self.run_gcloud("kms keyrings list --location=global")
        self.resources['kms_keyrings'] = keyrings
        print(f"   ✓ {len(keyrings)} keyrings encontrados")
    
    def extract_dns(self):
        """Extrai Cloud DNS zones"""
        print("🌐 Extraindo Cloud DNS...")
        zones = self.run_gcloud("dns managed-zones list")
        self.resources['dns_zones'] = zones
        print(f"   ✓ {len(zones)} DNS zones encontradas")
    
    def extract_load_balancers(self):
        """Extrai Load Balancers"""
        print("⚖️  Extraindo Load Balancers...")
        # URL Maps (HTTP(S) LB)
        url_maps = self.run_gcloud("compute url-maps list")
        self.resources['url_maps'] = url_maps
        
        # Backend Services
        backends = self.run_gcloud("compute backend-services list")
        self.resources['backend_services'] = backends
        
        # Target Proxies
        target_https = self.run_gcloud("compute target-https-proxies list")
        target_http = self.run_gcloud("compute target-http-proxies list")
        self.resources['target_https_proxies'] = target_https
        self.resources['target_http_proxies'] = target_http
        
        # Forwarding Rules
        forwarding_rules = self.run_gcloud("compute forwarding-rules list")
        self.resources['forwarding_rules'] = forwarding_rules
        
        print(f"   ✓ {len(url_maps)} URL maps")
        print(f"   ✓ {len(backends)} backend services")
        print(f"   ✓ {len(forwarding_rules)} forwarding rules")
    
    def extract_redis(self):
        """Extrai Memorystore Redis instances"""
        print("🗄️  Extraindo Redis (Memorystore)...")
        instances = self.run_gcloud("redis instances list")
        self.resources['redis_instances'] = instances
        print(f"   ✓ {len(instances)} instâncias Redis encontradas")
    
    def extract_artifact_registry(self):
        """Extrai Artifact Registry repositories"""
        print("📦 Extraindo Artifact Registry...")
        repos = self.run_gcloud("artifacts repositories list")
        self.resources['artifact_repos'] = repos
        print(f"   ✓ {len(repos)} repositórios encontrados")
    
    def extract_composer(self):
        """Extrai Cloud Composer (Airflow) environments"""
        print("🎼 Extraindo Cloud Composer...")
        envs = self.run_gcloud("composer environments list")
        self.resources['composer_envs'] = envs
        print(f"   ✓ {len(envs)} environments encontrados")
    
    def extract_dataflow(self):
        """Extrai Dataflow jobs"""
        print("🌊 Extraindo Dataflow...")
        jobs = self.run_gcloud("dataflow jobs list")
        self.resources['dataflow_jobs'] = jobs
        print(f"   ✓ {len(jobs)} jobs encontrados")
    
    def extract_iam_policies(self):
        """Extrai IAM Policies do projeto"""
        print("🔐 Extraindo IAM Policies...")
        try:
            # Obter IAM policy do projeto
            policy = self.run_gcloud(f"projects get-iam-policy {self.project_id}")
            self.resources['iam_policy'] = policy
            
            # Contar bindings
            bindings_count = len(policy.get('bindings', [])) if isinstance(policy, dict) else 0
            print(f"   ✓ {bindings_count} role bindings encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair IAM policy: {e}")
            self.resources['iam_policy'] = {}
    
    def extract_instance_groups(self):
        """Extrai Managed Instance Groups e Instance Templates"""
        print("🖥️  Extraindo Instance Groups e Templates...")
        
        # Instance Templates
        templates = self.run_gcloud("compute instance-templates list")
        self.resources['instance_templates'] = templates
        print(f"   ✓ {len(templates)} instance templates encontrados")
        
        # Managed Instance Groups (regionais e zonais)
        migs = self.run_gcloud("compute instance-groups managed list")
        self.resources['managed_instance_groups'] = migs
        print(f"   ✓ {len(migs)} managed instance groups encontrados")
        
        # Unmanaged Instance Groups
        uigs = self.run_gcloud("compute instance-groups unmanaged list")
        self.resources['unmanaged_instance_groups'] = uigs
        print(f"   ✓ {len(uigs)} unmanaged instance groups encontrados")
    
    def extract_cloud_nat(self):
        """Extrai Cloud NAT configurations"""
        print("🌐 Extraindo Cloud NAT...")
        
        # Cloud NAT é configurado por router e região
        all_nats = []
        routers = self.resources.get('routers', [])
        
        for router in routers:
            router_name = router.get('name', '')
            region = router.get('region', '').split('/')[-1] if router.get('region') else ''
            
            if router_name and region:
                try:
                    nats = self.run_gcloud(f"compute routers nats list --router={router_name} --region={region}")
                    for nat in nats:
                        nat['router_name'] = router_name
                        nat['region'] = region
                        all_nats.append(nat)
                except:
                    pass
        
        self.resources['cloud_nats'] = all_nats
        print(f"   ✓ {len(all_nats)} Cloud NAT encontrados")
    
    def extract_disks(self):
        """Extrai Compute Disks persistentes"""
        print("💾 Extraindo Compute Disks...")
        
        # Disks
        disks = self.run_gcloud("compute disks list")
        self.resources['compute_disks'] = disks
        print(f"   ✓ {len(disks)} discos encontrados")
        
        # Snapshots
        snapshots = self.run_gcloud("compute snapshots list")
        self.resources['compute_snapshots'] = snapshots
        print(f"   ✓ {len(snapshots)} snapshots encontrados")
    
    def extract_network_endpoint_groups(self):
        """Extrai Network Endpoint Groups (NEGs)"""
        print("🎯 Extraindo Network Endpoint Groups...")
        
        # NEGs podem ser zonais ou regionais
        negs = self.run_gcloud("compute network-endpoint-groups list")
        self.resources['network_endpoint_groups'] = negs
        print(f"   ✓ {len(negs)} NEGs encontrados")
    
    def extract_bigquery_extended(self):
        """Extrai BigQuery de forma mais completa"""
        print("📊 Extraindo BigQuery (estendido)...")
        # Datasets já extraídos, vamos adicionar tables
        datasets = self.resources.get('bigquery_datasets', [])
        
        all_tables = []
        for dataset in datasets[:3]:  # Limitar a 3 datasets para não demorar
            dataset_id = dataset.get('id', '').split(':')[-1] if dataset.get('id') else ''
            if dataset_id:
                try:
                    tables = self.run_gcloud(f"bq ls --project_id={self.project_id} {dataset_id}")
                    all_tables.extend(tables)
                except:
                    pass
        
        self.resources['bigquery_tables'] = all_tables
        print(f"   ✓ {len(all_tables)} tabelas encontradas (amostra)")
    
    def extract_all(self):
        """Extrai todos os recursos"""
        print(f"\n🚀 Iniciando extração do projeto: {self.project_id}\n")
        print("="*60)
        
        # Networking (ordem importante para peering)
        self.extract_networks()
        self.extract_firewall()
        self.extract_routes()
        self.extract_routers()
        self.extract_vpn_gateways()
        self.extract_peering()
        
        # Compute e Storage
        self.extract_compute()
        self.extract_instance_groups()  # FASE 1: MIGs
        self.extract_disks()  # FASE 1: Disks
        self.extract_storage()
        
        # Serverless
        self.extract_functions()
        self.extract_cloud_run()
        
        # Containers e Orchestration
        self.extract_gke()
        self.extract_composer()
        
        # Databases
        self.extract_sql()
        self.extract_redis()
        self.extract_bigquery()
        
        # Messaging
        self.extract_pubsub()
        
        # Security e IAM
        self.extract_service_accounts()
        self.extract_iam_policies()  # FASE 1: IAM Policies
        self.extract_secrets()
        self.extract_kms()
        
        # Networking avançado
        self.extract_dns()
        self.extract_load_balancers()
        self.extract_network_endpoint_groups()  # FASE 1: NEGs
        self.extract_cloud_nat()  # FASE 1: Cloud NAT
        
        # CI/CD e Artifacts
        self.extract_artifact_registry()
        
        # Scheduling
        self.extract_cloud_scheduler()
        
        # Data Processing
        self.extract_dataflow()
        
        print("="*60)
        print(f"\n✅ Extração concluída!\n")
    
    def sanitize_name(self, name: str) -> str:
        """Sanitiza nome para uso em Terraform"""
        return name.replace(".", "_").replace("-", "_").replace("/", "_")
    
    def generate_network_tf(self) -> str:
        """Gera HCL para networks - TODOS os parâmetros"""
        hcl = "# VPC Networks\n\n"
        
        for net in self.resources.get('networks', []):
            name = net.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_network" "{tf_name}" {{\n'
            hcl += f'  name                    = "{name}"\n'
            hcl += f'  project                 = "{self.project_id}"\n'
            hcl += f'  auto_create_subnetworks = {str(net.get("autoCreateSubnetworks", False)).lower()}\n'
            
            # Description
            if net.get('description'):
                hcl += f'  description             = "{net["description"]}"\n'
            
            # Routing Mode
            if net.get('routingConfig'):
                mode = net['routingConfig'].get('routingMode', 'REGIONAL')
                hcl += f'  routing_mode            = "{mode}"\n'
            
            # MTU
            if net.get('mtu'):
                hcl += f'  mtu                     = {net["mtu"]}\n'
            
            # Delete Default Routes
            if net.get('deleteDefaultRoutesOnCreate'):
                hcl += f'  delete_default_routes_on_create = true\n'
            
            # IPv6 ULA
            if net.get('enableUlaInternalIpv6'):
                hcl += f'  enable_ula_internal_ipv6 = true\n'
            
            if net.get('internalIpv6Range'):
                hcl += f'  internal_ipv6_range     = "{net["internalIpv6Range"]}"\n'
            
            hcl += '}\n\n'
        
        # Subnets
        hcl += "# Subnets\n\n"
        for subnet in self.resources.get('subnets', []):
            name = subnet.get('name', '')
            tf_name = self.sanitize_name(name)
            network_url = subnet.get('network', '')
            network_name = network_url.split('/')[-1] if network_url else ''
            
            hcl += f'resource "google_compute_subnetwork" "{tf_name}" {{\n'
            hcl += f'  name          = "{name}"\n'
            hcl += f'  project       = "{self.project_id}"\n'
            hcl += f'  ip_cidr_range = "{subnet.get("ipCidrRange", "")}"\n'
            hcl += f'  region        = "{subnet.get("region", "").split("/")[-1]}"\n'
            hcl += f'  network       = google_compute_network.{self.sanitize_name(network_name)}.id\n'
            
            # Description
            if subnet.get('description'):
                hcl += f'  description   = "{subnet["description"]}"\n'
            
            # Purpose (PRIVATE, INTERNAL_HTTPS_LOAD_BALANCER, etc.)
            if subnet.get('purpose'):
                hcl += f'  purpose       = "{subnet["purpose"]}"\n'
            
            # Role (ACTIVE/BACKUP para load balancer interno)
            if subnet.get('role'):
                hcl += f'  role          = "{subnet["role"]}"\n'
            
            # Private IP Google Access
            if subnet.get('privateIpGoogleAccess'):
                hcl += f'  private_ip_google_access = true\n'
            
            # Private IPv6 Google Access
            if subnet.get('privateIpv6GoogleAccess'):
                hcl += f'  private_ipv6_google_access = "{subnet["privateIpv6GoogleAccess"]}"\n'
            
            # Stack Type (IPV4_ONLY, IPV4_IPV6, etc.)
            if subnet.get('stackType'):
                hcl += f'  stack_type    = "{subnet["stackType"]}"\n'
            
            # IPv6 Access Type
            if subnet.get('ipv6AccessType'):
                hcl += f'  ipv6_access_type = "{subnet["ipv6AccessType"]}"\n'
            
            # IPv6 CIDR Range
            if subnet.get('ipv6CidrRange'):
                hcl += f'  ipv6_cidr_range = "{subnet["ipv6CidrRange"]}"\n'
            
            # Secondary IP Ranges (IMPORTANTE PARA ANÁLISE DE REDE!)
            if subnet.get('secondaryIpRanges'):
                hcl += '\n'
                for sec_range in subnet['secondaryIpRanges']:
                    hcl += f'  secondary_ip_range {{\n'
                    hcl += f'    range_name    = "{sec_range.get("rangeName", "")}"\n'
                    hcl += f'    ip_cidr_range = "{sec_range.get("ipCidrRange", "")}"\n'
                    hcl += f'  }}\n'
            
            # Flow Logs Configuration
            if subnet.get('logConfig'):
                log_cfg = subnet['logConfig']
                if log_cfg.get('enable'):
                    hcl += '\n  log_config {\n'
                    hcl += f'    aggregation_interval = "{log_cfg.get("aggregationInterval", "INTERVAL_5_SEC")}"\n'
                    hcl += f'    flow_sampling        = {log_cfg.get("flowSampling", 0.5)}\n'
                    hcl += f'    metadata             = "{log_cfg.get("metadata", "INCLUDE_ALL_METADATA")}"\n'
                    if log_cfg.get('metadataFields'):
                        hcl += f'    metadata_fields      = {json.dumps(log_cfg["metadataFields"])}\n'
                    if log_cfg.get('filterExpr'):
                        hcl += f'    filter_expr          = "{log_cfg["filterExpr"]}"\n'
                    hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_firewall_tf(self) -> str:
        """Gera HCL para firewall rules - TODOS os parâmetros"""
        hcl = "# Firewall Rules\n\n"
        
        for fw in self.resources.get('firewalls', []):
            name = fw.get('name', '')
            tf_name = self.sanitize_name(name)
            network_url = fw.get('network', '')
            network_name = network_url.split('/')[-1] if network_url else ''
            
            hcl += f'resource "google_compute_firewall" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  network = google_compute_network.{self.sanitize_name(network_name)}.id\n'
            
            # Description
            if fw.get('description'):
                hcl += f'  description = "{fw["description"]}"\n'
            
            # Direction (INGRESS/EGRESS)
            if fw.get('direction'):
                hcl += f'  direction = "{fw["direction"]}"\n'
            
            # Priority
            if fw.get('priority'):
                hcl += f'  priority = {fw["priority"]}\n'
            
            # Disabled
            if fw.get('disabled'):
                hcl += f'  disabled = true\n'
            
            # Source Ranges (INGRESS)
            if fw.get('sourceRanges'):
                hcl += f'  source_ranges = {json.dumps(fw["sourceRanges"])}\n'
            
            # Source Tags (INGRESS)
            if fw.get('sourceTags'):
                hcl += f'  source_tags = {json.dumps(fw["sourceTags"])}\n'
            
            # Source Service Accounts (INGRESS)
            if fw.get('sourceServiceAccounts'):
                hcl += f'  source_service_accounts = {json.dumps(fw["sourceServiceAccounts"])}\n'
            
            # Destination Ranges (EGRESS)
            if fw.get('destinationRanges'):
                hcl += f'  destination_ranges = {json.dumps(fw["destinationRanges"])}\n'
            
            # Target Tags
            if fw.get('targetTags'):
                hcl += f'  target_tags = {json.dumps(fw["targetTags"])}\n'
            
            # Target Service Accounts
            if fw.get('targetServiceAccounts'):
                hcl += f'  target_service_accounts = {json.dumps(fw["targetServiceAccounts"])}\n'
            
            # ALLOW Rules
            for allowed in fw.get('allowed', []):
                protocol = allowed.get('IPProtocol', 'tcp')
                hcl += f'\n  allow {{\n'
                hcl += f'    protocol = "{protocol}"\n'
                if allowed.get('ports'):
                    hcl += f'    ports    = {json.dumps(allowed["ports"])}\n'
                hcl += f'  }}\n'
            
            # DENY Rules (importante para análise de segurança!)
            for denied in fw.get('denied', []):
                protocol = denied.get('IPProtocol', 'tcp')
                hcl += f'\n  deny {{\n'
                hcl += f'    protocol = "{protocol}"\n'
                if denied.get('ports'):
                    hcl += f'    ports    = {json.dumps(denied["ports"])}\n'
                hcl += f'  }}\n'
            
            # Log Configuration (essencial para troubleshooting de rede!)
            if fw.get('logConfig'):
                log_cfg = fw['logConfig']
                if log_cfg.get('enable'):
                    hcl += '\n  log_config {\n'
                    hcl += f'    metadata = "{log_cfg.get("metadata", "INCLUDE_ALL_METADATA")}"\n'
                    hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_routes_tf(self) -> str:
        """Gera HCL para rotas personalizadas"""
        hcl = "# Custom Routes\n\n"
        
        for route in self.resources.get('routes', []):
            name = route.get('name', '')
            # Pular rotas padrão gerenciadas pelo Google
            if name.startswith('default-route-'):
                continue
                
            tf_name = self.sanitize_name(name)
            network_url = route.get('network', '')
            network_name = network_url.split('/')[-1] if network_url else ''
            
            hcl += f'resource "google_compute_route" "{tf_name}" {{\n'
            hcl += f'  name        = "{name}"\n'
            hcl += f'  project     = "{self.project_id}"\n'
            hcl += f'  dest_range  = "{route.get("destRange", "")}"\n'
            hcl += f'  network     = google_compute_network.{self.sanitize_name(network_name)}.id\n'
            
            if route.get('description'):
                hcl += f'  description = "{route["description"]}"\n'
            
            if route.get('priority'):
                hcl += f'  priority    = {route["priority"]}\n'
            
            if route.get('tags'):
                hcl += f'  tags        = {json.dumps(route["tags"])}\n'
            
            # Next hop
            if route.get('nextHopGateway'):
                gateway = route['nextHopGateway'].split('/')[-1]
                hcl += f'  next_hop_gateway = "{gateway}"\n'
            elif route.get('nextHopIp'):
                hcl += f'  next_hop_ip = "{route["nextHopIp"]}"\n'
            elif route.get('nextHopInstance'):
                hcl += f'  next_hop_instance = "{route["nextHopInstance"]}"\n'
            elif route.get('nextHopVpnTunnel'):
                hcl += f'  next_hop_vpn_tunnel = "{route["nextHopVpnTunnel"]}"\n'
            elif route.get('nextHopIlb'):
                hcl += f'  next_hop_ilb = "{route["nextHopIlb"]}"\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_routers_tf(self) -> str:
        """Gera HCL para Cloud Routers"""
        hcl = "# Cloud Routers\n\n"
        
        for router in self.resources.get('routers', []):
            name = router.get('name', '')
            tf_name = self.sanitize_name(name)
            network_url = router.get('network', '')
            network_name = network_url.split('/')[-1] if network_url else ''
            
            hcl += f'resource "google_compute_router" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  region  = "{router.get("region", "").split("/")[-1]}"\n'
            hcl += f'  network = google_compute_network.{self.sanitize_name(network_name)}.id\n'
            
            if router.get('description'):
                hcl += f'  description = "{router["description"]}"\n'
            
            # BGP Configuration\n            if router.get('bgp'):\n                bgp = router['bgp']\n                hcl += '\n  bgp {\n'\n                hcl += f'    asn = {bgp.get("asn", 64512)}\n'\n                if bgp.get('advertiseMode'):\n                    hcl += f'    advertise_mode = "{bgp["advertiseMode"]}"\n'\n                if bgp.get('advertisedGroups'):\n                    hcl += f'    advertised_groups = {json.dumps(bgp["advertisedGroups"])}\n'\n                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_vpn_tf(self) -> str:
        """Gera HCL para VPN Gateways e Tunnels"""
        hcl = "# VPN Gateways\n\n"
        
        for gw in self.resources.get('vpn_gateways', []):
            name = gw.get('name', '')
            tf_name = self.sanitize_name(name)
            network_url = gw.get('network', '')
            network_name = network_url.split('/')[-1] if network_url else ''
            
            hcl += f'resource "google_compute_ha_vpn_gateway" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  region  = "{gw.get("region", "").split("/")[-1]}"\n'
            hcl += f'  network = google_compute_network.{self.sanitize_name(network_name)}.id\n'
            
            if gw.get('description'):
                hcl += f'  description = "{gw["description"]}"\n'
            
            hcl += '}\n\n'
        
        # VPN Tunnels
        if self.resources.get('vpn_tunnels'):
            hcl += "# VPN Tunnels\n\n"
            
            for tunnel in self.resources.get('vpn_tunnels', []):
                name = tunnel.get('name', '')
                tf_name = self.sanitize_name(name)
                
                hcl += f'resource "google_compute_vpn_tunnel" "{tf_name}" {{\n'
                hcl += f'  name          = "{name}"\n'
                hcl += f'  project       = "{self.project_id}"\n'
                hcl += f'  region        = "{tunnel.get("region", "").split("/")[-1]}"\n'
                
                if tunnel.get('description'):
                    hcl += f'  description   = "{tunnel["description"]}"\n'
                
                if tunnel.get('peerIp'):
                    hcl += f'  peer_ip       = "{tunnel["peerIp"]}"\n'
                
                if tunnel.get('sharedSecret'):
                    hcl += f'  shared_secret = "<REDACTED>"  # Definir via variável segura\n'
                
                if tunnel.get('ikeVersion'):
                    hcl += f'  ike_version   = {tunnel["ikeVersion"]}\n'
                
                hcl += f'  # Configuração adicional necessária\n'
                hcl += '}\n\n'
        
        return hcl
    
    def generate_peering_tf(self) -> str:
        """Gera HCL para VPC Peering"""
        hcl = "# VPC Peering Connections\n\n"
        
        for peering_info in self.resources.get('peerings', []):
            network = peering_info.get('network', '')
            peering = peering_info.get('peering', {})
            
            name = peering.get('name', '')
            tf_name = self.sanitize_name(f"{network}_{name}")
            
            hcl += f'resource "google_compute_network_peering" "{tf_name}" {{\n'
            hcl += f'  name         = "{name}"\n'
            hcl += f'  network      = google_compute_network.{self.sanitize_name(network)}.id\n'
            hcl += f'  peer_network = "{peering.get("network", "")}"\n'
            
            if peering.get('exportCustomRoutes'):
                hcl += f'  export_custom_routes = true\n'
            
            if peering.get('importCustomRoutes'):
                hcl += f'  import_custom_routes = true\n'
            
            if peering.get('exportSubnetRoutesWithPublicIp'):
                hcl += f'  export_subnet_routes_with_public_ip = true\n'
            
            if peering.get('importSubnetRoutesWithPublicIp'):
                hcl += f'  import_subnet_routes_with_public_ip = true\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_storage_tf(self) -> str:
        """Gera HCL para storage buckets"""
        hcl = "# Storage Buckets\n\n"
        
        for bucket in self.resources.get('buckets', []):
            name = bucket.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_storage_bucket" "{tf_name}" {{\n'
            hcl += f'  name     = "{name}"\n'
            hcl += f'  project  = "{self.project_id}"\n'
            hcl += f'  location = "{bucket.get("location", "US")}"\n'
            
            if bucket.get('storageClass'):
                hcl += f'  storage_class = "{bucket["storageClass"]}"\n'
            
            if bucket.get('uniformBucketLevelAccess', {}).get('enabled'):
                hcl += f'\n  uniform_bucket_level_access = true\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_functions_tf(self) -> str:
        """Gera HCL para Cloud Functions"""
        hcl = "# Cloud Functions (Gen 2)\n\n"
        
        for fn in self.resources.get('functions', []):
            name = fn.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_cloudfunctions2_function" "{tf_name}" {{\n'
            hcl += f'  name     = "{name}"\n'
            hcl += f'  project  = "{self.project_id}"\n'
            hcl += f'  location = "{fn.get("location", "").split("/")[-1]}"\n'
            hcl += f'\n  # Configuração completa requer informações adicionais\n'
            hcl += f'  # Revisar manualmente após geração\n'
            hcl += '}\n\n'
        
        return hcl
    
    def generate_gke_tf(self) -> str:
        """Gera HCL para GKE clusters"""
        hcl = "# GKE Clusters\n\n"
        
        for cluster in self.resources.get('gke_clusters', []):
            name = cluster.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_container_cluster" "{tf_name}" {{\n'
            hcl += f'  name     = "{name}"\n'
            hcl += f'  project  = "{self.project_id}"\n'
            hcl += f'  location = "{cluster.get("location", "")}"\n'
            hcl += f'\n  # Configuração adicional necessária\n'
            hcl += f'  # initial_node_count, node_config, etc.\n'
            hcl += '}\n\n'
        
        return hcl
    
    def generate_service_accounts_tf(self) -> str:
        """Gera HCL para Service Accounts"""
        hcl = "# Service Accounts\n\n"
        
        for sa in self.resources.get('service_accounts', []):
            email = sa.get('email', '')
            # Pular service accounts gerenciadas pelo Google
            if 'gserviceaccount.com' in email and 'iam.gserviceaccount.com' in email:
                account_id = email.split('@')[0]
                tf_name = self.sanitize_name(account_id)
                
                hcl += f'resource "google_service_account" "{tf_name}" {{\n'
                hcl += f'  account_id   = "{account_id}"\n'
                hcl += f'  project      = "{self.project_id}"\n'
                hcl += f'  display_name = "{sa.get("displayName", account_id)}"\n'
                hcl += '}\n\n'
        
        return hcl
    
    def generate_iam_policies_tf(self) -> str:
        """Gera HCL para IAM Policies do projeto"""
        hcl = "# IAM Policy Bindings\n\n"
        
        policy = self.resources.get('iam_policy', {})
        bindings = policy.get('bindings', [])
        
        for idx, binding in enumerate(bindings):
            role = binding.get('role', '')
            members = binding.get('members', [])
            
            if role and members:
                # Sanitizar role para nome do recurso
                role_name = role.replace('roles/', '').replace('.', '_').replace('/', '_')
                tf_name = f"{role_name}_{idx}"
                
                hcl += f'resource "google_project_iam_binding" "{tf_name}" {{\n'
                hcl += f'  project = "{self.project_id}"\n'
                hcl += f'  role    = "{role}"\n\n'
                hcl += '  members = [\n'
                for member in members:
                    hcl += f'    "{member}",\n'
                hcl += '  ]\n'
                
                # Adicionar condition se existir
                if binding.get('condition'):
                    condition = binding['condition']
                    hcl += '\n  condition {\n'
                    hcl += f'    title       = "{condition.get("title", "")}"\n'
                    hcl += f'    description = "{condition.get("description", "")}"\n'
                    hcl += f'    expression  = "{condition.get("expression", "")}"\n'
                    hcl += '  }\n'
                
                hcl += '}\n\n'
        
        return hcl
    
    def generate_instance_groups_tf(self) -> str:
        """Gera HCL para Instance Templates e Managed Instance Groups"""
        hcl = "# Instance Templates\n\n"
        
        # Instance Templates
        for template in self.resources.get('instance_templates', []):
            name = template.get('name', '')
            tf_name = self.sanitize_name(name)
            properties = template.get('properties', {})
            
            hcl += f'resource "google_compute_instance_template" "{tf_name}" {{\n'
            hcl += f'  name         = "{name}"\n'
            hcl += f'  project      = "{self.project_id}"\n'
            
            if template.get('description'):
                hcl += f'  description  = "{template["description"]}"\n'
            
            # Machine type
            machine_type = properties.get('machineType', 'n1-standard-1')
            hcl += f'  machine_type = "{machine_type}"\n'
            
            # Disks
            if properties.get('disks'):
                for disk in properties['disks']:
                    hcl += '\n  disk {\n'
                    if disk.get('boot'):
                        hcl += '    boot         = true\n'
                    if disk.get('autoDelete'):
                        hcl += '    auto_delete  = true\n'
                    if disk.get('initializeParams'):
                        params = disk['initializeParams']
                        hcl += '    source_image = "{}"\n'.format(params.get('sourceImage', 'debian-cloud/debian-11'))
                        if params.get('diskSizeGb'):
                            hcl += f'    disk_size_gb = {params["diskSizeGb"]}\n'
                        if params.get('diskType'):
                            hcl += f'    disk_type    = "{params["diskType"]}"\n'
                    hcl += '  }\n'
            
            # Network interfaces
            if properties.get('networkInterfaces'):
                for iface in properties['networkInterfaces']:
                    hcl += '\n  network_interface {\n'
                    if iface.get('network'):
                        network_name = iface['network'].split('/')[-1]
                        hcl += f'    network = "{network_name}"\n'
                    if iface.get('subnetwork'):
                        subnet_name = iface['subnetwork'].split('/')[-1]
                        hcl += f'    subnetwork = "{subnet_name}"\n'
                    hcl += '  }\n'
            
            # Tags
            if properties.get('tags', {}).get('items'):
                hcl += '\n  tags = [\n'
                for tag in properties['tags']['items']:
                    hcl += f'    "{tag}",\n'
                hcl += '  ]\n'
            
            hcl += '}\n\n'
        
        # Managed Instance Groups
        hcl += "# Managed Instance Groups\n\n"
        for mig in self.resources.get('managed_instance_groups', []):
            name = mig.get('name', '')
            tf_name = self.sanitize_name(name)
            
            # Verificar se é regional ou zonal
            is_regional = 'region' in mig
            
            if is_regional:
                hcl += f'resource "google_compute_region_instance_group_manager" "{tf_name}" {{\n'
                hcl += f'  name   = "{name}"\n'
                hcl += f'  region = "{mig.get("region", "").split("/")[-1]}"\n'
            else:
                hcl += f'resource "google_compute_instance_group_manager" "{tf_name}" {{\n'
                hcl += f'  name = "{name}"\n'
                hcl += f'  zone = "{mig.get("zone", "").split("/")[-1]}"\n'
            
            hcl += f'  project = "{self.project_id}"\n'
            
            # Instance template
            if mig.get('instanceTemplate'):
                template_name = mig['instanceTemplate'].split('/')[-1]
                hcl += f'\n  version {{\n'
                hcl += f'    instance_template = google_compute_instance_template.{self.sanitize_name(template_name)}.id\n'
                hcl += '  }\n'
            
            # Target size
            if mig.get('targetSize'):
                hcl += f'\n  target_size = {mig["targetSize"]}\n'
            
            # Base instance name
            if mig.get('baseInstanceName'):
                hcl += f'  base_instance_name = "{mig["baseInstanceName"]}"\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_cloud_nat_tf(self) -> str:
        """Gera HCL para Cloud NAT"""
        hcl = "# Cloud NAT\n\n"
        
        for nat in self.resources.get('cloud_nats', []):
            name = nat.get('name', '')
            router_name = nat.get('router_name', '')
            region = nat.get('region', '')
            tf_name = self.sanitize_name(f"{router_name}_{name}")
            
            hcl += f'resource "google_compute_router_nat" "{tf_name}" {{\n'
            hcl += f'  name   = "{name}"\n'
            hcl += f'  router = google_compute_router.{self.sanitize_name(router_name)}.name\n'
            hcl += f'  region = "{region}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            # NAT IP allocate option
            if nat.get('natIpAllocateOption'):
                hcl += f'  nat_ip_allocate_option = "{nat["natIpAllocateOption"]}"\n'
            
            # Source subnetwork IP ranges
            if nat.get('sourceSubnetworkIpRangesToNat'):
                hcl += f'  source_subnetwork_ip_ranges_to_nat = "{nat["sourceSubnetworkIpRangesToNat"]}"\n'
            
            # Subnetworks (se especificado)
            if nat.get('subnetworks'):
                for subnet in nat['subnetworks']:
                    hcl += '\n  subnetwork {\n'
                    if subnet.get('name'):
                        subnet_name = subnet['name'].split('/')[-1]
                        hcl += f'    name = "{subnet_name}"\n'
                    if subnet.get('sourceIpRangesToNat'):
                        hcl += f'    source_ip_ranges_to_nat = {json.dumps(subnet["sourceIpRangesToNat"])}\n'
                    hcl += '  }\n'
            
            # Min ports per VM
            if nat.get('minPortsPerVm'):
                hcl += f'  min_ports_per_vm = {nat["minPortsPerVm"]}\n'
            
            # Log config
            if nat.get('logConfig'):
                log_config = nat['logConfig']
                hcl += '\n  log_config {\n'
                hcl += f'    enable = {str(log_config.get("enable", False)).lower()}\n'
                hcl += f'    filter = "{log_config.get("filter", "ALL")}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_disks_tf(self) -> str:
        """Gera HCL para Compute Disks"""
        hcl = "# Compute Persistent Disks\n\n"
        
        for disk in self.resources.get('compute_disks', []):
            name = disk.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_disk" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  zone    = "{disk.get("zone", "").split("/")[-1]}"\n'
            
            # Type
            if disk.get('type'):
                disk_type = disk['type'].split('/')[-1]
                hcl += f'  type    = "{disk_type}"\n'
            
            # Size
            if disk.get('sizeGb'):
                hcl += f'  size    = {disk["sizeGb"]}\n'
            
            # Description
            if disk.get('description'):
                hcl += f'  description = "{disk["description"]}"\n'
            
            # Labels
            if disk.get('labels'):
                hcl += '\n  labels = {\n'
                for key, value in disk['labels'].items():
                    hcl += f'    {key} = "{value}"\n'
                hcl += '  }\n'
            
            # Physical block size
            if disk.get('physicalBlockSizeBytes'):
                hcl += f'  physical_block_size_bytes = {disk["physicalBlockSizeBytes"]}\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_negs_tf(self) -> str:
        """Gera HCL para Network Endpoint Groups"""
        hcl = "# Network Endpoint Groups (NEGs)\n\n"
        
        for neg in self.resources.get('network_endpoint_groups', []):
            name = neg.get('name', '')
            tf_name = self.sanitize_name(name)
            
            # Verificar tipo de NEG (zonal, regional, serverless, etc)
            neg_type = neg.get('networkEndpointType', 'GCE_VM_IP_PORT')
            
            if 'region' in neg:
                # NEG Regional
                hcl += f'resource "google_compute_region_network_endpoint_group" "{tf_name}" {{\n'
                hcl += f'  name   = "{name}"\n'
                hcl += f'  region = "{neg.get("region", "").split("/")[-1]}"\n'
            else:
                # NEG Zonal
                hcl += f'resource "google_compute_network_endpoint_group" "{tf_name}" {{\n'
                hcl += f'  name = "{name}"\n'
                hcl += f'  zone = "{neg.get("zone", "").split("/")[-1]}"\n'
            
            hcl += f'  project = "{self.project_id}"\n'
            
            # Network
            if neg.get('network'):
                network_name = neg['network'].split('/')[-1]
                hcl += f'  network = "{network_name}"\n'
            
            # Subnetwork
            if neg.get('subnetwork'):
                subnet_name = neg['subnetwork'].split('/')[-1]
                hcl += f'  subnetwork = "{subnet_name}"\n'
            
            # Network endpoint type
            hcl += f'  network_endpoint_type = "{neg_type}"\n'
            
            # Default port
            if neg.get('defaultPort'):
                hcl += f'  default_port = {neg["defaultPort"]}\n'
            
            # Description
            if neg.get('description'):
                hcl += f'  description = "{neg["description"]}"\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_provider_tf(self) -> str:
        """Gera arquivo provider.tf"""
        return f'''terraform {{
  required_version = ">= 1.0"
  
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

provider "google" {{
  project = "{self.project_id}"
  region  = "us-central1"  # Ajustar conforme necessário
}}
'''
    
    def generate_variables_tf(self) -> str:
        """Gera arquivo variables.tf"""
        return f'''variable "project_id" {{
  description = "GCP Project ID"
  type        = string
  default     = "{self.project_id}"
}}

variable "region" {{
  description = "Default GCP region"
  type        = string
  default     = "us-central1"
}}

variable "zone" {{
  description = "Default GCP zone"
  type        = string
  default     = "us-central1-a"
}}
'''
    
    def save_terraform_files(self):
        """Salva arquivos Terraform"""
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📝 Gerando arquivos Terraform em: {output_path}\n")
        
        # Provider
        with open(output_path / "provider.tf", "w") as f:
            f.write(self.generate_provider_tf())
        print("   ✓ provider.tf")
        
        # Variables
        with open(output_path / "variables.tf", "w") as f:
            f.write(self.generate_variables_tf())
        print("   ✓ variables.tf")
        
        # Networks
        if self.resources.get('networks') or self.resources.get('subnets'):
            with open(output_path / "networks.tf", "w") as f:
                f.write(self.generate_network_tf())
            print("   ✓ networks.tf")
        
        # Firewall
        if self.resources.get('firewalls'):
            with open(output_path / "firewall.tf", "w") as f:
                f.write(self.generate_firewall_tf())
            print("   ✓ firewall.tf")
        
        # Routes
        if self.resources.get('routes'):
            with open(output_path / "routes.tf", "w") as f:
                f.write(self.generate_routes_tf())
            print("   ✓ routes.tf")
        
        # Cloud Routers
        if self.resources.get('routers'):
            with open(output_path / "routers.tf", "w") as f:
                f.write(self.generate_routers_tf())
            print("   ✓ routers.tf")
        
        # VPN
        if self.resources.get('vpn_gateways') or self.resources.get('vpn_tunnels'):
            with open(output_path / "vpn.tf", "w") as f:
                f.write(self.generate_vpn_tf())
            print("   ✓ vpn.tf")
        
        # VPC Peering
        if self.resources.get('peerings'):
            with open(output_path / "peering.tf", "w") as f:
                f.write(self.generate_peering_tf())
            print("   ✓ peering.tf")
        
        # Storage
        if self.resources.get('buckets'):
            with open(output_path / "storage.tf", "w") as f:
                f.write(self.generate_storage_tf())
            print("   ✓ storage.tf")
        
        # Functions
        if self.resources.get('functions'):
            with open(output_path / "functions.tf", "w") as f:
                f.write(self.generate_functions_tf())
            print("   ✓ functions.tf")
        
        # GKE
        if self.resources.get('gke_clusters'):
            with open(output_path / "gke.tf", "w") as f:
                f.write(self.generate_gke_tf())
            print("   ✓ gke.tf")
        
        # Service Accounts
        if self.resources.get('service_accounts'):
            with open(output_path / "iam.tf", "w") as f:
                f.write(self.generate_service_accounts_tf())
            print("   ✓ iam.tf")
        
        # IAM Policies (FASE 1)
        if self.resources.get('iam_policy', {}).get('bindings'):
            with open(output_path / "iam_policies.tf", "w") as f:
                f.write(self.generate_iam_policies_tf())
            print("   ✓ iam_policies.tf")
        
        # Instance Groups e Templates (FASE 1)
        if self.resources.get('instance_templates') or self.resources.get('managed_instance_groups'):
            with open(output_path / "instance_groups.tf", "w") as f:
                f.write(self.generate_instance_groups_tf())
            print("   ✓ instance_groups.tf")
        
        # Cloud NAT (FASE 1)
        if self.resources.get('cloud_nats'):
            with open(output_path / "cloud_nat.tf", "w") as f:
                f.write(self.generate_cloud_nat_tf())
            print("   ✓ cloud_nat.tf")
        
        # Compute Disks (FASE 1)
        if self.resources.get('compute_disks'):
            with open(output_path / "disks.tf", "w") as f:
                f.write(self.generate_disks_tf())
            print("   ✓ disks.tf")
        
        # Network Endpoint Groups (FASE 1)
        if self.resources.get('network_endpoint_groups'):
            with open(output_path / "negs.tf", "w") as f:
                f.write(self.generate_negs_tf())
            print("   ✓ negs.tf")
        
        # README
        readme = f"""# Terraform - {self.project_id}

Infraestrutura extraída automaticamente do GCP.

## Uso

```bash
# Inicializar Terraform
terraform init

# Verificar plano
terraform plan

# Aplicar (cuidado!)
# terraform apply
```

## Recursos Extraídos

### 🌐 Networking
- **Networks**: {len(self.resources.get('networks', []))} VPC(s)
- **Subnets**: {len(self.resources.get('subnets', []))} subnet(s)
- **Firewall Rules**: {len(self.resources.get('firewalls', []))} regra(s)
- **Routes**: {len(self.resources.get('routes', []))} rota(s) personalizada(s)
- **Cloud Routers**: {len(self.resources.get('routers', []))} router(s)
- **Cloud NAT**: {len(self.resources.get('cloud_nats', []))} NAT(s) ⭐ FASE 1
- **Network Endpoint Groups**: {len(self.resources.get('network_endpoint_groups', []))} NEG(s) ⭐ FASE 1
- **VPN Gateways**: {len(self.resources.get('vpn_gateways', []))} gateway(s)
- **VPN Tunnels**: {len(self.resources.get('vpn_tunnels', []))} tunnel(s)
- **VPC Peering**: {len(self.resources.get('peerings', []))} conexão(ões)

### 💻 Compute & Storage
- **Compute Instances**: {len(self.resources.get('instances', []))} VM(s)
- **Instance Templates**: {len(self.resources.get('instance_templates', []))} template(s) ⭐ FASE 1
- **Managed Instance Groups**: {len(self.resources.get('managed_instance_groups', []))} MIG(s) ⭐ FASE 1
- **Compute Disks**: {len(self.resources.get('compute_disks', []))} disco(s) ⭐ FASE 1
- **Compute Snapshots**: {len(self.resources.get('compute_snapshots', []))} snapshot(s) ⭐ FASE 1
- **Storage Buckets**: {len(self.resources.get('buckets', []))} bucket(s)
- **Cloud Functions**: {len(self.resources.get('functions', []))} function(s)
- **GKE Clusters**: {len(self.resources.get('gke_clusters', []))} cluster(s)
- **Cloud SQL**: {len(self.resources.get('sql_instances', []))} instância(s)

### 🔐 Security & IAM
- **Service Accounts**: {len(self.resources.get('service_accounts', []))} SA(s)
- **IAM Policy Bindings**: {len(self.resources.get('iam_policy', {}).get('bindings', []))} binding(s) ⭐ FASE 1

## 🔍 Recursos Importantes para Análise de Rede

Este projeto captura **TODOS os parâmetros** de networking:

### Networks & Subnets:
- ✅ Description, MTU, Routing Mode
- ✅ IPv6 configurations (ULA, ranges, access types)
- ✅ **Secondary IP Ranges** (crucial para GKE/pods)
- ✅ **Flow Logs** (configuração completa)
- ✅ Private Google Access
- ✅ Purpose & Role (load balancers internos)

### Firewall Rules:
- ✅ Allow & **Deny** rules
- ✅ Source/Destination ranges
- ✅ Source/Target **Tags**
- ✅ Source/Target **Service Accounts**
- ✅ Priority, Direction, Disabled state
- ✅ **Log Configuration** (para troubleshooting)

### Routes & Connectivity:
- ✅ Custom routes (next hops: gateway, IP, instance, VPN, ILB)
- ✅ Cloud Routers (BGP, ASN, advertised routes)
- ✅ VPN Gateways & Tunnels (HA VPN)
- ✅ **VPC Peering** (export/import routes e IPs públicas)

## ⚠️ Aviso Importante

Os arquivos gerados são um **ponto de partida**. Revise e ajuste conforme necessário:

1. Configurações específicas de recursos (node pools GKE, configurações avançadas, etc.)
2. Dependências entre recursos
3. Variáveis e valores sensíveis
4. Tags e labels
5. Policies e permissões

**NÃO execute `terraform apply` sem revisão completa!**
"""
        
        with open(output_path / "README.md", "w") as f:
            f.write(readme)
        print("   ✓ README.md")
        
        print(f"\n✅ Arquivos Terraform gerados com sucesso!\n")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 gcp_to_terraform.py <project-id> [output-dir]")
        sys.exit(1)
    
    project_id = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    extractor = GCPToTerraform(project_id, output_dir)
    extractor.extract_all()
    extractor.save_terraform_files()
    
    print(f"📁 Arquivos salvos em: {extractor.output_dir}")
    print(f"\n💡 Próximos passos:")
    print(f"   cd {extractor.output_dir}")
    print(f"   terraform init")
    print(f"   terraform plan")


if __name__ == "__main__":
    main()
