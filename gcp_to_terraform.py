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
        
        # Compute e outros serviços
        self.extract_compute()
        self.extract_storage()
        self.extract_functions()
        self.extract_gke()
        self.extract_sql()
        self.extract_pubsub()
        self.extract_service_accounts()
        
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
            
            # BGP Configuration\n            if router.get('bgp'):\n                bgp = router['bgp']\n                hcl += '\\n  bgp {\\n'\n                hcl += f'    asn = {bgp.get("asn", 64512)}\\n'\n                if bgp.get('advertiseMode'):\n                    hcl += f'    advertise_mode = \"{bgp[\"advertiseMode\"]}\"\\n'\n                if bgp.get('advertisedGroups'):\n                    hcl += f'    advertised_groups = {json.dumps(bgp[\"advertisedGroups\"])}\\n'\n                hcl += '  }\\n'
            
            hcl += '}\\n\\n'
        
        return hcl
    
    def generate_vpn_tf(self) -> str:
        \"\"\"Gera HCL para VPN Gateways e Tunnels\"\"\"
        hcl = \"# VPN Gateways\\n\\n\"
        
        for gw in self.resources.get('vpn_gateways', []):
            name = gw.get('name', '')
            tf_name = self.sanitize_name(name)
            network_url = gw.get('network', '')
            network_name = network_url.split('/')[-1] if network_url else ''
            
            hcl += f'resource \"google_compute_ha_vpn_gateway\" \"{tf_name}\" {{\\n'
            hcl += f'  name    = \"{name}\"\\n'
            hcl += f'  project = \"{self.project_id}\"\\n'
            hcl += f'  region  = \"{gw.get(\"region\", \"\").split(\"/\")[-1]}\"\\n'
            hcl += f'  network = google_compute_network.{self.sanitize_name(network_name)}.id\\n'
            
            if gw.get('description'):
                hcl += f'  description = \"{gw[\"description\"]}\"\\n'
            
            hcl += '}\\n\\n'
        
        # VPN Tunnels
        if self.resources.get('vpn_tunnels'):
            hcl += \"# VPN Tunnels\\n\\n\"
            
            for tunnel in self.resources.get('vpn_tunnels', []):
                name = tunnel.get('name', '')
                tf_name = self.sanitize_name(name)
                
                hcl += f'resource \"google_compute_vpn_tunnel\" \"{tf_name}\" {{\\n'
                hcl += f'  name          = \"{name}\"\\n'
                hcl += f'  project       = \"{self.project_id}\"\\n'
                hcl += f'  region        = \"{tunnel.get(\"region\", \"\").split(\"/\")[-1]}\"\\n'
                
                if tunnel.get('description'):
                    hcl += f'  description   = \"{tunnel[\"description\"]}\"\\n'
                
                if tunnel.get('peerIp'):
                    hcl += f'  peer_ip       = \"{tunnel[\"peerIp\"]}\"\\n'
                
                if tunnel.get('sharedSecret'):
                    hcl += f'  shared_secret = \"<REDACTED>\"  # Definir via variável segura\\n'
                
                if tunnel.get('ikeVersion'):
                    hcl += f'  ike_version   = {tunnel[\"ikeVersion\"]}\\n'
                
                hcl += f'  # Configuração adicional necessária\\n'
                hcl += '}\\n\\n'
        
        return hcl
    
    def generate_peering_tf(self) -> str:
        \"\"\"Gera HCL para VPC Peering\"\"\"
        hcl = \"# VPC Peering Connections\\n\\n\"
        
        for peering_info in self.resources.get('peerings', []):
            network = peering_info.get('network', '')
            peering = peering_info.get('peering', {})
            
            name = peering.get('name', '')
            tf_name = self.sanitize_name(f\"{network}_{name}\")
            
            hcl += f'resource \"google_compute_network_peering\" \"{tf_name}\" {{\\n'
            hcl += f'  name         = \"{name}\"\\n'
            hcl += f'  network      = google_compute_network.{self.sanitize_name(network)}.id\\n'
            hcl += f'  peer_network = \"{peering.get(\"network\", \"\")}\"\\n'
            
            if peering.get('exportCustomRoutes'):
                hcl += f'  export_custom_routes = true\\n'
            
            if peering.get('importCustomRoutes'):
                hcl += f'  import_custom_routes = true\\n'
            
            if peering.get('exportSubnetRoutesWithPublicIp'):
                hcl += f'  export_subnet_routes_with_public_ip = true\\n'
            
            if peering.get('importSubnetRoutesWithPublicIp'):
                hcl += f'  import_subnet_routes_with_public_ip = true\\n'
            
            hcl += '}\\n\\n'
        
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
- **VPN Gateways**: {len(self.resources.get('vpn_gateways', []))} gateway(s)
- **VPN Tunnels**: {len(self.resources.get('vpn_tunnels', []))} tunnel(s)
- **VPC Peering**: {len(self.resources.get('peerings', []))} conexão(ões)

### 💾 Compute & Storage
- **Storage Buckets**: {len(self.resources.get('buckets', []))} bucket(s)
- **Cloud Functions**: {len(self.resources.get('functions', []))} function(s)
- **GKE Clusters**: {len(self.resources.get('gke_clusters', []))} cluster(s)
- **Cloud SQL**: {len(self.resources.get('sql_instances', []))} instância(s)

### 🔐 IAM
- **Service Accounts**: {len(self.resources.get('service_accounts', []))} SA(s)

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
