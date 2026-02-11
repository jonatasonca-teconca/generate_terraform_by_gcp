#!/usr/bin/env python3
"""
Script para extrair recursos da ORGANIZAÇÃO GCP e gerar arquivos Terraform
Uso: python3 gcp_org_to_terraform.py <org-id>
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Any


class GCPOrgToTerraform:
    def __init__(self, org_id: str, output_dir: str = None):
        self.org_id = org_id
        self.output_dir = output_dir or f"./org-{org_id}"
        self.resources = {}
        self.org_info = {}
        
    def run_gcloud(self, command: str, use_org: bool = True) -> Any:
        """Executa comando gcloud e retorna JSON"""
        try:
            if use_org and "--organization" not in command:
                full_cmd = f"gcloud {command} --organization={self.org_id} --format=json"
            else:
                full_cmd = f"gcloud {command} --format=json"
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            return json.loads(result.stdout) if result.stdout else []
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Erro ao executar: {command}")
            print(f"    {e.stderr[:200]}")
            return [] if "list" in command else {}
        except json.JSONDecodeError:
            return []
    
    def get_org_info(self):
        """Obtém informações básicas da organização"""
        print("🏢 Obtendo informações da organização...")
        try:
            result = subprocess.run(
                f"gcloud organizations describe {self.org_id} --format=json",
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            self.org_info = json.loads(result.stdout)
            print(f"   ✓ Organização: {self.org_info.get('displayName', 'N/A')}")
            print(f"   ✓ ID: {self.org_id}")
            print(f"   ✓ Directory Customer ID: {self.org_info.get('directoryCustomerId', 'N/A')}")
        except Exception as e:
            print(f"   ⚠️  Erro ao obter info da org: {e}")
            self.org_info = {'name': f'organizations/{self.org_id}'}
    
    def extract_folders(self):
        """Extrai folders da organização"""
        print("📁 Extraindo Folders...")
        folders = self.run_gcloud(f"resource-manager folders list --organization={self.org_id}")
        self.resources['folders'] = folders
        print(f"   ✓ {len(folders)} folders encontrados")
        
        # Para cada folder, pegar subfolders
        all_folders = folders.copy()
        for folder in folders:
            folder_id = folder.get('name', '').split('/')[-1]
            if folder_id:
                subfolders = self.run_gcloud(
                    f"resource-manager folders list --folder={folder_id}",
                    use_org=False
                )
                all_folders.extend(subfolders)
        
        self.resources['all_folders'] = all_folders
        print(f"   ✓ {len(all_folders)} folders totais (incluindo subfolders)")
    
    def extract_projects(self):
        """Lista todos os projetos da organização"""
        print("📦 Extraindo Projetos...")
        projects = self.run_gcloud(
            f'projects list --filter="parent.id={self.org_id}"',
            use_org=False
        )
        self.resources['projects'] = projects
        print(f"   ✓ {len(projects)} projetos encontrados")
        
        # Listar projetos por folder
        for folder in self.resources.get('all_folders', []):
            folder_id = folder.get('name', '').split('/')[-1]
            if folder_id:
                folder_projects = self.run_gcloud(
                    f'projects list --filter="parent.id={folder_id}"',
                    use_org=False
                )
                if folder_projects:
                    print(f"      → Folder {folder.get('displayName', folder_id)}: {len(folder_projects)} projetos")
    
    def extract_org_policies(self):
        """Extrai Organization Policies"""
        print("📜 Extraindo Organization Policies...")
        try:
            # Lista todas as constraints disponíveis
            policies = self.run_gcloud(
                f"resource-manager org-policies list --organization={self.org_id}"
            )
            self.resources['org_policies'] = policies
            print(f"   ✓ {len(policies)} policies configuradas")
            
            # Detalhe de cada policy
            detailed_policies = []
            for policy in policies[:10]:  # Limitar a 10 para não demorar muito
                constraint = policy.get('constraint', '')
                if constraint:
                    detail = self.run_gcloud(
                        f"resource-manager org-policies describe {constraint} --organization={self.org_id}"
                    )
                    if detail:
                        detailed_policies.append(detail)
            
            self.resources['org_policies_detailed'] = detailed_policies
            
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair policies: {e}")
            self.resources['org_policies'] = []
    
    def extract_org_iam(self):
        """Extrai IAM policies da organização"""
        print("🔐 Extraindo IAM Policies da Organização...")
        try:
            iam_policy = self.run_gcloud(
                f"organizations get-iam-policy {self.org_id}"
            )
            self.resources['org_iam_policy'] = iam_policy
            
            bindings = iam_policy.get('bindings', []) if isinstance(iam_policy, dict) else []
            print(f"   ✓ {len(bindings)} role bindings encontrados")
            
            # Contar membros únicos
            members = set()
            for binding in bindings:
                members.update(binding.get('members', []))
            print(f"   ✓ {len(members)} membros únicos")
            
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair IAM: {e}")
            self.resources['org_iam_policy'] = {}
    
    def extract_tags(self):
        """Extrai Tags organizacionais"""
        print("🏷️  Extraindo Tags Organizacionais...")
        try:
            # Tag Keys
            tag_keys = self.run_gcloud(
                f"resource-manager tags keys list --parent=organizations/{self.org_id}"
            )
            self.resources['tag_keys'] = tag_keys
            print(f"   ✓ {len(tag_keys)} tag keys encontradas")
            
            # Tag Values para cada key
            all_tag_values = []
            for tag_key in tag_keys:
                key_name = tag_key.get('name', '')
                if key_name:
                    tag_values = self.run_gcloud(
                        f"resource-manager tags values list --parent={key_name}",
                        use_org=False
                    )
                    all_tag_values.extend(tag_values)
            
            self.resources['tag_values'] = all_tag_values
            print(f"   ✓ {len(all_tag_values)} tag values encontrados")
            
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair tags: {e}")
            self.resources['tag_keys'] = []
            self.resources['tag_values'] = []
    
    def extract_billing(self):
        """Extrai informações de billing"""
        print("💰 Extraindo Billing Accounts...")
        try:
            billing_accounts = self.run_gcloud("billing accounts list", use_org=False)
            self.resources['billing_accounts'] = billing_accounts
            print(f"   ✓ {len(billing_accounts)} billing accounts encontradas")
            
            # Para cada projeto, verificar billing
            if self.resources.get('projects'):
                projects_with_billing = []
                for project in self.resources['projects'][:5]:  # Limitar amostra
                    project_id = project.get('projectId', '')
                    if project_id:
                        try:
                            billing_info = self.run_gcloud(
                                f"billing projects describe {project_id}",
                                use_org=False
                            )
                            if billing_info:
                                projects_with_billing.append({
                                    'project': project_id,
                                    'billing': billing_info
                                })
                        except:
                            pass
                
                self.resources['projects_billing'] = projects_with_billing
                
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair billing: {e}")
            self.resources['billing_accounts'] = []
    
    def extract_all(self):
        """Extrai todos os recursos da organização"""
        print(f"\n🚀 Iniciando extração da Organização: {self.org_id}\n")
        print("="*60)
        
        self.get_org_info()
        self.extract_folders()
        self.extract_projects()
        self.extract_org_policies()
        self.extract_org_iam()
        self.extract_tags()
        self.extract_billing()
        
        print("="*60)
        print(f"\n✅ Extração da organização concluída!\n")
    
    def sanitize_name(self, name: str) -> str:
        """Sanitiza nome para uso em Terraform"""
        return name.replace(".", "_").replace("-", "_").replace("/", "_").replace(" ", "_")
    
    def generate_org_tf(self) -> str:
        """Gera HCL para organização"""
        hcl = "# Organization\n\n"
        
        hcl += f'data "google_organization" "org" {{\n'
        hcl += f'  organization = "{self.org_id}"\n'
        hcl += '}\n\n'
        
        return hcl
    
    def generate_folders_tf(self) -> str:
        """Gera HCL para folders"""
        hcl = "# Folders\n\n"
        
        for folder in self.resources.get('all_folders', []):
            display_name = folder.get('displayName', '')
            folder_id = folder.get('name', '').split('/')[-1]
            parent = folder.get('parent', '')
            
            if not folder_id:
                continue
            
            tf_name = self.sanitize_name(display_name or folder_id)
            
            hcl += f'resource "google_folder" "{tf_name}" {{\n'
            hcl += f'  display_name = "{display_name}"\n'
            hcl += f'  parent       = "{parent}"\n'
            hcl += '}\n\n'
        
        return hcl
    
    def generate_org_policies_tf(self) -> str:
        """Gera HCL para organization policies"""
        hcl = "# Organization Policies\n\n"
        
        for policy in self.resources.get('org_policies_detailed', []):
            constraint = policy.get('constraint', '').split('/')[-1]
            if not constraint:
                continue
            
            tf_name = self.sanitize_name(constraint)
            
            hcl += f'resource "google_organization_policy" "{tf_name}" {{\n'
            hcl += f'  org_id     = "{self.org_id}"\n'
            hcl += f'  constraint = "{policy.get("constraint", "")}"\n'
            
            # Boolean Policy
            if policy.get('booleanPolicy'):
                enforced = policy['booleanPolicy'].get('enforced', False)
                hcl += f'\n  boolean_policy {{\n'
                hcl += f'    enforced = {str(enforced).lower()}\n'
                hcl += f'  }}\n'
            
            # List Policy
            elif policy.get('listPolicy'):
                list_policy = policy['listPolicy']
                hcl += f'\n  list_policy {{\n'
                
                if list_policy.get('allowedValues'):
                    hcl += f'    allow {{\n'
                    hcl += f'      values = {json.dumps(list_policy["allowedValues"])}\n'
                    hcl += f'    }}\n'
                
                if list_policy.get('deniedValues'):
                    hcl += f'    deny {{\n'
                    hcl += f'      values = {json.dumps(list_policy["deniedValues"])}\n'
                    hcl += f'    }}\n'
                
                if list_policy.get('allValues'):
                    hcl += f'    suggested_value = "{list_policy["allValues"]}"\n'
                
                hcl += f'  }}\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_org_iam_tf(self) -> str:
        """Gera HCL para IAM da organização"""
        hcl = "# Organization IAM Bindings\n\n"
        
        iam_policy = self.resources.get('org_iam_policy', {})
        bindings = iam_policy.get('bindings', []) if isinstance(iam_policy, dict) else []
        
        for i, binding in enumerate(bindings):
            role = binding.get('role', '')
            members = binding.get('members', [])
            
            if not role or not members:
                continue
            
            # Sanitizar nome do role para Terraform
            tf_name = self.sanitize_name(role.replace('roles/', ''))
            
            hcl += f'resource "google_organization_iam_binding" "{tf_name}_{i}" {{\n'
            hcl += f'  org_id  = "{self.org_id}"\n'
            hcl += f'  role    = "{role}"\n'
            hcl += f'  members = [\n'
            for member in members:
                hcl += f'    "{member}",\n'
            hcl += f'  ]\n'
            
            # Condition (se existir)
            if binding.get('condition'):
                condition = binding['condition']
                hcl += f'\n  condition {{\n'
                hcl += f'    title       = "{condition.get("title", "")}"\n'
                hcl += f'    description = "{condition.get("description", "")}"\n'
                hcl += f'    expression  = "{condition.get("expression", "")}"\n'
                hcl += f'  }}\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def generate_tags_tf(self) -> str:
        """Gera HCL para tags"""
        hcl = "# Organization Tags\n\n"
        
        # Tag Keys
        for tag_key in self.resources.get('tag_keys', []):
            short_name = tag_key.get('shortName', '')
            key_name = tag_key.get('name', '')
            
            if not short_name:
                continue
            
            tf_name = self.sanitize_name(short_name)
            
            hcl += f'resource "google_tags_tag_key" "{tf_name}" {{\n'
            hcl += f'  parent      = "organizations/{self.org_id}"\n'
            hcl += f'  short_name  = "{short_name}"\n'
            
            if tag_key.get('description'):
                hcl += f'  description = "{tag_key["description"]}"\n'
            
            hcl += '}\n\n'
        
        # Tag Values
        for tag_value in self.resources.get('tag_values', []):
            short_name = tag_value.get('shortName', '')
            parent = tag_value.get('parent', '')
            
            if not short_name or not parent:
                continue
            
            parent_key = parent.split('/')[-1]
            tf_name = self.sanitize_name(f"{parent_key}_{short_name}")
            
            hcl += f'resource "google_tags_tag_value" "{tf_name}" {{\n'
            hcl += f'  parent      = "{parent}"\n'
            hcl += f'  short_name  = "{short_name}"\n'
            
            if tag_value.get('description'):
                hcl += f'  description = "{tag_value["description"]}"\n'
            
            hcl += '}\n\n'
        
        return hcl
    
    def save_terraform_files(self):
        """Salva arquivos Terraform"""
        output_path = Path(self.output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n📝 Gerando arquivos Terraform em: {self.output_dir}\n")
        
        # Provider
        provider_tf = f'''terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

provider "google" {{
  # Credenciais serão lidas de GOOGLE_APPLICATION_CREDENTIALS
  # ou usar: gcloud auth application-default login
}}
'''
        with open(output_path / "provider.tf", "w") as f:
            f.write(provider_tf)
        print("   ✓ provider.tf")
        
        # Variables
        variables_tf = f'''variable "org_id" {{
  description = "Organization ID"
  type        = string
  default     = "{self.org_id}"
}}

variable "org_display_name" {{
  description = "Organization Display Name"
  type        = string
  default     = "{self.org_info.get("displayName", "")}"
}}
'''
        with open(output_path / "variables.tf", "w") as f:
            f.write(variables_tf)
        print("   ✓ variables.tf")
        
        # Organization
        org_content = self.generate_org_tf()
        with open(output_path / "organization.tf", "w") as f:
            f.write(org_content)
        print("   ✓ organization.tf")
        
        # Folders
        if self.resources.get('all_folders'):
            folders_content = self.generate_folders_tf()
            with open(output_path / "folders.tf", "w") as f:
                f.write(folders_content)
            print("   ✓ folders.tf")
        
        # Organization Policies
        if self.resources.get('org_policies_detailed'):
            policies_content = self.generate_org_policies_tf()
            with open(output_path / "org_policies.tf", "w") as f:
                f.write(policies_content)
            print("   ✓ org_policies.tf")
        
        # IAM
        if self.resources.get('org_iam_policy'):
            iam_content = self.generate_org_iam_tf()
            with open(output_path / "org_iam.tf", "w") as f:
                f.write(iam_content)
            print("   ✓ org_iam.tf")
        
        # Tags
        if self.resources.get('tag_keys') or self.resources.get('tag_values'):
            tags_content = self.generate_tags_tf()
            with open(output_path / "tags.tf", "w") as f:
                f.write(tags_content)
            print("   ✓ tags.tf")
        
        # README
        readme = self.generate_readme()
        with open(output_path / "README.md", "w") as f:
            f.write(readme)
        print("   ✓ README.md")
        
        # JSON completo dos recursos
        with open(output_path / "resources.json", "w") as f:
            json.dump(self.resources, f, indent=2)
        print("   ✓ resources.json")
        
        print(f"\n✅ Arquivos Terraform gerados com sucesso!\n")
    
    def generate_readme(self) -> str:
        """Gera README"""
        return f'''# Terraform - Organization {self.org_id}

**Organização:** {self.org_info.get("displayName", "N/A")}  
**ID:** {self.org_id}  
**Directory Customer ID:** {self.org_info.get("directoryCustomerId", "N/A")}

Recursos da organização extraídos automaticamente do GCP.

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

### 📁 Estrutura
- **Folders**: {len(self.resources.get('all_folders', []))} folder(s)
- **Projetos**: {len(self.resources.get('projects', []))} projeto(s)

### 📜 Governance
- **Organization Policies**: {len(self.resources.get('org_policies', []))} policy(ies)
- **IAM Bindings**: {len(self.resources.get('org_iam_policy', {}).get('bindings', []))} binding(s)

### 🏷️ Tags
- **Tag Keys**: {len(self.resources.get('tag_keys', []))} key(s)
- **Tag Values**: {len(self.resources.get('tag_values', []))} value(s)

### 💰 Billing
- **Billing Accounts**: {len(self.resources.get('billing_accounts', []))} account(s)

## Projetos na Organização

{self._format_projects_list()}

## ⚠️ IMPORTANTE

Este código foi gerado automaticamente e deve ser **REVISADO** antes do uso.

**NÃO execute `terraform apply` sem revisão completa!**

Especialmente importante para:
- IAM policies (podem afetar permissões críticas)
- Organization policies (podem bloquear recursos)
- Billing (pode afetar custos)
'''
    
    def _format_projects_list(self) -> str:
        """Formata lista de projetos para o README"""
        projects = self.resources.get('projects', [])
        if not projects:
            return "Nenhum projeto encontrado."
        
        result = "| Project ID | Nome | State |\n"
        result += "|------------|------|-------|\n"
        for project in projects:
            project_id = project.get('projectId', 'N/A')
            name = project.get('name', 'N/A')
            state = project.get('lifecycleState', 'N/A')
            result += f"| {project_id} | {name} | {state} |\n"
        
        return result


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 gcp_org_to_terraform.py <org-id> [output-dir]")
        print("\nExemplo: python3 gcp_org_to_terraform.py 109234159153")
        sys.exit(1)
    
    org_id = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    extractor = GCPOrgToTerraform(org_id, output_dir)
    extractor.extract_all()
    extractor.save_terraform_files()
    
    print(f"📁 Arquivos salvos em: {extractor.output_dir}")
    print(f"\n💡 Próximos passos:")
    print(f"   cd {extractor.output_dir}")
    print(f"   terraform init")
    print(f"   terraform plan")


if __name__ == "__main__":
    main()
