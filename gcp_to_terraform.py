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
        self.enabled_apis = set()  # APIs habilitadas no projeto
        
        # Mapeamento de API -> Métodos de extração
        self.api_to_methods = {
            'compute.googleapis.com': [
                'extract_networks', 'extract_firewall', 'extract_routes',
                'extract_routers', 'extract_vpn_gateways', 'extract_peering',
                'extract_compute', 'extract_instance_groups', 'extract_compute_disks',
                'extract_compute_images', 'extract_load_balancers', 'extract_health_checks',
                'extract_ssl_certificates', 'extract_network_endpoint_groups',
                'extract_cloud_nat', 'extract_cloud_armor', 'extract_cloud_interconnect',
                'extract_autoscalers', 'extract_private_service_connect', 'extract_binary_authorization',
                'extract_commitments', 'extract_reservations', 'extract_cloud_cdn'
            ],
            'storage-component.googleapis.com': ['extract_storage'],
            'cloudfunctions.googleapis.com': ['extract_functions'],
            'run.googleapis.com': ['extract_cloudrun'],
            'container.googleapis.com': ['extract_gke', 'extract_gke_node_pools', 'extract_binary_authorization'],
            'composer.googleapis.com': ['extract_composer'],
            'sqladmin.googleapis.com': ['extract_sql'],
            'redis.googleapis.com': ['extract_redis'],
            'bigquery.googleapis.com': ['extract_bigquery', 'extract_bigquery_tables', 'extract_bigquery_routines'],
            'spanner.googleapis.com': ['extract_cloud_spanner'],
            'pubsub.googleapis.com': ['extract_pubsub', 'extract_pubsub_complete'],
            'iam.googleapis.com': ['extract_service_accounts', 'extract_iam_policies', 
                                   'extract_iam_custom_roles', 'extract_service_account_keys', 
                                   'extract_workload_identity'],
            'secretmanager.googleapis.com': ['extract_secrets'],
            'cloudkms.googleapis.com': ['extract_kms'],
            'dns.googleapis.com': ['extract_dns'],
            'file.googleapis.com': ['extract_filestore'],
            'artifactregistry.googleapis.com': ['extract_artifact_registry'],
            'cloudscheduler.googleapis.com': ['extract_cloud_scheduler'],
            'cloudtasks.googleapis.com': ['extract_cloud_tasks'],
            'dataflow.googleapis.com': ['extract_dataflow'],
            'dataproc.googleapis.com': ['extract_dataproc'],
            'bigtable.googleapis.com': ['extract_bigtable'],
            'monitoring.googleapis.com': ['extract_monitoring_dashboards', 'extract_alerting_policies', 'extract_uptime_checks'],
            'logging.googleapis.com': ['extract_log_sinks'],
            'securitycenter.googleapis.com': ['extract_security_command_center']
        }
        
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
    
    def detect_enabled_apis(self):
        """Detecta APIs habilitadas no projeto"""
        print("🔍 Detectando APIs habilitadas no projeto...")
        try:
            result = subprocess.run(
                f"gcloud services list --enabled --project={self.project_id} --format=json".split(),
                capture_output=True,
                text=True,
                check=True
            )
            services = json.loads(result.stdout) if result.stdout else []
            
            # Extrair apenas os nomes das APIs
            for service in services:
                service_name = service.get('config', {}).get('name', '')
                if service_name:
                    self.enabled_apis.add(service_name)
            
            print(f"   ✓ {len(self.enabled_apis)} APIs habilitadas detectadas")
            
            # Mostrar APIs relevantes para extração
            relevant_apis = self.enabled_apis.intersection(self.api_to_methods.keys())
            if relevant_apis:
                print(f"   ℹ️  APIs relevantes para extração: {len(relevant_apis)}")
                for api in sorted(relevant_apis):
                    api_short = api.replace('.googleapis.com', '')
                    print(f"      • {api_short}")
            else:
                print(f"   ⚠️  Nenhuma API relevante detectada")
                
        except Exception as e:
            print(f"   ⚠️  Erro ao detectar APIs: {str(e)}")
            print(f"   ℹ️  Continuando com extração padrão...")
    
    def should_extract(self, method_name: str) -> bool:
        """Verifica se um método de extração deve ser executado baseado nas APIs habilitadas"""
        # Se não conseguiu detectar APIs, extrai tudo (comportamento antigo)
        if not self.enabled_apis:
            return True
        
        # Verifica se alguma API habilitada requer este método
        for api, methods in self.api_to_methods.items():
            if api in self.enabled_apis and method_name in methods:
                return True
        
        return False
    
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
        # BigQuery usa ferramenta 'bq' standalone, não 'gcloud bq'
        try:
            result = subprocess.run(
                f"bq ls -p {self.project_id} --format=json".split(),
                capture_output=True,
                text=True,
                check=True
            )
            datasets = json.loads(result.stdout) if result.stdout else []
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # Se 'bq' não estiver instalado ou comando falhar, usa lista vazia
            datasets = []
        
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
    
    def extract_compute_disks(self):
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
    
    def extract_cloud_armor(self):
        """Extrai Cloud Armor Security Policies"""
        print("🛡️  Extraindo Cloud Armor...")
        
        # Security Policies
        policies = self.run_gcloud("compute security-policies list")
        self.resources['security_policies'] = policies
        print(f"   ✓ {len(policies)} security policies encontradas")
    
    def extract_iam_custom_roles(self):
        """Extrai IAM Custom Roles criadas no projeto"""
        print("🎭 Extraindo IAM Custom Roles...")
        
        # Custom roles do projeto
        roles = self.run_gcloud(f"iam roles list --project={self.project_id}")
        self.resources['custom_roles'] = roles
        print(f"   ✓ {len(roles)} custom roles encontradas")
    
    def extract_service_account_keys(self):
        """Extrai Service Account Keys para auditoria"""
        print("🔑 Extraindo Service Account Keys...")
        
        all_keys = []
        service_accounts = self.resources.get('service_accounts', [])
        
        for sa in service_accounts:
            email = sa.get('email', '')
            if email and 'iam.gserviceaccount.com' in email:
                try:
                    keys = self.run_gcloud(f"iam service-accounts keys list --iam-account={email}")
                    for key in keys:
                        key['service_account'] = email
                        all_keys.append(key)
                except:
                    pass
        
        self.resources['sa_keys'] = all_keys
        print(f"   ✓ {len(all_keys)} service account keys encontradas")
    
    def extract_health_checks(self):
        """Extrai Health Checks (HTTP, HTTPS, TCP, etc)"""
        print("❤️  Extraindo Health Checks...")
        
        # Health checks globais e regionais
        health_checks = self.run_gcloud("compute health-checks list")
        self.resources['health_checks'] = health_checks
        print(f"   ✓ {len(health_checks)} health checks encontrados")
    
    def extract_ssl_certificates(self):
        """Extrai SSL Certificates"""
        print("🔒 Extraindo SSL Certificates...")
        
        # SSL Certificates (managed e self-managed)
        ssl_certs = self.run_gcloud("compute ssl-certificates list")
        self.resources['ssl_certificates'] = ssl_certs
        print(f"   ✓ {len(ssl_certs)} SSL certificates encontrados")
    
    def extract_compute_images(self):
        """Extrai imagens customizadas (excluindo imagens públicas)"""
        print("💿 Extraindo Compute Images...")
        
        # Apenas imagens custom do projeto
        images = self.run_gcloud("compute images list --no-standard-images")
        self.resources['compute_images'] = images
        print(f"   ✓ {len(images)} imagens customizadas encontradas")
    
    def extract_pubsub_complete(self):
        """Extrai Pub/Sub completo (topics, subscriptions, schemas)"""
        print("📬 Extraindo Pub/Sub Completo...")
        
        # Subscriptions
        subscriptions = self.run_gcloud("pubsub subscriptions list")
        self.resources['pubsub_subscriptions'] = subscriptions
        print(f"   ✓ {len(subscriptions)} subscriptions encontradas")
        
        # Schemas
        schemas = self.run_gcloud("pubsub schemas list")
        self.resources['pubsub_schemas'] = schemas
        print(f"   ✓ {len(schemas)} schemas encontrados")
    
    def extract_bigquery_tables(self):
        """Extrai BigQuery tables e views por dataset"""
        print("📊 Extraindo BigQuery Tables...")
        
        # Usar comando bq correto
        try:
            # Listar todos os datasets primeiro
            result = subprocess.run(
                f"bq ls -p {self.project_id} --format=json".split(),
                capture_output=True,
                text=True,
                check=True
            )
            datasets = json.loads(result.stdout) if result.stdout else []
            
            all_tables = []
            for dataset in datasets:
                dataset_id = dataset.get('datasetReference', {}).get('datasetId', '')
                if dataset_id:
                    try:
                        # Listar tables do dataset
                        table_result = subprocess.run(
                            f"bq ls -p {self.project_id} --format=json {dataset_id}".split(),
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        tables = json.loads(table_result.stdout) if table_result.stdout else []
                        for table in tables:
                            table['dataset_id'] = dataset_id
                            all_tables.append(table)
                    except:
                        pass
            
            self.resources['bigquery_tables'] = all_tables
            print(f"   ✓ {len(all_tables)} tables/views encontradas")
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            # Se 'bq' não estiver instalado ou comando falhar, usa lista vazia silenciosamente
            self.resources['bigquery_tables'] = []
            print(f"   ✓ 0 tables/views encontradas")
    
    def extract_gke_node_pools(self):
        """Extrai GKE Node Pools"""
        print("☸️  Extraindo GKE Node Pools...")
        
        all_node_pools = []
        clusters = self.resources.get('gke_clusters', [])
        
        for cluster in clusters:
            cluster_name = cluster.get('name', '')
            location = cluster.get('location', '') or cluster.get('zone', '')
            
            if cluster_name and location:
                try:
                    # Usar --region ou --zone dependendo do tipo de cluster
                    location_flag = "--region" if not location.endswith(('-a', '-b', '-c', '-d', '-e', '-f')) else "--zone"
                    node_pools = self.run_gcloud(f"container node-pools list --cluster={cluster_name} {location_flag}={location}")
                    for pool in node_pools:
                        pool['cluster_name'] = cluster_name
                        pool['cluster_location'] = location
                        all_node_pools.append(pool)
                except:
                    pass
        
        self.resources['gke_node_pools'] = all_node_pools
        print(f"   ✓ {len(all_node_pools)} node pools encontrados")
    
    def extract_monitoring_dashboards(self):
        """Extrai Monitoring Dashboards"""
        print("📈 Extraindo Monitoring Dashboards...")
        dashboards = self.run_gcloud("monitoring dashboards list")
        self.resources['monitoring_dashboards'] = dashboards
        print(f"   ✓ {len(dashboards)} dashboards encontrados")
    
    def extract_alerting_policies(self):
        """Extrai Alerting Policies"""
        print("🔔 Extraindo Alerting Policies...")
        try:
            policies = self.run_gcloud("alpha monitoring policies list")
            self.resources['alerting_policies'] = policies
            print(f"   ✓ {len(policies)} alerting policies encontradas")
        except:
            print(f"   ⚠️  Alpha component necessário para alerting policies")
            self.resources['alerting_policies'] = []
    
    def extract_cloud_interconnect(self):
        """Extrai Cloud Interconnect"""
        print("🔗 Extraindo Cloud Interconnect...")
        
        # Interconnects
        interconnects = self.run_gcloud("compute interconnects list")
        self.resources['interconnects'] = interconnects
        print(f"   ✓ {len(interconnects)} interconnects encontrados")
        
        # Interconnect Attachments
        attachments = self.run_gcloud("compute interconnects attachments list")
        self.resources['interconnect_attachments'] = attachments
        print(f"   ✓ {len(attachments)} interconnect attachments encontrados")
    
    def extract_cloud_spanner(self):
        """Extrai Cloud Spanner instances"""
        print("🗄️  Extraindo Cloud Spanner...")
        instances = self.run_gcloud("spanner instances list")
        self.resources['spanner_instances'] = instances
        print(f"   ✓ {len(instances)} Spanner instances encontradas")
    
    def extract_filestore(self):
        """Extrai Filestore instances"""
        print("📁 Extraindo Filestore...")
        # Filestore requer location
        try:
            instances = self.run_gcloud("filestore instances list --location=-")
            self.resources['filestore_instances'] = instances
            print(f"   ✓ {len(instances)} Filestore instances encontradas")
        except:
            print(f"   ⚠️  Erro ao extrair Filestore (pode precisar especificar --location)")
            self.resources['filestore_instances'] = []
    
    def extract_dataproc(self):
        """Extrai Dataproc clusters"""
        print("🔬 Extraindo Dataproc Clusters...")
        try:
            clusters = self.run_gcloud("dataproc clusters list --region=us-central1")
            self.resources['dataproc_clusters'] = clusters
            print(f"   ✓ {len(clusters)} Dataproc clusters encontrados")
        except:
            # Tentar listar em todas as regiões
            try:
                all_clusters = []
                regions = ['us-central1', 'us-east1', 'europe-west1']
                for region in regions:
                    clusters = self.run_gcloud(f"dataproc clusters list --region={region}")
                    all_clusters.extend(clusters)
                self.resources['dataproc_clusters'] = all_clusters
                print(f"   ✓ {len(all_clusters)} Dataproc clusters encontrados")
            except:
                print(f"   ⚠️  Erro ao extrair Dataproc clusters")
                self.resources['dataproc_clusters'] = []
    
    def extract_autoscalers(self):
        """Extrai Autoscalers para Managed Instance Groups"""
        print("📈 Extraindo Autoscalers...")
        try:
            # Listar todos os autoscalers em todas as zonas
            all_autoscalers = []
            
            # Autoscalers regionais
            try:
                regional_autoscalers = self.run_gcloud("compute instance-groups managed list")
                for mig in regional_autoscalers:
                    if mig.get('zone'):
                        zone = mig['zone'].split('/')[-1]
                        name = mig.get('name', '')
                        try:
                            autoscaler = self.run_gcloud(
                                f"compute instance-groups managed describe {name} --zone={zone} --format=json"
                            )
                            if autoscaler and isinstance(autoscaler, list) and len(autoscaler) > 0:
                                autoscaler_data = autoscaler[0]
                                if autoscaler_data.get('autoscaler'):
                                    all_autoscalers.append({
                                        'name': autoscaler_data['autoscaler'].split('/')[-1],
                                        'mig_name': name,
                                        'zone': zone,
                                        'target': autoscaler_data.get('autoscaler', ''),
                                        'policy': autoscaler_data.get('autoscalingPolicy', {})
                                    })
                        except:
                            pass
            except Exception as e:
                print(f"   ⚠️  Erro ao listar MIGs: {str(e)}")
            
            self.resources['autoscalers'] = all_autoscalers
            print(f"   ✓ {len(all_autoscalers)} Autoscalers encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Autoscalers: {str(e)}")
            self.resources['autoscalers'] = []
    
    def extract_bigtable(self):
        """Extrai instâncias Bigtable"""
        print("🗄️  Extraindo Cloud Bigtable...")
        try:
            instances = self.run_gcloud("bigtable instances list")
            
            # Para cada instância, extrair clusters
            for instance in instances:
                instance_id = instance.get('name', '').split('/')[-1]
                try:
                    clusters = self.run_gcloud(f"bigtable clusters list --instances={instance_id}")
                    instance['clusters'] = clusters
                except:
                    instance['clusters'] = []
                
                # Extrair tables
                try:
                    tables = self.run_gcloud(f"bigtable tables list --instances={instance_id}")
                    instance['tables'] = tables
                except:
                    instance['tables'] = []
            
            self.resources['bigtable_instances'] = instances
            print(f"   ✓ {len(instances)} instâncias Bigtable encontradas")
        except Exception as e:
            print(f"   ⚠️  Bigtable não disponível ou sem instâncias: {str(e)}")
            self.resources['bigtable_instances'] = []
    
    def extract_private_service_connect(self):
        """Extrai Private Service Connect (endpoints e attachments)"""
        print("🔌 Extraindo Private Service Connect...")
        try:
            # Service Attachments (producer side)
            attachments = self.run_gcloud("compute service-attachments list")
            
            # Forwarding rules com target = service attachment (consumer side)
            forwarding_rules = self.run_gcloud("compute forwarding-rules list")
            psc_forwarding_rules = [
                fr for fr in forwarding_rules 
                if 'serviceAttachment' in fr.get('target', '') or 
                   fr.get('loadBalancingScheme') == 'INTERNAL'
            ]
            
            self.resources['psc_attachments'] = attachments
            self.resources['psc_forwarding_rules'] = psc_forwarding_rules
            print(f"   ✓ {len(attachments)} service attachments encontrados")
            print(f"   ✓ {len(psc_forwarding_rules)} PSC forwarding rules encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Private Service Connect: {str(e)}")
            self.resources['psc_attachments'] = []
            self.resources['psc_forwarding_rules'] = []
    
    def extract_cloud_tasks(self):
        """Extrai Cloud Tasks queues"""
        print("📋 Extraindo Cloud Tasks...")
        try:
            # Listar locations disponíveis
            locations_result = self.run_gcloud("tasks locations list")
            
            all_queues = []
            for location in locations_result[:3]:  # Limitar a 3 locations
                location_id = location.get('name', '').split('/')[-1]
                try:
                    queues = self.run_gcloud(f"tasks queues list --location={location_id}")
                    for queue in queues:
                        queue['location'] = location_id
                    all_queues.extend(queues)
                except:
                    pass
            
            self.resources['cloud_tasks_queues'] = all_queues
            print(f"   ✓ {len(all_queues)} task queues encontradas")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Cloud Tasks: {str(e)}")
            self.resources['cloud_tasks_queues'] = []
    
    def extract_workload_identity(self):
        """Extrai configurações de Workload Identity"""
        print("🆔 Extraindo Workload Identity...")
        try:
            # Workload Identity é configurado através de IAM bindings
            # Buscar service accounts com workload identity habilitado
            service_accounts = self.resources.get('service_accounts', [])
            
            workload_identities = []
            for sa in service_accounts:
                email = sa.get('email', '')
                try:
                    # Verificar IAM policy do SA para workload identity bindings
                    policy = self.run_gcloud(f"iam service-accounts get-iam-policy {email}")
                    bindings = policy.get('bindings', [])
                    
                    # Filtrar bindings de workload identity
                    wi_bindings = [
                        b for b in bindings 
                        if any('serviceaccount.gserviceaccount.com' in member for member in b.get('members', []))
                    ]
                    
                    if wi_bindings:
                        workload_identities.append({
                            'service_account': email,
                            'bindings': wi_bindings
                        })
                except:
                    pass
            
            self.resources['workload_identity_bindings'] = workload_identities
            print(f"   ✓ {len(workload_identities)} workload identity bindings encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Workload Identity: {str(e)}")
            self.resources['workload_identity_bindings'] = []
    
    def extract_security_command_center(self):
        """Extrai configurações do Security Command Center"""
        print("🛡️  Extraindo Security Command Center...")
        try:
            # Organization sources
            org_name = f"organizations/{self.project_id}"  # Normalmente precisa do org ID
            
            # Listar sources de segurança
            # Nota: SCC normalmente é configurado no nível da organização
            sources = []
            try:
                # Tentar listar sources (pode precisar de permissão de org)
                result = subprocess.run(
                    f"gcloud scc sources list --organization={org_name} --format=json".split(),
                    capture_output=True,
                    text=True,
                    check=True
                )
                sources = json.loads(result.stdout) if result.stdout else []
            except:
                # Se não tiver acesso ao org, só registra no project
                sources = []
            
            self.resources['scc_sources'] = sources
            print(f"   ✓ {len(sources)} Security Command Center sources encontrados")
        except Exception as e:
            print(f"   ⚠️  Security Command Center requer permissões de organização")
            self.resources['scc_sources'] = []
    
    def extract_binary_authorization(self):
        """Extrai políticas de Binary Authorization"""
        print("✅ Extraindo Binary Authorization...")
        try:
            # Obter política de Binary Authorization do projeto
            try:
                policy = self.run_gcloud("container binauthz policy export")
                self.resources['binary_authz_policy'] = policy if policy else {}
                
                # Listar attestors
                attestors = self.run_gcloud("container binauthz attestors list")
                self.resources['binary_authz_attestors'] = attestors
                
                print(f"   ✓ Política Binary Authorization encontrada")
                print(f"   ✓ {len(attestors)} attestors encontrados")
            except:
                self.resources['binary_authz_policy'] = {}
                self.resources['binary_authz_attestors'] = []
                print(f"   ✓ Binary Authorization não configurado")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Binary Authorization: {str(e)}")
            self.resources['binary_authz_policy'] = {}
            self.resources['binary_authz_attestors'] = []
    
    def extract_commitments(self):
        """Extrai Committed Use Discounts (CUDs)"""
        print("💰 Extraindo Committed Use Discounts...")
        try:
            commitments = self.run_gcloud("compute commitments list")
            self.resources['commitments'] = commitments
            print(f"   ✓ {len(commitments)} commitments encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Commitments: {str(e)}")
            self.resources['commitments'] = []
    
    def extract_reservations(self):
        """Extrai Compute Reservations"""
        print("🎫 Extraindo Compute Reservations...")
        try:
            reservations = self.run_gcloud("compute reservations list")
            self.resources['reservations'] = reservations
            print(f"   ✓ {len(reservations)} reservations encontradas")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Reservations: {str(e)}")
            self.resources['reservations'] = []
    
    def extract_cloud_cdn(self):
        """Extrai configurações de Cloud CDN"""
        print("🌐 Extraindo Cloud CDN...")
        try:
            # Cloud CDN é configurado via backend services
            backend_services = self.run_gcloud("compute backend-services list")
            
            cdn_services = [
                bs for bs in backend_services 
                if bs.get('enableCDN', False) or bs.get('cdnPolicy')
            ]
            
            self.resources['cloud_cdn_services'] = cdn_services
            print(f"   ✓ {len(cdn_services)} backend services com CDN encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Cloud CDN: {str(e)}")
            self.resources['cloud_cdn_services'] = []
    
    def extract_log_sinks(self):
        """Extrai Log Sinks (exportação de logs)"""
        print("📝 Extraindo Log Sinks...")
        try:
            sinks = self.run_gcloud("logging sinks list")
            self.resources['log_sinks'] = sinks
            print(f"   ✓ {len(sinks)} log sinks encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Log Sinks: {str(e)}")
            self.resources['log_sinks'] = []
    
    def extract_uptime_checks(self):
        """Extrai Uptime Checks (monitoramento de disponibilidade)"""
        print("📡 Extraindo Uptime Checks...")
        try:
            # Listar uptime checks
            uptime_checks = self.run_gcloud("monitoring uptime-checks list")
            self.resources['uptime_checks'] = uptime_checks
            print(f"   ✓ {len(uptime_checks)} uptime checks encontrados")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair Uptime Checks: {str(e)}")
            self.resources['uptime_checks'] = []
    
    def extract_bigquery_routines(self):
        """Extrai BigQuery Routines e Scheduled Queries"""
        print("🔧 Extraindo BigQuery Routines...")
        try:
            datasets = self.resources.get('bigquery_datasets', [])
            
            all_routines = []
            for dataset in datasets[:5]:  # Limitar para não demorar
                dataset_id = dataset.get('datasetReference', {}).get('datasetId', '')
                if dataset_id:
                    try:
                        # Listar routines (UDFs, stored procedures)
                        result = subprocess.run(
                            f"bq ls --routines -p {self.project_id} --format=json {dataset_id}".split(),
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        routines = json.loads(result.stdout) if result.stdout else []
                        for routine in routines:
                            routine['dataset_id'] = dataset_id
                            all_routines.append(routine)
                    except:
                        pass
            
            self.resources['bigquery_routines'] = all_routines
            print(f"   ✓ {len(all_routines)} routines encontradas")
            
            # Scheduled queries (data transfer configs)
            try:
                transfers = self.run_gcloud("transfer-configs list")
                self.resources['bigquery_transfers'] = transfers
                print(f"   ✓ {len(transfers)} scheduled queries encontradas")
            except:
                self.resources['bigquery_transfers'] = []
                print(f"   ✓ 0 scheduled queries encontradas")
                
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair BigQuery Routines: {str(e)}")
            self.resources['bigquery_routines'] = []
            self.resources['bigquery_transfers'] = []
    
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
        
        # PASSO 1: Detectar APIs habilitadas (NOVA ESTRATÉGIA)
        self.detect_enabled_apis()
        print()
        
        # PASSO 2: Extrair recursos baseado nas APIs habilitadas
        
        # Networking (ordem importante para peering)
        if self.should_extract('extract_networks'):
            self.extract_networks()
            self.extract_firewall()
            self.extract_routes()
            self.extract_routers()
            self.extract_vpn_gateways()
            self.extract_peering()
        
        # Compute e Storage
        if self.should_extract('extract_compute'):
            self.extract_compute()
            self.extract_instance_groups()  # FASE 1: MIGs
            self.extract_compute_disks()  # FASE 1: Disks
            self.extract_compute_images()  # FASE 2: Custom Images
            self.extract_autoscalers()  # FASE 4: Autoscalers
            self.extract_commitments()  # FASE 6: Committed Use Discounts
            self.extract_reservations()  # FASE 6: VM Reservations
        
        if self.should_extract('extract_storage'):
            self.extract_storage()
        
        # Serverless
        if self.should_extract('extract_functions'):
            self.extract_functions()
        
        if self.should_extract('extract_cloudrun'):
            self.extract_cloud_run()
        
        # Containers e Orchestration
        if self.should_extract('extract_gke'):
            self.extract_gke()
            self.extract_gke_node_pools()  # FASE 3: GKE Node Pools
        
        if self.should_extract('extract_binary_authorization'):
            self.extract_binary_authorization()  # FASE 5: Binary Authorization
        
        if self.should_extract('extract_composer'):
            self.extract_composer()
        
        # Databases
        if self.should_extract('extract_sql'):
            self.extract_sql()
        
        if self.should_extract('extract_redis'):
            self.extract_redis()
        
        if self.should_extract('extract_bigquery'):
            self.extract_bigquery()
            self.extract_bigquery_tables()  # FASE 3: BigQuery Tables
            self.extract_bigquery_routines()  # FASE 6: BigQuery Routines e Scheduled Queries
        
        if self.should_extract('extract_cloud_spanner'):
            self.extract_cloud_spanner()  # FASE 3: Cloud Spanner
        
        if self.should_extract('extract_bigtable'):
            self.extract_bigtable()  # FASE 4: Bigtable
        
        # Messaging
        if self.should_extract('extract_pubsub'):
            self.extract_pubsub()
            self.extract_pubsub_complete()  # FASE 3: Pub/Sub Subscriptions e Schemas
        
        # Security e IAM (sempre extrair, pois IAM é fundamental)
        if self.should_extract('extract_service_accounts'):
            self.extract_service_accounts()
            self.extract_iam_policies()  # FASE 1: IAM Policies
            self.extract_iam_custom_roles()  # FASE 2: Custom Roles
            self.extract_service_account_keys()  # FASE 2: SA Keys
            self.extract_workload_identity()  # FASE 5: Workload Identity
        
        if self.should_extract('extract_secrets'):
            self.extract_secrets()
        
        if self.should_extract('extract_kms'):
            self.extract_kms()
        
        # Networking avançado
        if self.should_extract('extract_dns'):
            self.extract_dns()
        
        if self.should_extract('extract_load_balancers'):
            self.extract_load_balancers()
            self.extract_health_checks()  # FASE 2: Health Checks
            self.extract_ssl_certificates()  # FASE 2: SSL Certificates
            self.extract_network_endpoint_groups()  # FASE 1: NEGs
            self.extract_cloud_nat()  # FASE 1: Cloud NAT
            self.extract_cloud_armor()  # FASE 2: Cloud Armor
            self.extract_cloud_interconnect()  # FASE 3: Cloud Interconnect
            self.extract_private_service_connect()  # FASE 5: Private Service Connect
            self.extract_cloud_cdn()  # FASE 6: Cloud CDN
        
        # Storage avançado
        if self.should_extract('extract_filestore'):
            self.extract_filestore()  # FASE 3: Filestore
        
        # CI/CD e Artifacts
        if self.should_extract('extract_artifact_registry'):
            self.extract_artifact_registry()
        
        # Scheduling
        if self.should_extract('extract_cloud_scheduler'):
            self.extract_cloud_scheduler()
        
        if self.should_extract('extract_cloud_tasks'):
            self.extract_cloud_tasks()  # FASE 5: Cloud Tasks
        
        # Data Processing
        if self.should_extract('extract_dataflow'):
            self.extract_dataflow()
        
        if self.should_extract('extract_dataproc'):
            self.extract_dataproc()  # FASE 3: Dataproc
        
        # Monitoring e Observability
        if self.should_extract('extract_monitoring_dashboards'):
            self.extract_monitoring_dashboards()  # FASE 3: Monitoring Dashboards
            self.extract_alerting_policies()  # FASE 3: Alerting Policies
            self.extract_uptime_checks()  # FASE 6: Uptime Checks
        
        # Logging
        if self.should_extract('extract_logging'):
            self.extract_log_sinks()  # FASE 6: Log Sinks
        
        # Security Avançado
        if self.should_extract('extract_security_command_center'):
            self.extract_security_command_center()  # FASE 5: Security Command Center
        
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
    
    def generate_cloud_armor_tf(self) -> str:
        """Gera HCL para Cloud Armor Security Policies"""
        hcl = "# Cloud Armor Security Policies\n\n"
        
        for policy in self.resources.get('security_policies', []):
            name = policy.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_security_policy" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if policy.get('description'):
                hcl += f'  description = "{policy["description"]}"\n'
            
            # Rules
            if policy.get('rules'):
                for rule in policy['rules']:
                    hcl += '\n  rule {\n'
                    hcl += f'    action   = "{rule.get("action", "allow")}"\n'
                    hcl += f'    priority = {rule.get("priority", 1000)}\n'
                    
                    if rule.get('description'):
                        hcl += f'    description = "{rule["description"]}"\n'
                    
                    if rule.get('match'):
                        match = rule['match']
                        hcl += '\n    match {\n'
                        if match.get('versionedExpr'):
                            hcl += f'      versioned_expr = "{match["versionedExpr"]}"\n'
                        if match.get('config'):
                            config = match['config']
                            hcl += '      config {\n'
                            if config.get('srcIpRanges'):
                                hcl += f'        src_ip_ranges = {json.dumps(config["srcIpRanges"])}\n'
                            hcl += '      }\n'
                        hcl += '    }\n'
                    
                    hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_custom_roles_tf(self) -> str:
        """Gera HCL para IAM Custom Roles"""
        hcl = "# IAM Custom Roles\n\n"
        
        for role in self.resources.get('custom_roles', []):
            name = role.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_project_iam_custom_role" "{tf_name}" {{\n'
            hcl += f'  role_id     = "{name}"\n'
            hcl += f'  project     = "{self.project_id}"\n'
            hcl += f'  title       = "{role.get("title", name)}"\n'
            
            if role.get('description'):
                hcl += f'  description = "{role["description"]}"\n'
            
            if role.get('includedPermissions'):
                hcl += '\n  permissions = [\n'
                for perm in role['includedPermissions']:
                    hcl += f'    "{perm}",\n'
                hcl += '  ]\n'
            
            if role.get('stage'):
                hcl += f'  stage = "{role["stage"]}"\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_health_checks_tf(self) -> str:
        """Gera HCL para Health Checks"""
        hcl = "# Health Checks\n\n"
        
        for hc in self.resources.get('health_checks', []):
            name = hc.get('name', '')
            tf_name = self.sanitize_name(name)
            hc_type = hc.get('type', 'HTTP').lower()
            
            hcl += f'resource "google_compute_health_check" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if hc.get('description'):
                hcl += f'  description = "{hc["description"]}"\n'
            
            # Check interval e timeout
            if hc.get('checkIntervalSec'):
                hcl += f'  check_interval_sec = {hc["checkIntervalSec"]}\n'
            if hc.get('timeoutSec'):
                hcl += f'  timeout_sec = {hc["timeoutSec"]}\n'
            if hc.get('healthyThreshold'):
                hcl += f'  healthy_threshold = {hc["healthyThreshold"]}\n'
            if hc.get('unhealthyThreshold'):
                hcl += f'  unhealthy_threshold = {hc["unhealthyThreshold"]}\n'
            
            # Configuração específica do tipo
            type_config = hc.get(f'{hc_type}HealthCheck', {})
            if type_config:
                hcl += f'\n  {hc_type}_health_check {{\n'
                if type_config.get('port'):
                    hcl += f'    port = {type_config["port"]}\n'
                if type_config.get('requestPath'):
                    hcl += f'    request_path = "{type_config["requestPath"]}"\n'
                if type_config.get('proxyHeader'):
                    hcl += f'    proxy_header = "{type_config["proxyHeader"]}"\n'
                if type_config.get('response'):
                    hcl += f'    response = "{type_config["response"]}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_ssl_certificates_tf(self) -> str:
        """Gera HCL para SSL Certificates"""
        hcl = "# SSL Certificates\n\n"
        
        for cert in self.resources.get('ssl_certificates', []):
            name = cert.get('name', '')
            tf_name = self.sanitize_name(name)
            cert_type = cert.get('type', 'SELF_MANAGED')
            
            if cert_type == 'MANAGED':
                hcl += f'resource "google_compute_managed_ssl_certificate" "{tf_name}" {{\n'
                hcl += f'  name    = "{name}"\n'
                hcl += f'  project = "{self.project_id}"\n'
                
                if cert.get('managed', {}).get('domains'):
                    hcl += '\n  managed {\n'
                    hcl += f'    domains = {json.dumps(cert["managed"]["domains"])}\n'
                    hcl += '  }\n'
            else:
                hcl += f'resource "google_compute_ssl_certificate" "{tf_name}" {{\n'
                hcl += f'  name    = "{name}"\n'
                hcl += f'  project = "{self.project_id}"\n'
                hcl += '  # Note: certificate e private_key devem ser fornecidos manualmente\n'
                hcl += '  # certificate = file("path/to/cert.pem")\n'
                hcl += '  # private_key = file("path/to/key.pem")\n'
            
            if cert.get('description'):
                hcl += f'  description = "{cert["description"]}"\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_compute_images_tf(self) -> str:
        """Gera HCL para Compute Images customizadas"""
        hcl = "# Compute Custom Images\n\n"
        
        for img in self.resources.get('compute_images', []):
            name = img.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_image" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if img.get('description'):
                hcl += f'  description = "{img["description"]}"\n'
            
            if img.get('family'):
                hcl += f'  family = "{img["family"]}"\n'
            
            # Source disk (se existe)
            if img.get('sourceDisk'):
                source_disk = img['sourceDisk'].split('/')[-1]
                hcl += f'  source_disk = "{source_disk}"\n'
            
            # Labels
            if img.get('labels'):
                hcl += '\n  labels = {\n'
                for key, value in img['labels'].items():
                    hcl += f'    {key} = "{value}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_pubsub_subscriptions_tf(self) -> str:
        """Gera HCL para Pub/Sub Subscriptions e Schemas"""
        hcl = "# Pub/Sub Subscriptions\n\n"
        
        for sub in self.resources.get('pubsub_subscriptions', []):
            name = sub.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            topic = sub.get('topic', '').split('/')[-1]
            
            hcl += f'resource "google_pubsub_subscription" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  topic   = "{topic}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if sub.get('ackDeadlineSeconds'):
                hcl += f'  ack_deadline_seconds = {sub["ackDeadlineSeconds"]}\n'
            
            if sub.get('retainAckedMessages'):
                hcl += f'  retain_acked_messages = {str(sub["retainAckedMessages"]).lower()}\n'
            
            if sub.get('messageRetentionDuration'):
                hcl += f'  message_retention_duration = "{sub["messageRetentionDuration"]}"\n'
            
            hcl += '}\n\n'
        
        # Schemas
        hcl += "# Pub/Sub Schemas\n\n"
        for schema in self.resources.get('pubsub_schemas', []):
            name = schema.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_pubsub_schema" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if schema.get('type'):
                hcl += f'  type = "{schema["type"]}"\n'
            
            if schema.get('definition'):
                hcl += f'  definition = <<EOF\n{schema["definition"]}\nEOF\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_gke_node_pools_tf(self) -> str:
        """Gera HCL para GKE Node Pools"""
        hcl = "# GKE Node Pools\n\n"
        
        for pool in self.resources.get('gke_node_pools', []):
            name = pool.get('name', '')
            cluster_name = pool.get('cluster_name', '')
            location = pool.get('cluster_location', '')
            tf_name = self.sanitize_name(f"{cluster_name}_{name}")
            
            hcl += f'resource "google_container_node_pool" "{tf_name}" {{\n'
            hcl += f'  name     = "{name}"\n'
            hcl += f'  cluster  = "{cluster_name}"\n'
            hcl += f'  location = "{location}"\n'
            hcl += f'  project  = "{self.project_id}"\n'
            
            if pool.get('initialNodeCount'):
                hcl += f'  initial_node_count = {pool["initialNodeCount"]}\n'
            
            # Node config
            if pool.get('config'):
                config = pool['config']
                hcl += '\n  node_config {\n'
                if config.get('machineType'):
                    hcl += f'    machine_type = "{config["machineType"]}"\n'
                if config.get('diskSizeGb'):
                    hcl += f'    disk_size_gb = {config["diskSizeGb"]}\n'
                if config.get('diskType'):
                    hcl += f'    disk_type = "{config["diskType"]}"\n'
                if config.get('imageType'):
                    hcl += f'    image_type = "{config["imageType"]}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_spanner_tf(self) -> str:
        """Gera HCL para Cloud Spanner"""
        hcl = "# Cloud Spanner Instances\n\n"
        
        for instance in self.resources.get('spanner_instances', []):
            name = instance.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_spanner_instance" "{tf_name}" {{\n'
            hcl += f'  name         = "{name}"\n'
            hcl += f'  project      = "{self.project_id}"\n'
            hcl += f'  config       = "{instance.get("config", "").split("/")[-1]}"\n'
            hcl += f'  display_name = "{instance.get("displayName", name)}"\n'
            
            if instance.get('nodeCount'):
                hcl += f'  num_nodes = {instance["nodeCount"]}\n'
            
            if instance.get('processingUnits'):
                hcl += f'  processing_units = {instance["processingUnits"]}\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_filestore_tf(self) -> str:
        """Gera HCL para Filestore"""
        hcl = "# Filestore Instances\n\n"
        
        for instance in self.resources.get('filestore_instances', []):
            name = instance.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_filestore_instance" "{tf_name}" {{\n'
            hcl += f'  name     = "{name}"\n'
            hcl += f'  project  = "{self.project_id}"\n'
            hcl += f'  location = "{instance.get("location", "").split("/")[-1]}"\n'
            hcl += f'  tier     = "{instance.get("tier", "STANDARD")}"\n'
            
            if instance.get('fileShares'):
                for share in instance['fileShares']:
                    hcl += '\n  file_shares {\n'
                    hcl += f'    name        = "{share.get("name", "")}"\n'
                    hcl += f'    capacity_gb = {share.get("capacityGb", 1024)}\n'
                    hcl += '  }\n'
            
            if instance.get('networks'):
                for network in instance['networks']:
                    hcl += '\n  networks {\n'
                    network_name = network.get('network', '').split('/')[-1]
                    hcl += f'    network = "{network_name}"\n'
                    hcl += f'    modes   = ["MODE_IPV4"]\n'
                    hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_dataproc_tf(self) -> str:
        """Gera HCL para Dataproc"""
        hcl = "# Dataproc Clusters\n\n"
        
        for cluster in self.resources.get('dataproc_clusters', []):
            name = cluster.get('clusterName', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_dataproc_cluster" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  region  = "{cluster.get("location", "").split("/")[-1]}"\n'
            
            # Cluster config
            if cluster.get('config'):
                config = cluster['config']
                
                # Master config
                if config.get('masterConfig'):
                    master = config['masterConfig']
                    hcl += '\n  cluster_config {\n'
                    hcl += '    master_config {\n'
                    if master.get('numInstances'):
                        hcl += f'      num_instances = {master["numInstances"]}\n'
                    if master.get('machineType'):
                        hcl += f'      machine_type = "{master["machineType"].split("/")[-1]}"\n'
                    if master.get('diskConfig', {}).get('bootDiskSizeGb'):
                        hcl += f'      disk_config {{\n'
                        hcl += f'        boot_disk_size_gb = {master["diskConfig"]["bootDiskSizeGb"]}\n'
                        hcl += '      }\n'
                    hcl += '    }\n'
                    hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_autoscalers_tf(self) -> str:
        """Gera HCL para Autoscalers"""
        hcl = "# Compute Autoscalers\n\n"
        
        for autoscaler in self.resources.get('autoscalers', []):
            name = autoscaler.get('name', '')
            tf_name = self.sanitize_name(name)
            mig_name = autoscaler.get('mig_name', '')
            zone = autoscaler.get('zone', '')
            
            hcl += f'resource "google_compute_autoscaler" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  zone    = "{zone}"\n'
            hcl += f'  target  = google_compute_instance_group_manager.{self.sanitize_name(mig_name)}.id\n'
            
            # Autoscaling policy
            policy = autoscaler.get('policy', {})
            if policy:
                hcl += '\n  autoscaling_policy {\n'
                
                if policy.get('minNumReplicas'):
                    hcl += f'    min_replicas = {policy["minNumReplicas"]}\n'
                if policy.get('maxNumReplicas'):
                    hcl += f'    max_replicas = {policy["maxNumReplicas"]}\n'
                if policy.get('coolDownPeriodSec'):
                    hcl += f'    cooldown_period = {policy["coolDownPeriodSec"]}\n'
                
                # CPU utilization
                if policy.get('cpuUtilization'):
                    cpu = policy['cpuUtilization']
                    hcl += '\n    cpu_utilization {\n'
                    if cpu.get('utilizationTarget'):
                        hcl += f'      target = {cpu["utilizationTarget"]}\n'
                    hcl += '    }\n'
                
                # Load balancing utilization
                if policy.get('loadBalancingUtilization'):
                    lb = policy['loadBalancingUtilization']
                    hcl += '\n    load_balancing_utilization {\n'
                    if lb.get('utilizationTarget'):
                        hcl += f'      target = {lb["utilizationTarget"]}\n'
                    hcl += '    }\n'
                
                # Custom metrics
                if policy.get('customMetricUtilizations'):
                    for metric in policy['customMetricUtilizations']:
                        hcl += '\n    metric {\n'
                        if metric.get('metric'):
                            hcl += f'      name   = "{metric["metric"]}"\n'
                        if metric.get('utilizationTarget'):
                            hcl += f'      target = {metric["utilizationTarget"]}\n'
                        if metric.get('utilizationTargetType'):
                            hcl += f'      type   = "{metric["utilizationTargetType"]}"\n'
                        hcl += '    }\n'
                
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_bigtable_tf(self) -> str:
        """Gera HCL para Cloud Bigtable"""
        hcl = "# Cloud Bigtable Instances\n\n"
        
        for instance in self.resources.get('bigtable_instances', []):
            name = instance.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_bigtable_instance" "{tf_name}" {{\n'
            hcl += f'  name         = "{name}"\n'
            hcl += f'  project      = "{self.project_id}"\n'
            
            if instance.get('displayName'):
                hcl += f'  display_name = "{instance["displayName"]}"\n'
            
            # Instance type
            if instance.get('type'):
                instance_type = instance['type'].lower()
                if instance_type == 'production':
                    hcl += f'  instance_type = "PRODUCTION"\n'
                elif instance_type == 'development':
                    hcl += f'  instance_type = "DEVELOPMENT"\n'
            
            # Clusters
            if instance.get('clusters'):
                for cluster in instance['clusters']:
                    cluster_id = cluster.get('name', '').split('/')[-1]
                    hcl += f'\n  cluster {{\n'
                    hcl += f'    cluster_id   = "{cluster_id}"\n'
                    
                    if cluster.get('location'):
                        zone = cluster['location'].split('/')[-1]
                        hcl += f'    zone         = "{zone}"\n'
                    
                    if cluster.get('serveNodes'):
                        hcl += f'    num_nodes    = {cluster["serveNodes"]}\n'
                    
                    if cluster.get('defaultStorageType'):
                        storage_type = cluster['defaultStorageType']
                        hcl += f'    storage_type = "{storage_type}"\n'
                    
                    hcl += '  }\n'
            
            # Labels
            if instance.get('labels'):
                hcl += '\n  labels = {\n'
                for key, value in instance['labels'].items():
                    hcl += f'    {key} = "{value}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        # Tables
        if self.resources.get('bigtable_instances'):
            hcl += "# Cloud Bigtable Tables\n\n"
            for instance in self.resources.get('bigtable_instances', []):
                instance_name = instance.get('name', '').split('/')[-1]
                instance_tf_name = self.sanitize_name(instance_name)
                
                for table in instance.get('tables', []):
                    table_name = table.get('name', '').split('/')[-1]
                    table_tf_name = self.sanitize_name(f"{instance_name}_{table_name}")
                    
                    hcl += f'resource "google_bigtable_table" "{table_tf_name}" {{\n'
                    hcl += f'  name          = "{table_name}"\n'
                    hcl += f'  instance_name = google_bigtable_instance.{instance_tf_name}.name\n'
                    hcl += f'  project       = "{self.project_id}"\n'
                    
                    # Column families
                    if table.get('columnFamilies'):
                        for cf_name, cf_data in table['columnFamilies'].items():
                            hcl += f'\n  column_family {{\n'
                            hcl += f'    family = "{cf_name}"\n'
                            hcl += '  }\n'
                    
                    hcl += '}\n\n'
        
        return hcl
    
    def generate_private_service_connect_tf(self) -> str:
        """Gera HCL para Private Service Connect"""
        hcl = "# Private Service Connect - Service Attachments\n\n"
        
        for attachment in self.resources.get('psc_attachments', []):
            name = attachment.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_service_attachment" "{tf_name}" {{\n'
            hcl += f'  name        = "{name}"\n'
            hcl += f'  project     = "{self.project_id}"\n'
            
            if attachment.get('region'):
                region = attachment['region'].split('/')[-1]
                hcl += f'  region      = "{region}"\n'
            
            if attachment.get('description'):
                hcl += f'  description = "{attachment["description"]}"\n'
            
            if attachment.get('targetService'):
                target = attachment['targetService'].split('/')[-1]
                hcl += f'  target_service = google_compute_forwarding_rule.{self.sanitize_name(target)}.self_link\n'
            
            if attachment.get('connectionPreference'):
                hcl += f'  connection_preference = "{attachment["connectionPreference"]}"\n'
            
            if attachment.get('natSubnets'):
                hcl += '\n  nat_subnets = [\n'
                for subnet in attachment['natSubnets']:
                    subnet_name = subnet.split('/')[-1]
                    hcl += f'    google_compute_subnetwork.{self.sanitize_name(subnet_name)}.self_link,\n'
                hcl += '  ]\n'
            
            if attachment.get('enableProxyProtocol'):
                hcl += f'  enable_proxy_protocol = {str(attachment["enableProxyProtocol"]).lower()}\n'
            
            hcl += '}\n\n'
        
        # PSC Forwarding Rules (consumer side)
        if self.resources.get('psc_forwarding_rules'):
            hcl += "# Private Service Connect - Forwarding Rules\n\n"
            for fr in self.resources.get('psc_forwarding_rules', []):
                name = fr.get('name', '')
                tf_name = self.sanitize_name(name)
                
                hcl += f'resource "google_compute_forwarding_rule" "{tf_name}_psc" {{\n'
                hcl += f'  name    = "{name}"\n'
                hcl += f'  project = "{self.project_id}"\n'
                
                if fr.get('region'):
                    region = fr['region'].split('/')[-1]
                    hcl += f'  region  = "{region}"\n'
                
                if fr.get('target'):
                    hcl += f'  target  = "{fr["target"]}"\n'
                
                if fr.get('network'):
                    network = fr['network'].split('/')[-1]
                    hcl += f'  network = google_compute_network.{self.sanitize_name(network)}.self_link\n'
                
                hcl += '}\n\n'
        
        return hcl
    
    def generate_cloud_tasks_tf(self) -> str:
        """Gera HCL para Cloud Tasks"""
        hcl = "# Cloud Tasks Queues\n\n"
        
        for queue in self.resources.get('cloud_tasks_queues', []):
            name = queue.get('name', '').split('/')[-1]
            location = queue.get('location', 'us-central1')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_cloud_tasks_queue" "{tf_name}" {{\n'
            hcl += f'  name     = "{name}"\n'
            hcl += f'  location = "{location}"\n'
            hcl += f'  project  = "{self.project_id}"\n'
            
            # Rate limits
            if queue.get('rateLimits'):
                hcl += '\n  rate_limits {\n'
                rate_limits = queue['rateLimits']
                
                if rate_limits.get('maxDispatchesPerSecond'):
                    hcl += f'    max_dispatches_per_second = {rate_limits["maxDispatchesPerSecond"]}\n'
                
                if rate_limits.get('maxBurstSize'):
                    hcl += f'    max_burst_size = {rate_limits["maxBurstSize"]}\n'
                
                if rate_limits.get('maxConcurrentDispatches'):
                    hcl += f'    max_concurrent_dispatches = {rate_limits["maxConcurrentDispatches"]}\n'
                
                hcl += '  }\n'
            
            # Retry config
            if queue.get('retryConfig'):
                hcl += '\n  retry_config {\n'
                retry = queue['retryConfig']
                
                if retry.get('maxAttempts'):
                    hcl += f'    max_attempts = {retry["maxAttempts"]}\n'
                
                if retry.get('maxRetryDuration'):
                    hcl += f'    max_retry_duration = "{retry["maxRetryDuration"]}"\n'
                
                if retry.get('minBackoff'):
                    hcl += f'    min_backoff = "{retry["minBackoff"]}"\n'
                
                if retry.get('maxBackoff'):
                    hcl += f'    max_backoff = "{retry["maxBackoff"]}"\n'
                
                if retry.get('maxDoublings'):
                    hcl += f'    max_doublings = {retry["maxDoublings"]}\n'
                
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_workload_identity_tf(self) -> str:
        """Gera HCL para Workload Identity bindings"""
        hcl = "# Workload Identity IAM Bindings\n\n"
        
        for wi in self.resources.get('workload_identity_bindings', []):
            sa_email = wi.get('service_account', '')
            sa_tf_name = self.sanitize_name(sa_email.split('@')[0])
            
            for idx, binding in enumerate(wi.get('bindings', [])):
                role = binding.get('role', '')
                role_tf = self.sanitize_name(role)
                
                hcl += f'resource "google_service_account_iam_binding" "{sa_tf_name}_{role_tf}_{idx}" {{\n'
                hcl += f'  service_account_id = google_service_account.{sa_tf_name}.name\n'
                hcl += f'  role               = "{role}"\n'
                hcl += '\n  members = [\n'
                
                for member in binding.get('members', []):
                    hcl += f'    "{member}",\n'
                
                hcl += '  ]\n'
                hcl += '}\n\n'
        
        return hcl
    
    def generate_security_command_center_tf(self) -> str:
        """Gera HCL para Security Command Center"""
        hcl = "# Security Command Center\n\n"
        hcl += "# Note: SCC is typically configured at organization level\n"
        hcl += "# Sources are managed automatically by Google Cloud\n\n"
        
        sources = self.resources.get('scc_sources', [])
        if sources:
            hcl += f"# Found {len(sources)} SCC sources\n"
            for source in sources:
                source_name = source.get('name', '')
                hcl += f"# - {source_name}\n"
            hcl += "\n"
        
        return hcl
    
    def generate_binary_authorization_tf(self) -> str:
        """Gera HCL para Binary Authorization"""
        hcl = "# Binary Authorization Policy\n\n"
        
        policy = self.resources.get('binary_authz_policy', {})
        if policy and policy.get('defaultAdmissionRule'):
            hcl += f'resource "google_binary_authorization_policy" "policy" {{\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            default_rule = policy['defaultAdmissionRule']
            hcl += '\n  default_admission_rule {\n'
            
            if default_rule.get('evaluationMode'):
                eval_mode = default_rule['evaluationMode']
                hcl += f'    evaluation_mode  = "{eval_mode}"\n'
            
            if default_rule.get('enforcementMode'):
                enf_mode = default_rule['enforcementMode']
                hcl += f'    enforcement_mode = "{enf_mode}"\n'
            
            if default_rule.get('requireAttestationsBy'):
                hcl += '\n    require_attestations_by = [\n'
                for attestor in default_rule['requireAttestationsBy']:
                    attestor_name = attestor.split('/')[-1]
                    hcl += f'      google_binary_authorization_attestor.{self.sanitize_name(attestor_name)}.name,\n'
                hcl += '    ]\n'
            
            hcl += '  }\n'
            
            # Global policy evaluation (GKE)
            if policy.get('globalPolicyEvaluationMode'):
                hcl += f'\n  global_policy_evaluation_mode = "{policy["globalPolicyEvaluationMode"]}"\n'
            
            hcl += '}\n\n'
        
        # Attestors
        for attestor in self.resources.get('binary_authz_attestors', []):
            name = attestor.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_binary_authorization_attestor" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if attestor.get('description'):
                hcl += f'  description = "{attestor["description"]}"\n'
            
            if attestor.get('userOwnedGrafeasNote'):
                note = attestor['userOwnedGrafeasNote']
                hcl += '\n  attestation_authority_note {\n'
                if note.get('noteReference'):
                    hcl += f'    note_reference = "{note["noteReference"]}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_commitments_tf(self) -> str:
        """Gera HCL para Committed Use Discounts"""
        hcl = "# Committed Use Discounts (CUDs)\n\n"
        
        for commitment in self.resources.get('commitments', []):
            name = commitment.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_commitment" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if commitment.get('region'):
                region = commitment['region'].split('/')[-1]
                hcl += f'  region  = "{region}"\n'
            
            # Plan (12 months ou 36 months)
            if commitment.get('plan'):
                plan = commitment['plan']
                hcl += f'  plan    = "{plan}"\n'
            
            # Resources (vCPUs, memory)
            if commitment.get('resources'):
                for resource in commitment['resources']:
                    res_type = resource.get('type', '')
                    amount = resource.get('amount', 0)
                    
                    if 'MEMORY' in res_type:
                        hcl += f'\n  resources {{\n'
                        hcl += f'    memory_mb = {amount}\n'
                        hcl += '  }\n'
                    elif 'VCPU' in res_type:
                        hcl += f'\n  resources {{\n'
                        hcl += f'    vcpu = {amount}\n'
                        hcl += '  }\n'
            
            # Category (MACHINE, LICENSE)
            if commitment.get('category'):
                hcl += f'  category = "{commitment["category"]}"\n'
            
            # Type (GENERAL_PURPOSE, COMPUTE_OPTIMIZED, MEMORY_OPTIMIZED)
            if commitment.get('type'):
                commit_type = commitment.get('type', '')
                if 'GENERAL_PURPOSE' in commit_type:
                    hcl += f'  type = "GENERAL_PURPOSE_N1"\n'
            
            # Auto renew
            if commitment.get('autoRenew'):
                hcl += f'  auto_renew = true\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_reservations_tf(self) -> str:
        """Gera HCL para Compute Reservations"""
        hcl = "# Compute Reservations\n\n"
        
        for reservation in self.resources.get('reservations', []):
            name = reservation.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_reservation" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            if reservation.get('zone'):
                zone = reservation['zone'].split('/')[-1]
                hcl += f'  zone    = "{zone}"\n'
            
            # Specific reservation
            if reservation.get('specificReservation'):
                spec = reservation['specificReservation']
                hcl += '\n  specific_reservation {\n'
                
                if spec.get('count'):
                    hcl += f'    count = {spec["count"]}\n'
                
                if spec.get('instanceProperties'):
                    props = spec['instanceProperties']
                    hcl += '\n    instance_properties {\n'
                    
                    if props.get('machineType'):
                        hcl += f'      machine_type = "{props["machineType"]}"\n'
                    
                    if props.get('minCpuPlatform'):
                        hcl += f'      min_cpu_platform = "{props["minCpuPlatform"]}"\n'
                    
                    if props.get('guestAccelerators'):
                        for gpu in props['guestAccelerators']:
                            hcl += '\n      guest_accelerators {\n'
                            if gpu.get('acceleratorType'):
                                hcl += f'        accelerator_type  = "{gpu["acceleratorType"]}"\n'
                            if gpu.get('acceleratorCount'):
                                hcl += f'        accelerator_count = {gpu["acceleratorCount"]}\n'
                            hcl += '      }\n'
                    
                    hcl += '    }\n'
                
                hcl += '  }\n'
            
            # Commitment
            if reservation.get('commitment'):
                commitment = reservation['commitment'].split('/')[-1]
                hcl += f'\n  commitment = google_compute_commitment.{self.sanitize_name(commitment)}.id\n'
            
            # Specific reservation required
            if reservation.get('specificReservationRequired'):
                hcl += f'  specific_reservation_required = true\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_cloud_cdn_tf(self) -> str:
        """Gera HCL para Cloud CDN (via backend services)"""
        hcl = "# Cloud CDN Backend Services\n\n"
        
        for service in self.resources.get('cloud_cdn_services', []):
            name = service.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'# Backend service {name} with Cloud CDN enabled\n'
            hcl += f'resource "google_compute_backend_service" "{tf_name}" {{\n'
            hcl += f'  name        = "{name}"\n'
            hcl += f'  project     = "{self.project_id}"\n'
            hcl += f'  enable_cdn  = true\n'
            
            # CDN Policy
            if service.get('cdnPolicy'):
                cdn = service['cdnPolicy']
                hcl += '\n  cdn_policy {\n'
                
                if cdn.get('cacheMode'):
                    hcl += f'    cache_mode = "{cdn["cacheMode"]}"\n'
                
                if cdn.get('defaultTtl'):
                    hcl += f'    default_ttl = {cdn["defaultTtl"]}\n'
                
                if cdn.get('clientTtl'):
                    hcl += f'    client_ttl = {cdn["clientTtl"]}\n'
                
                if cdn.get('maxTtl'):
                    hcl += f'    max_ttl = {cdn["maxTtl"]}\n'
                
                if cdn.get('negativeCaching'):
                    hcl += f'    negative_caching = true\n'
                
                if cdn.get('serveWhileStale'):
                    hcl += f'    serve_while_stale = {cdn["serveWhileStale"]}\n'
                
                # Cache key policy
                if cdn.get('cacheKeyPolicy'):
                    ckp = cdn['cacheKeyPolicy']
                    hcl += '\n    cache_key_policy {\n'
                    
                    if ckp.get('includeHost'):
                        hcl += f'      include_host = true\n'
                    if ckp.get('includeProtocol'):
                        hcl += f'      include_protocol = true\n'
                    if ckp.get('includeQueryString'):
                        hcl += f'      include_query_string = true\n'
                    
                    hcl += '    }\n'
                
                hcl += '  }\n'
            
            # Protocol
            if service.get('protocol'):
                hcl += f'  protocol    = "{service["protocol"]}"\n'
            
            # Timeout
            if service.get('timeoutSec'):
                hcl += f'  timeout_sec = {service["timeoutSec"]}\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_log_sinks_tf(self) -> str:
        """Gera HCL para Log Sinks"""
        hcl = "# Cloud Logging Sinks\n\n"
        
        for sink in self.resources.get('log_sinks', []):
            name = sink.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_logging_project_sink" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            
            # Destination (BigQuery, Storage, Pub/Sub, etc)
            if sink.get('destination'):
                dest = sink['destination']
                hcl += f'  destination = "{dest}"\n'
            
            # Filter
            if sink.get('filter'):
                filter_str = sink['filter'].replace('"', '\\"')
                hcl += f'  filter = "{filter_str}"\n'
            
            # Unique writer identity
            if sink.get('writerIdentity'):
                hcl += f'\n  unique_writer_identity = true\n'
            
            # BigQuery options
            if sink.get('bigqueryOptions'):
                bq_opts = sink['bigqueryOptions']
                hcl += '\n  bigquery_options {\n'
                
                if bq_opts.get('usePartitionedTables'):
                    hcl += f'    use_partitioned_tables = true\n'
                
                hcl += '  }\n'
            
            # Exclusions
            if sink.get('exclusions'):
                for exclusion in sink['exclusions']:
                    hcl += '\n  exclusions {\n'
                    if exclusion.get('name'):
                        hcl += f'    name   = "{exclusion["name"]}"\n'
                    if exclusion.get('filter'):
                        ex_filter = exclusion['filter'].replace('"', '\\"')
                        hcl += f'    filter = "{ex_filter}"\n'
                    hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_uptime_checks_tf(self) -> str:
        """Gera HCL para Uptime Checks"""
        hcl = "# Monitoring Uptime Checks\n\n"
        
        for check in self.resources.get('uptime_checks', []):
            name = check.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_monitoring_uptime_check_config" "{tf_name}" {{\n'
            hcl += f'  display_name = "{check.get("displayName", name)}"\n'
            hcl += f'  project      = "{self.project_id}"\n'
            
            # Timeout
            if check.get('timeout'):
                timeout = check['timeout'].rstrip('s')
                hcl += f'  timeout      = "{timeout}s"\n'
            
            # Period
            if check.get('period'):
                period = check['period'].rstrip('s')
                hcl += f'  period       = "{period}s"\n'
            
            # Monitored resource (HTTP, TCP, etc)
            if check.get('monitoredResource'):
                resource = check['monitoredResource']
                hcl += '\n  monitored_resource {\n'
                hcl += f'    type = "{resource.get("type", "uptime_url")}"\n'
                
                if resource.get('labels'):
                    hcl += '\n    labels = {\n'
                    for k, v in resource['labels'].items():
                        hcl += f'      {k} = "{v}"\n'
                    hcl += '    }\n'
                
                hcl += '  }\n'
            
            # HTTP check
            if check.get('httpCheck'):
                http = check['httpCheck']
                hcl += '\n  http_check {\n'
                
                if http.get('requestMethod'):
                    hcl += f'    request_method = "{http["requestMethod"]}"\n'
                
                if http.get('path'):
                    hcl += f'    path = "{http["path"]}"\n'
                
                if http.get('port'):
                    hcl += f'    port = {http["port"]}\n'
                
                if http.get('useSsl'):
                    hcl += f'    use_ssl = true\n'
                
                if http.get('validateSsl'):
                    hcl += f'    validate_ssl = true\n'
                
                hcl += '  }\n'
            
            # TCP check
            if check.get('tcpCheck'):
                tcp = check['tcpCheck']
                hcl += '\n  tcp_check {\n'
                
                if tcp.get('port'):
                    hcl += f'    port = {tcp["port"]}\n'
                
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_bigquery_routines_tf(self) -> str:
        """Gera HCL para BigQuery Routines"""
        hcl = "# BigQuery Routines (UDFs e Stored Procedures)\n\n"
        
        for routine in self.resources.get('bigquery_routines', []):
            dataset_id = routine.get('dataset_id', '')
            routine_id = routine.get('routineReference', {}).get('routineId', '')
            tf_name = self.sanitize_name(f"{dataset_id}_{routine_id}")
            
            hcl += f'resource "google_bigquery_routine" "{tf_name}" {{\n'
            hcl += f'  dataset_id  = "{dataset_id}"\n'
            hcl += f'  routine_id  = "{routine_id}"\n'
            hcl += f'  project     = "{self.project_id}"\n'
            
            # Type (SCALAR_FUNCTION, PROCEDURE, TABLE_VALUED_FUNCTION)
            if routine.get('routineType'):
                routine_type = routine['routineType']
                hcl += f'  routine_type = "{routine_type}"\n'
            
            # Language (SQL, JAVASCRIPT)
            if routine.get('language'):
                hcl += f'  language = "{routine["language"]}"\n'
            
            # Definition
            if routine.get('definitionBody'):
                definition = routine['definitionBody'].replace('\\', '\\\\').replace('"', '\\"')
                hcl += f'\n  definition_body = <<EOF\n{routine["definitionBody"]}\nEOF\n'
            
            # Arguments
            if routine.get('arguments'):
                for arg in routine['arguments']:
                    hcl += '\n  arguments {\n'
                    if arg.get('name'):
                        hcl += f'    name = "{arg["name"]}"\n'
                    if arg.get('dataType'):
                        data_type = arg['dataType'].get('typeKind', 'STRING')
                        hcl += f'    data_type = jsonencode({{"typeKind": "{data_type}"}})\n'
                    hcl += '  }\n'
            
            # Return type
            if routine.get('returnType'):
                ret_type = routine['returnType'].get('typeKind', 'STRING')
                hcl += f'\n  return_type = jsonencode({{"typeKind": "{ret_type}"}})\n'
            
            hcl += '}\n\n'
        
        # Scheduled queries (data transfer configs)
        for transfer in self.resources.get('bigquery_transfers', []):
            name = transfer.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'# Scheduled query: {transfer.get("displayName", name)}\n'
            hcl += f'resource "google_bigquery_data_transfer_config" "{tf_name}" {{\n'
            hcl += f'  display_name   = "{transfer.get("displayName", name)}"\n'
            hcl += f'  project        = "{self.project_id}"\n'
            hcl += f'  data_source_id = "{transfer.get("dataSourceId", "scheduled_query")}"\n'
            
            if transfer.get('schedule'):
                hcl += f'  schedule       = "{transfer["schedule"]}"\n'
            
            if transfer.get('destinationDatasetId'):
                hcl += f'  destination_dataset_id = "{transfer["destinationDatasetId"]}"\n'
            
            if transfer.get('params'):
                hcl += '\n  params = {\n'
                for k, v in transfer['params'].items():
                    hcl += f'    {k} = "{v}"\n'
                hcl += '  }\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_bigquery_tables_tf(self) -> str:
        """Gera HCL para BigQuery Tables"""
        hcl = "# BigQuery Tables\n\n"
        
        for table in self.resources.get('bigquery_tables', []):
            dataset_id = table.get('dataset_id', '')
            table_id = table.get('table_id', '')
            tf_name = self.sanitize_name(f"{dataset_id}_{table_id}")
            
            hcl += f'resource "google_bigquery_table" "{tf_name}" {{\n'
            hcl += f'  dataset_id = "{dataset_id}"\n'
            hcl += f'  table_id   = "{table_id}"\n'
            hcl += f'  project    = "{self.project_id}"\n'
            
            if table.get('type') == 'TABLE':
                if table.get('schema'):
                    hcl += '\n  schema = <<EOF\n'
                    hcl += json.dumps(table['schema'], indent=2)
                    hcl += '\nEOF\n'
            
            elif table.get('type') == 'VIEW':
                if table.get('query'):
                    hcl += '\n  view {\n'
                    hcl += f'    query          = <<EOF\n{table["query"]}\nEOF\n'
                    hcl += f'    use_legacy_sql = false\n'
                    hcl += '  }\n'
            
            if table.get('description'):
                hcl += f'  description = "{table["description"]}"\n'
            
            if table.get('expirationTime'):
                hcl += f'  expiration_time = {table["expirationTime"]}\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_monitoring_dashboards_tf(self) -> str:
        """Gera HCL para Monitoring Dashboards"""
        hcl = "# Monitoring Dashboards\n\n"
        
        for dashboard in self.resources.get('monitoring_dashboards', []):
            name = dashboard.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_monitoring_dashboard" "{tf_name}" {{\n'
            hcl += f'  dashboard_json = <<EOF\n'
            hcl += json.dumps(dashboard, indent=2)
            hcl += '\nEOF\n'
            hcl += '}\n\n'
        
        return hcl
    
    def generate_alerting_policies_tf(self) -> str:
        """Gera HCL para Alerting Policies"""
        hcl = "# Alerting Policies\n\n"
        
        for policy in self.resources.get('alerting_policies', []):
            name = policy.get('name', '').split('/')[-1]
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_monitoring_alert_policy" "{tf_name}" {{\n'
            hcl += f'  display_name = "{policy.get("displayName", name)}"\n'
            hcl += f'  project      = "{self.project_id}"\n'
            
            if policy.get('enabled'):
                hcl += f'  enabled = {str(policy["enabled"]).lower()}\n'
            
            if policy.get('combiner'):
                hcl += f'  combiner = "{policy["combiner"]}"\n'
            
            # Conditions
            if policy.get('conditions'):
                for condition in policy['conditions']:
                    hcl += '\n  conditions {\n'
                    hcl += f'    display_name = "{condition.get("displayName", "")}"\n'
                    hcl += '  }\n'
            
            # Notification channels
            if policy.get('notificationChannels'):
                hcl += '\n  notification_channels = [\n'
                for channel in policy['notificationChannels']:
                    channel_id = channel.split('/')[-1]
                    hcl += f'    "{channel_id}",\n'
                hcl += '  ]\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_interconnect_tf(self) -> str:
        """Gera HCL para Cloud Interconnect"""
        hcl = "# Cloud Interconnect\n\n"
        
        # Interconnects
        for interconnect in self.resources.get('interconnects', []):
            name = interconnect.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_interconnect" "{tf_name}" {{\n'
            hcl += f'  name                  = "{name}"\n'
            hcl += f'  project               = "{self.project_id}"\n'
            hcl += f'  customer_name         = "{interconnect.get("customerName", "")}"\n'
            hcl += f'  interconnect_type     = "{interconnect.get("interconnectType", "DEDICATED")}"\n'
            hcl += f'  link_type             = "{interconnect.get("linkType", "LINK_TYPE_ETHERNET_10G_LR")}"\n'
            hcl += f'  location              = "{interconnect.get("location", "").split("/")[-1]}"\n'
            hcl += f'  requested_link_count  = {interconnect.get("requestedLinkCount", 1)}\n'
            hcl += '}\n\n'
        
        # Interconnect Attachments (VLAN Attachments)
        hcl += "# Interconnect Attachments\n\n"
        for attachment in self.resources.get('interconnect_attachments', []):
            name = attachment.get('name', '')
            tf_name = self.sanitize_name(name)
            
            hcl += f'resource "google_compute_interconnect_attachment" "{tf_name}" {{\n'
            hcl += f'  name    = "{name}"\n'
            hcl += f'  project = "{self.project_id}"\n'
            hcl += f'  region  = "{attachment.get("region", "").split("/")[-1]}"\n'
            
            if attachment.get('router'):
                router_name = attachment['router'].split('/')[-1]
                hcl += f'  router = "{router_name}"\n'
            
            if attachment.get('interconnect'):
                interconnect_name = attachment['interconnect'].split('/')[-1]
                hcl += f'  interconnect = google_compute_interconnect.{self.sanitize_name(interconnect_name)}.self_link\n'
            
            if attachment.get('vlanTag8021q'):
                hcl += f'  vlan_tag8021q = {attachment["vlanTag8021q"]}\n'
            
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
        
        # Cloud Armor (FASE 2)
        if self.resources.get('security_policies'):
            with open(output_path / "cloud_armor.tf", "w") as f:
                f.write(self.generate_cloud_armor_tf())
            print("   ✓ cloud_armor.tf")
        
        # IAM Custom Roles (FASE 2)
        if self.resources.get('custom_roles'):
            with open(output_path / "custom_roles.tf", "w") as f:
                f.write(self.generate_custom_roles_tf())
            print("   ✓ custom_roles.tf")
        
        # Health Checks (FASE 2)
        if self.resources.get('health_checks'):
            with open(output_path / "health_checks.tf", "w") as f:
                f.write(self.generate_health_checks_tf())
            print("   ✓ health_checks.tf")
        
        # SSL Certificates (FASE 2)
        if self.resources.get('ssl_certificates'):
            with open(output_path / "ssl_certificates.tf", "w") as f:
                f.write(self.generate_ssl_certificates_tf())
            print("   ✓ ssl_certificates.tf")
        
        # Compute Images (FASE 2)
        if self.resources.get('compute_images'):
            with open(output_path / "images.tf", "w") as f:
                f.write(self.generate_compute_images_tf())
            print("   ✓ images.tf")
        
        # Pub/Sub Subscriptions e Schemas (FASE 3)
        if self.resources.get('pubsub_subscriptions') or self.resources.get('pubsub_schemas'):
            with open(output_path / "pubsub.tf", "w") as f:
                f.write(self.generate_pubsub_subscriptions_tf())
            print("   ✓ pubsub.tf")
        
        # GKE Node Pools (FASE 3)
        if self.resources.get('gke_node_pools'):
            with open(output_path / "gke_node_pools.tf", "w") as f:
                f.write(self.generate_gke_node_pools_tf())
            print("   ✓ gke_node_pools.tf")
        
        # BigQuery Tables (FASE 3)
        if self.resources.get('bigquery_tables'):
            with open(output_path / "bigquery_tables.tf", "w") as f:
                f.write(self.generate_bigquery_tables_tf())
            print("   ✓ bigquery_tables.tf")
        
        # Monitoring Dashboards e Alerting Policies (FASE 3)
        if self.resources.get('monitoring_dashboards') or self.resources.get('alerting_policies'):
            with open(output_path / "monitoring.tf", "w") as f:
                content = ""
                if self.resources.get('monitoring_dashboards'):
                    content += self.generate_monitoring_dashboards_tf()
                if self.resources.get('alerting_policies'):
                    content += self.generate_alerting_policies_tf()
                f.write(content)
            print("   ✓ monitoring.tf")
        
        # Cloud Interconnect (FASE 3)
        if self.resources.get('interconnects') or self.resources.get('interconnect_attachments'):
            with open(output_path / "interconnect.tf", "w") as f:
                f.write(self.generate_interconnect_tf())
            print("   ✓ interconnect.tf")
        
        # Cloud Spanner (FASE 3)
        if self.resources.get('spanner_instances'):
            with open(output_path / "spanner.tf", "w") as f:
                f.write(self.generate_spanner_tf())
            print("   ✓ spanner.tf")
        
        # Filestore (FASE 3)
        if self.resources.get('filestore_instances'):
            with open(output_path / "filestore.tf", "w") as f:
                f.write(self.generate_filestore_tf())
            print("   ✓ filestore.tf")
        
        # Dataproc (FASE 3)
        if self.resources.get('dataproc_clusters'):
            with open(output_path / "dataproc.tf", "w") as f:
                f.write(self.generate_dataproc_tf())
            print("   ✓ dataproc.tf")
        
        # Autoscalers (FASE 4)
        if self.resources.get('autoscalers'):
            with open(output_path / "autoscalers.tf", "w") as f:
                f.write(self.generate_autoscalers_tf())
            print("   ✓ autoscalers.tf")
        
        # Bigtable (FASE 4)
        if self.resources.get('bigtable_instances'):
            with open(output_path / "bigtable.tf", "w") as f:
                f.write(self.generate_bigtable_tf())
            print("   ✓ bigtable.tf")
        
        # Private Service Connect (FASE 5)
        if self.resources.get('psc_attachments') or self.resources.get('psc_forwarding_rules'):
            with open(output_path / "private_service_connect.tf", "w") as f:
                f.write(self.generate_private_service_connect_tf())
            print("   ✓ private_service_connect.tf")
        
        # Cloud Tasks (FASE 5)
        if self.resources.get('cloud_tasks_queues'):
            with open(output_path / "cloud_tasks.tf", "w") as f:
                f.write(self.generate_cloud_tasks_tf())
            print("   ✓ cloud_tasks.tf")
        
        # Workload Identity (FASE 5)
        if self.resources.get('workload_identity_bindings'):
            with open(output_path / "workload_identity.tf", "w") as f:
                f.write(self.generate_workload_identity_tf())
            print("   ✓ workload_identity.tf")
        
        # Security Command Center (FASE 5)
        if self.resources.get('scc_sources'):
            with open(output_path / "security_command_center.tf", "w") as f:
                f.write(self.generate_security_command_center_tf())
            print("   ✓ security_command_center.tf")
        
        # Binary Authorization (FASE 5)
        if self.resources.get('binary_authz_policy') or self.resources.get('binary_authz_attestors'):
            with open(output_path / "binary_authorization.tf", "w") as f:
                f.write(self.generate_binary_authorization_tf())
            print("   ✓ binary_authorization.tf")
        
        # Commitments (FASE 6)
        if self.resources.get('commitments'):
            with open(output_path / "commitments.tf", "w") as f:
                f.write(self.generate_commitments_tf())
            print("   ✓ commitments.tf")
        
        # Reservations (FASE 6)
        if self.resources.get('reservations'):
            with open(output_path / "reservations.tf", "w") as f:
                f.write(self.generate_reservations_tf())
            print("   ✓ reservations.tf")
        
        # Cloud CDN (FASE 6)
        if self.resources.get('cloud_cdn_services'):
            with open(output_path / "cloud_cdn.tf", "w") as f:
                f.write(self.generate_cloud_cdn_tf())
            print("   ✓ cloud_cdn.tf")
        
        # Log Sinks (FASE 6)
        if self.resources.get('log_sinks'):
            with open(output_path / "log_sinks.tf", "w") as f:
                f.write(self.generate_log_sinks_tf())
            print("   ✓ log_sinks.tf")
        
        # Uptime Checks (FASE 6)
        if self.resources.get('uptime_checks'):
            with open(output_path / "uptime_checks.tf", "w") as f:
                f.write(self.generate_uptime_checks_tf())
            print("   ✓ uptime_checks.tf")
        
        # BigQuery Routines (FASE 6)
        if self.resources.get('bigquery_routines') or self.resources.get('bigquery_transfers'):
            with open(output_path / "bigquery_routines.tf", "w") as f:
                f.write(self.generate_bigquery_routines_tf())
            print("   ✓ bigquery_routines.tf")
        
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
- **Health Checks**: {len(self.resources.get('health_checks', []))} health check(s) ⭐ FASE 2
- **SSL Certificates**: {len(self.resources.get('ssl_certificates', []))} certificado(s) ⭐ FASE 2
- **VPN Gateways**: {len(self.resources.get('vpn_gateways', []))} gateway(s)
- **VPN Tunnels**: {len(self.resources.get('vpn_tunnels', []))} tunnel(s)
- **VPC Peering**: {len(self.resources.get('peerings', []))} conexão(ões)
- **Cloud Interconnect**: {len(self.resources.get('interconnects', []))} interconnect(s) 🚀 FASE 3
- **Interconnect Attachments**: {len(self.resources.get('interconnect_attachments', []))} attachment(s) 🚀 FASE 3
- **Private Service Connect**: {len(self.resources.get('psc_attachments', []))} service attachment(s) 🏆 FASE 5
- **Cloud CDN**: {len(self.resources.get('cloud_cdn_services', []))} backend service(s) com CDN 💎 FASE 6

### 💻 Compute & Storage
- **Compute Instances**: {len(self.resources.get('instances', []))} VM(s)
- **Instance Templates**: {len(self.resources.get('instance_templates', []))} template(s) ⭐ FASE 1
- **Managed Instance Groups**: {len(self.resources.get('managed_instance_groups', []))} MIG(s) ⭐ FASE 1
- **Autoscalers**: {len(self.resources.get('autoscalers', []))} autoscaler(s) 🎯 FASE 4
- **Commitments (CUDs)**: {len(self.resources.get('commitments', []))} commitment(s) 💎 FASE 6
- **Reservations**: {len(self.resources.get('reservations', []))} reservation(s) 💎 FASE 6
- **Compute Disks**: {len(self.resources.get('compute_disks', []))} disco(s) ⭐ FASE 1
- **Compute Snapshots**: {len(self.resources.get('compute_snapshots', []))} snapshot(s) ⭐ FASE 1
- **Compute Images**: {len(self.resources.get('compute_images', []))} imagem(ns) ⭐ FASE 2
- **Storage Buckets**: {len(self.resources.get('buckets', []))} bucket(s)
- **Filestore Instances**: {len(self.resources.get('filestore_instances', []))} instance(s) 🚀 FASE 3
- **Cloud Functions**: {len(self.resources.get('functions', []))} function(s)

### 🔧 Containers & Orchestration
- **GKE Clusters**: {len(self.resources.get('gke_clusters', []))} cluster(s)
- **GKE Node Pools**: {len(self.resources.get('gke_node_pools', []))} node pool(s) 🚀 FASE 3
- **Binary Authorization**: {len(self.resources.get('binary_authz_attestors', []))} attestor(s) 🏆 FASE 5

### 📊 Data & Analytics
- **Cloud SQL**: {len(self.resources.get('sql_instances', []))} instância(s)
- **BigQuery Tables**: {len(self.resources.get('bigquery_tables', []))} tabela(s) 🚀 FASE 3
- **BigQuery Routines**: {len(self.resources.get('bigquery_routines', []))} routine(s) 💎 FASE 6
- **BigQuery Scheduled Queries**: {len(self.resources.get('bigquery_transfers', []))} scheduled query(ies) 💎 FASE 6
- **Cloud Spanner**: {len(self.resources.get('spanner_instances', []))} instance(s) 🚀 FASE 3
- **Cloud Bigtable**: {len(self.resources.get('bigtable_instances', []))} instance(s) 🎯 FASE 4
- **Dataproc Clusters**: {len(self.resources.get('dataproc_clusters', []))} cluster(s) 🚀 FASE 3

### 📨 Messaging
- **Pub/Sub Topics**: {len(self.resources.get('pubsub_topics', []))} topic(s)
- **Pub/Sub Subscriptions**: {len(self.resources.get('pubsub_subscriptions', []))} subscription(s) 🚀 FASE 3
- **Pub/Sub Schemas**: {len(self.resources.get('pubsub_schemas', []))} schema(s) 🚀 FASE 3
- **Cloud Tasks**: {len(self.resources.get('cloud_tasks_queues', []))} task queue(s) 🏆 FASE 5

### 📈 Monitoring & Logging
- **Monitoring Dashboards**: {len(self.resources.get('monitoring_dashboards', []))} dashboard(s) 🚀 FASE 3
- **Alerting Policies**: {len(self.resources.get('alerting_policies', []))} policy(ies) 🚀 FASE 3
- **Uptime Checks**: {len(self.resources.get('uptime_checks', []))} uptime check(s) 💎 FASE 6
- **Log Sinks**: {len(self.resources.get('log_sinks', []))} log sink(s) 💎 FASE 6

### 🔐 Security & IAM
- **Service Accounts**: {len(self.resources.get('service_accounts', []))} SA(s)
- **Service Account Keys**: {len(self.resources.get('sa_keys', []))} chave(s) ⭐ FASE 2
- **IAM Policy Bindings**: {len(self.resources.get('iam_policy', {}).get('bindings', []))} binding(s) ⭐ FASE 1
- **IAM Custom Roles**: {len(self.resources.get('custom_roles', []))} role(s) ⭐ FASE 2
- **Cloud Armor Policies**: {len(self.resources.get('security_policies', []))} policy(ies) ⭐ FASE 2
- **Workload Identity**: {len(self.resources.get('workload_identity_bindings', []))} binding(s) 🏆 FASE 5
- **Security Command Center**: {len(self.resources.get('scc_sources', []))} source(s) 🏆 FASE 5

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
    import argparse
    
    parser = argparse.ArgumentParser(
        description='🚀 Extrai recursos do GCP e gera arquivos Terraform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python3 gcp_to_terraform.py --project meu-projeto
  python3 gcp_to_terraform.py --project meu-projeto --output terraform_meu_projeto
  python3 gcp_to_terraform.py -p meu-projeto -o saida

Recursos Suportados (59 tipos - 100% de cobertura):
  • Networking (18): VPC, Subnets, Firewall, VPN, Peering, CDN, etc
  • Compute (14): VMs, MIGs, Autoscalers, Disks, Images, CUDs, Reservations
  • Containers (4): GKE, Node Pools, Binary Authorization
  • Data (9): BigQuery, Cloud SQL, Spanner, Bigtable, Routines
  • Serverless (6): Cloud Functions, Run, Pub/Sub, Tasks
  • Monitoring (4): Dashboards, Alerts, Uptime Checks, Log Sinks
  • Security (10): IAM, KMS, Secret Manager, Cloud Armor, Workload Identity
  • Development (2): Artifact Registry, Dataflow
        '''
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='GCP Project ID (obrigatório)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Diretório de saída (padrão: terraform_<project-id>)'
    )
    
    args = parser.parse_args()
    
    extractor = GCPToTerraform(args.project, args.output)
    extractor.extract_all()
    extractor.save_terraform_files()
    
    print(f"📁 Arquivos salvos em: {extractor.output_dir}")
    print(f"\n💡 Próximos passos:")
    print(f"   cd {extractor.output_dir}")
    print(f"   terraform init")
    print(f"   terraform plan")


if __name__ == "__main__":
    main()
