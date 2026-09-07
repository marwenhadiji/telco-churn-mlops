#!/usr/bin/env python
"""
Nettoyage des Managed Online Endpoints bloqués ("Ghost Endpoints")
Permet de forcer la suppression d'endpoints dans l'état Failed/Deleting

Utilisation:
    python 03_cleanup_endpoints.py --list              # Lister les endpoints
    python 03_cleanup_endpoints.py --delete <name>     # Forcer suppression
    python 03_cleanup_endpoints.py --force-delete-all  # Supprimer TOUS les endpoints
"""
import sys
import argparse
import logging
from pathlib import Path
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Azure
SUBSCRIPTION_ID = "eb1cf44f-57ae-4310-8998-c0a2a0886a86"
RESOURCE_GROUP = "rg-mlops-final"
WORKSPACE_NAME = "churn"

def get_ml_client():
    """Crée une instance MLClient"""
    try:
        logger.info("Authentification...")
        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False,
            exclude_environment_credential=False,
        )
        # Test la credential
        token = credential.get_token("https://management.azure.com/.default")
        
    except Exception as e:
        logger.warning(f"DefaultAzureCredential échouée: {e}")
        logger.info("Fallback vers InteractiveBrowserCredential...")
        try:
            credential = InteractiveBrowserCredential()
            token = credential.get_token("https://management.azure.com/.default")
        except Exception as e2:
            logger.error(f"Authentification échouée: {e2}")
            raise
    
    ml_client = MLClient(
        credential=credential,
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        workspace_name=WORKSPACE_NAME
    )
    
    logger.info(f"✅ Connecté au workspace: {WORKSPACE_NAME}")
    return ml_client

def list_endpoints(ml_client):
    """Liste tous les endpoints avec leurs états"""
    logger.info("\n" + "="*60)
    logger.info("LISTE DES ENDPOINTS")
    logger.info("="*60)
    
    try:
        endpoints = ml_client.online_endpoints.list()
        endpoint_list = list(endpoints)
        
        if not endpoint_list:
            logger.info("ℹ️  Aucun endpoint trouvé")
            return []
        
        logger.info(f"\n✅ {len(endpoint_list)} endpoint(s) trouvé(s):\n")
        
        for i, ep in enumerate(endpoint_list, 1):
            name = ep.name
            state = ep.provisioning_state
            auth_mode = ep.auth_mode
            scoring_uri = ep.scoring_uri if hasattr(ep, 'scoring_uri') else "N/A"
            
            # Code couleur basé sur l'état
            if state == "Succeeded":
                status_icon = "✅"
            elif state in ["Failed", "Deleting"]:
                status_icon = "❌"
            else:
                status_icon = "⏳"
            
            print(f"{i}. {status_icon} {name}")
            print(f"   État: {state}")
            print(f"   Auth Mode: {auth_mode}")
            print(f"   Scoring URI: {scoring_uri}")
            print()
        
        return endpoint_list
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des endpoints: {e}")
        return []

def delete_endpoint(ml_client, endpoint_name, force=False):
    """Supprime un endpoint"""
    logger.info(f"\n{'='*60}")
    logger.info(f"SUPPRESSION DE L'ENDPOINT: {endpoint_name}")
    logger.info(f"{'='*60}")
    
    try:
        # Vérifier l'état actuel de l'endpoint
        endpoint = ml_client.online_endpoints.get(endpoint_name)
        prov_state = endpoint.provisioning_state
        
        logger.info(f"État actuel: {prov_state}")
        
        if prov_state == "Deleting":
            logger.warning("⚠️  L'endpoint est déjà en suppression")
            logger.info("Attendez quelques minutes avant de recréer un endpoint avec le même nom")
            return False
        
        if not force and prov_state not in ["Failed", "Succeeded"]:
            response = input(f"\n⚠️  L'endpoint est dans l'état '{prov_state}'. Continuer la suppression? (y/n): ")
            if response.lower() != 'y':
                logger.info("Suppression annulée")
                return False
        
        logger.info("Envoi de la requête de suppression...")
        ml_client.online_endpoints.begin_delete(name=endpoint_name).result()
        
        logger.info("✅ Endpoint supprimé avec succès!")
        logger.info("ℹ️  Le nom peut être réutilisé après quelques minutes (délai ARM)")
        
        return True
        
    except Exception as e:
        if "not found" in str(e) or "NotFound" in str(e):
            logger.warning(f"⚠️  L'endpoint '{endpoint_name}' n'existe pas")
            return True
        else:
            logger.error(f"❌ Erreur lors de la suppression: {e}")
            logger.error(f"   Type: {type(e).__name__}")
            logger.info("\n💡 Si l'endpoint reste bloqué, attendez 15-30 minutes avant de réessayer")
            return False

def force_delete_all(ml_client):
    """Force la suppression de TOUS les endpoints (avec confirmation)"""
    logger.info("\n" + "="*60)
    logger.info("⚠️  SUPPRESSION DE TOUS LES ENDPOINTS")
    logger.info("="*60)
    
    endpoints = list(ml_client.online_endpoints.list())
    
    if not endpoints:
        logger.info("ℹ️  Aucun endpoint à supprimer")
        return True
    
    logger.warning(f"\n⚠️  Vous êtes sur le point de supprimer {len(endpoints)} endpoint(s):")
    for ep in endpoints:
        logger.warning(f"   - {ep.name} ({ep.provisioning_state})")
    
    response = input("\n⚠️  ÊTES-VOUS SÛR? Tapez 'DELETE ALL' pour confirmer: ")
    
    if response != "DELETE ALL":
        logger.info("Opération annulée")
        return False
    
    logger.info("\nSuppression en cours...")
    
    all_success = True
    for ep in endpoints:
        success = delete_endpoint(ml_client, ep.name, force=True)
        if not success:
            all_success = False
    
    if all_success:
        logger.info("\n✅ Tous les endpoints ont été supprimés avec succès!")
    else:
        logger.warning("\n⚠️  Certains endpoints n'ont pas pu être supprimés. Réessayez dans quelques minutes.")
    
    return all_success

def get_endpoint_details(ml_client, endpoint_name):
    """Affiche les détails complets d'un endpoint"""
    logger.info(f"\n{'='*60}")
    logger.info(f"DÉTAILS DE L'ENDPOINT: {endpoint_name}")
    logger.info(f"{'='*60}")
    
    try:
        endpoint = ml_client.online_endpoints.get(endpoint_name)
        
        logger.info(f"\nInformations générales:")
        logger.info(f"  Nom: {endpoint.name}")
        logger.info(f"  État: {endpoint.provisioning_state}")
        logger.info(f"  Auth Mode: {endpoint.auth_mode}")
        logger.info(f"  Scoring URI: {endpoint.scoring_uri}")
        logger.info(f"  Swagger URI: {endpoint.swagger_uri if hasattr(endpoint, 'swagger_uri') else 'N/A'}")
        
        if hasattr(endpoint, 'tags'):
            logger.info(f"\n  Tags: {endpoint.tags}")
        
        if hasattr(endpoint, 'properties'):
            logger.info(f"\n  Propriétés: {endpoint.properties}")
        
        # Lister les deployments
        try:
            deployments = ml_client.online_deployments.list(endpoint_name)
            deployment_list = list(deployments)
            if deployment_list:
                logger.info(f"\n  Deployments ({len(deployment_list)}):")
                for dep in deployment_list:
                    logger.info(f"    - {dep.name} ({dep.provisioning_state})")
        except:
            logger.info("\n  Deployments: Impossible à récupérer")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Gérer les Managed Online Endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python 03_cleanup_endpoints.py --list
  python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v5
  python 03_cleanup_endpoints.py --details telco-churn-endpoint-v5
  python 03_cleanup_endpoints.py --force-delete-all
        """
    )
    parser.add_argument('--list', action='store_true', help='Lister tous les endpoints')
    parser.add_argument('--delete', metavar='NAME', help='Supprimer un endpoint spécifique')
    parser.add_argument('--details', metavar='NAME', help='Afficher les détails d\'un endpoint')
    parser.add_argument('--force-delete-all', action='store_true', help='Supprimer TOUS les endpoints (confirmation requise)')
    
    args = parser.parse_args()
    
    try:
        ml_client = get_ml_client()
        
        if args.list:
            list_endpoints(ml_client)
        
        elif args.delete:
            success = delete_endpoint(ml_client, args.delete)
            sys.exit(0 if success else 1)
        
        elif args.details:
            success = get_endpoint_details(ml_client, args.details)
            sys.exit(0 if success else 1)
        
        elif args.force_delete_all:
            success = force_delete_all(ml_client)
            sys.exit(0 if success else 1)
        
        else:
            # Par défaut, afficher la liste
            list_endpoints(ml_client)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
