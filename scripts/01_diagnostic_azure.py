#!/usr/bin/env python
"""
Script de diagnostic Azure ML - Vérifie l'authentification, l'abonnement et le workspace
"""
import sys
import subprocess
import json
from pathlib import Path

def run_cmd(cmd, check=False):
    """Exécute une commande et retourne la sortie"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_azure_cli():
    """Vérifie si Azure CLI est installée"""
    print_section("1. VÉRIFICATION AZURE CLI")
    stdout, stderr, rc = run_cmd("az version")
    if rc == 0:
        print("✅ Azure CLI installée")
        try:
            version_data = json.loads(stdout)
            print(f"   Version: {version_data.get('azure-cli', 'N/A')}")
            print(f"   Azure ML extension: {version_data.get('azure-cli-ml', 'N/A')}")
        except:
            print(stdout)
    else:
        print(f"❌ Erreur: {stderr}")
        return False
    return True

def check_authentication():
    """Vérifie l'authentification active"""
    print_section("2. VÉRIFICATION AUTHENTIFICATION")
    
    # Vérifier l'utilisateur actuellement connecté
    stdout, stderr, rc = run_cmd("az account show")
    if rc == 0:
        try:
            account = json.loads(stdout)
            print(f"✅ Utilisateur connecté:")
            print(f"   ID: {account.get('id', 'N/A')}")
            print(f"   Nom: {account.get('name', 'N/A')}")
            print(f"   Type: {account.get('user', {}).get('type', 'N/A')}")
        except:
            print(stdout)
    else:
        print(f"❌ Pas d'authentification active: {stderr}")
        print("   👉 Exécutez: az login")
        return False
    
    return True

def check_subscription():
    """Vérifie l'abonnement et le contexte"""
    print_section("3. VÉRIFICATION ABONNEMENT")
    
    SUBSCRIPTION_ID = "eb1cf44f-57ae-4310-8998-c0a2a0886a86"
    
    # Lister les abonnements
    stdout, stderr, rc = run_cmd("az account list --output json")
    if rc == 0:
        try:
            subs = json.loads(stdout)
            print(f"✅ Abonnements disponibles: {len(subs)}")
            for sub in subs:
                is_default = "🔵 (par défaut)" if sub.get('isDefault') else ""
                print(f"   - {sub.get('name')} ({sub.get('id')}) {is_default}")
        except:
            print(stdout)
    else:
        print(f"❌ Erreur: {stderr}")
    
    # Vérifier si l'abonnement cible est défini
    stdout, stderr, rc = run_cmd("az account show")
    if rc == 0:
        try:
            current = json.loads(stdout)
            if current.get('id') == SUBSCRIPTION_ID:
                print(f"✅ Abonnement correct défini: {SUBSCRIPTION_ID}")
            else:
                print(f"⚠️  Abonnement actif: {current.get('id')}")
                print(f"   Attendu: {SUBSCRIPTION_ID}")
                print(f"   👉 Corrigez: az account set --subscription {SUBSCRIPTION_ID}")
        except:
            pass
    
    return True

def check_resource_group():
    """Vérifie le groupe de ressources"""
    print_section("4. VÉRIFICATION GROUPE DE RESSOURCES")
    
    RG_NAME = "rg-mlops-final"
    SUBSCRIPTION_ID = "eb1cf44f-57ae-4310-8998-c0a2a0886a86"
    
    stdout, stderr, rc = run_cmd(f"az group show --name {RG_NAME} --subscription {SUBSCRIPTION_ID}")
    if rc == 0:
        try:
            rg = json.loads(stdout)
            print(f"✅ Groupe de ressources trouvé:")
            print(f"   Nom: {rg.get('name')}")
            print(f"   Région: {rg.get('location')}")
            print(f"   ID: {rg.get('id')}")
        except:
            print(stdout)
    else:
        print(f"❌ Erreur: {stderr}")
        return False
    
    return True

def check_workspace():
    """Vérifie le workspace Azure ML"""
    print_section("5. VÉRIFICATION WORKSPACE AZURE ML")
    
    WS_NAME = "churn"
    RG_NAME = "rg-mlops-final"
    SUBSCRIPTION_ID = "eb1cf44f-57ae-4310-8998-c0a2a0886a86"
    
    stdout, stderr, rc = run_cmd(
        f"az ml workspace show --name {WS_NAME} --resource-group {RG_NAME} --subscription {SUBSCRIPTION_ID}"
    )
    if rc == 0:
        try:
            ws = json.loads(stdout)
            print(f"✅ Workspace trouvé:")
            print(f"   Nom: {ws.get('name')}")
            print(f"   Région: {ws.get('location')}")
            print(f"   ID: {ws.get('id')}")
        except:
            print(stdout)
    else:
        print(f"❌ Erreur: {stderr}")
        return False
    
    return True

def check_endpoints():
    """Liste les endpoints existants"""
    print_section("6. VÉRIFICATION ENDPOINTS EXISTANTS")
    
    WS_NAME = "churn"
    RG_NAME = "rg-mlops-final"
    SUBSCRIPTION_ID = "eb1cf44f-57ae-4310-8998-c0a2a0886a86"
    
    stdout, stderr, rc = run_cmd(
        f"az ml online-endpoint list --resource-group {RG_NAME} --workspace-name {WS_NAME} --subscription {SUBSCRIPTION_ID} --output json"
    )
    if rc == 0:
        try:
            endpoints = json.loads(stdout)
            if endpoints:
                print(f"✅ {len(endpoints)} endpoint(s) trouvé(s):")
                for ep in endpoints:
                    provisioning_state = ep.get('properties', {}).get('provisioning_state', 'N/A')
                    print(f"   - {ep.get('name')} (État: {provisioning_state})")
                    if provisioning_state not in ['Succeeded']:
                        print(f"     ⚠️  Cet endpoint peut être bloqué!")
            else:
                print("✅ Aucun endpoint trouvé (c'est normal si c'est la première déploiement)")
        except Exception as e:
            print(f"Réponse brute: {stdout}")
    else:
        print(f"❌ Erreur: {stderr}")

def check_env_variables():
    """Vérifie les variables d'environnement Azure"""
    print_section("7. VÉRIFICATION VARIABLES D'ENVIRONNEMENT")
    
    important_vars = [
        'AZURE_SUBSCRIPTION_ID',
        'AZURE_RESOURCE_GROUP',
        'AZURE_ML_WORKSPACE',
        'AZURE_TENANT_ID',
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET'
    ]
    
    for var in important_vars:
        value = subprocess.os.getenv(var, "Non définie")
        if var == 'AZURE_CLIENT_SECRET' or var == 'AZURE_TENANT_ID':
            status = "✅" if value != "Non définie" else "⚠️ "
        else:
            status = "✅" if value != "Non définie" else "⚠️ "
        
        display_value = "***" if 'SECRET' in var else value
        print(f"{status} {var}: {display_value}")

def check_python_sdk():
    """Vérifie les packages Python nécessaires"""
    print_section("8. VÉRIFICATION SDK PYTHON AZURE ML")
    
    try:
        from azure.ai.ml import MLClient
        from azure.identity import DefaultAzureCredential
        print("✅ azure-ai-ml SDK installé")
        import azure.ai.ml
        print(f"   Version: {azure.ai.ml.__version__}")
    except ImportError as e:
        print(f"❌ azure-ai-ml SDK non installé: {e}")
        print("   👉 Installez: pip install azure-ai-ml azure-identity")
    
    try:
        from azure.identity import DefaultAzureCredential
        print("✅ azure-identity installé")
    except ImportError:
        print("❌ azure-identity non installé")

def main():
    print("\n" + "🔍 DIAGNOSTIC AZURE ML - Telco Churn MLOps".center(60, "="))
    
    all_checks = [
        check_azure_cli(),
        check_authentication(),
        check_subscription(),
        check_resource_group(),
        check_workspace(),
    ]
    
    check_endpoints()
    check_env_variables()
    check_python_sdk()
    
    print_section("📊 RÉSUMÉ DU DIAGNOSTIC")
    if all(all_checks):
        print("✅ Tous les contrôles critiques sont passés!")
        print("\n💡 Prochaines étapes:")
        print("   1. Essayez le déploiement avec 02_deploy_mlclient.py")
        print("   2. Si des endpoints bloqués existent, utilisez 03_cleanup_endpoints.py")
    else:
        print("⚠️  Certains contrôles critiques ont échoué!")
        print("   Veuillez corriger les erreurs ci-dessus avant de continuer.")
    
    print("\n")

if __name__ == "__main__":
    main()
