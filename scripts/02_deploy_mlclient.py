#!/usr/bin/env python
"""
Déploiement via Azure ML SDK v2 (MLClient)
Contourne les problèmes de CLI Azure (SubscriptionNotRegistered [N/A], Ghost Endpoints)

Utilisation:
    python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6 --region norwayeast
"""
import sys
import argparse
from pathlib import Path
from azure.ai.ml import MLClient
from azure.ai.ml.entities import ManagedOnlineEndpoint, ManagedOnlineDeployment, Environment, CodeConfiguration
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
import yaml
import logging

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
REGION = "norwayeast"

def get_ml_client(subscription_id=SUBSCRIPTION_ID, resource_group=RESOURCE_GROUP, workspace_name=WORKSPACE_NAME):
    """
    Crée une instance MLClient avec authentification appropriée
    
    Stratégie d'authentification :
    1. DefaultAzureCredential (env vars, managed identity, az login)
    2. InteractiveBrowserCredential (fallback)
    """
    try:
        logger.info("Tentative connexion avec DefaultAzureCredential...")
        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False,
            exclude_environment_credential=False,
            exclude_managed_identity_credential=False,
        )
        
        # Test la credential
        token = credential.get_token("https://management.azure.com/.default")
        logger.info("✅ Authentification réussie via DefaultAzureCredential")
        
    except Exception as e:
        logger.warning(f"DefaultAzureCredential échouée: {e}")
        logger.info("Fallback vers InteractiveBrowserCredential...")
        try:
            credential = InteractiveBrowserCredential()
            token = credential.get_token("https://management.azure.com/.default")
            logger.info("✅ Authentification réussie via navigateur")
        except Exception as e2:
            logger.error(f"Toutes les méthodes d'authentification ont échoué: {e2}")
            raise
    
    # Créer le MLClient
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name,
        default_compute="compute-churn-dev"  # Adapter si nécessaire
    )
    
    logger.info(f"✅ MLClient créé pour:")
    logger.info(f"   - Subscription: {subscription_id}")
    logger.info(f"   - Resource Group: {resource_group}")
    logger.info(f"   - Workspace: {workspace_name}")
    
    return ml_client

def load_yaml_config(yaml_path):
    """Charge la configuration depuis un fichier YAML"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def create_endpoint(ml_client, endpoint_name, auth_mode="key"):
    """Crée un Managed Online Endpoint"""
    logger.info(f"\n{'='*60}")
    logger.info(f"CRÉATION DE L'ENDPOINT: {endpoint_name}")
    logger.info(f"{'='*60}")
    
    try:
        # Vérifier si l'endpoint existe déjà
        try:
            existing_endpoint = ml_client.online_endpoints.get(endpoint_name)
            prov_state = existing_endpoint.provisioning_state
            logger.info(f"⚠️  L'endpoint '{endpoint_name}' existe déjà")
            logger.info(f"   État de provisioning: {prov_state}")
            
            if prov_state == "Failed":
                logger.error("   ❌ L'endpoint est dans l'état 'Failed' - Suppression nécessaire")
                return False
            elif prov_state == "Deleting":
                logger.error("   ❌ L'endpoint est dans l'état 'Deleting' - Attendez avant de recréer")
                return False
            else:
                logger.info("   ✅ L'endpoint peut être utilisé ou mis à jour")
                return True
                
        except Exception as e:
            if "not found" in str(e) or "NotFound" in str(e):
                logger.info("✅ L'endpoint n'existe pas, création en cours...")
            else:
                raise
        
        # Créer le nouvel endpoint
        endpoint = ManagedOnlineEndpoint(
            name=endpoint_name,
            auth_mode=auth_mode,
            description="Managed Online Endpoint pour Telco Churn Prediction",
            tags={
                "project": "telco-churn",
                "environment": "production",
                "version": "v6"
            }
        )
        
        logger.info(f"Envoi de la requête de création au Resource Manager...")
        created_endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        
        logger.info("✅ Endpoint créé avec succès!")
        logger.info(f"   Nom: {created_endpoint.name}")
        logger.info(f"   URI: {created_endpoint.scoring_uri}")
        logger.info(f"   État: {created_endpoint.provisioning_state}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de l'endpoint: {e}")
        logger.error(f"   Type: {type(e).__name__}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def create_deployment(ml_client, endpoint_name, deployment_config_path):
    """Crée un Managed Online Deployment"""
    logger.info(f"\n{'='*60}")
    logger.info(f"CRÉATION DU DEPLOYMENT")
    logger.info(f"{'='*60}")
    
    try:
        # Charger la configuration du deployment
        config = load_yaml_config(deployment_config_path)
        logger.info(f"Configuration chargée depuis: {deployment_config_path}")
        
        deployment_name = config.get('name', 'xgboost-deployment')
        model_reference = config.get('model', 'azureml:Telco_Churn_XGBoost@latest')
        instance_type = config.get('instance_type', 'Standard_DS2_v2')
        instance_count = config.get('instance_count', 1)
        
        # Configuration du code
        code_config = config.get('code_configuration', {})
        code_path = code_config.get('code', '../src')
        scoring_script = code_config.get('scoring_script', 'score.py')
        
        # Configuration de l'environnement
        env_config = config.get('environment', {})
        env_name = env_config.get('name', 'churn-inference-env')
        env_version = env_config.get('version', '1')
        
        logger.info(f"Configuration du deployment:")
        logger.info(f"  - Nom: {deployment_name}")
        logger.info(f"  - Modèle: {model_reference}")
        logger.info(f"  - Environnement: {env_name}:{env_version}")
        logger.info(f"  - Instance type: {instance_type}")
        logger.info(f"  - Nombre d'instances: {instance_count}")
        
        # Créer la configuration du code
        code_configuration = CodeConfiguration(
            code=code_path,
            scoring_script=scoring_script
        )
        
        # Créer la configuration de l'environnement
        environment = Environment(
            name=env_name,
            version=str(env_version),
            image=env_config.get('image', 'mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest'),
            conda_file=env_config.get('conda_file', '../conda.yml')
        )
        
        # Créer le deployment
        deployment = ManagedOnlineDeployment(
            name=deployment_name,
            endpoint_name=endpoint_name,
            model=model_reference,
            code_configuration=code_configuration,
            environment=environment,
            instance_type=instance_type,
            instance_count=instance_count,
            app_insights_enabled=True,  # Activer les diagnostics
            request_settings={
                "request_timeout_ms": 60000,
                "max_concurrent_requests_per_instance": 1,
                "max_queue_wait_ms": 500,
            }
        )
        
        logger.info(f"Envoi de la requête de déploiement au Resource Manager...")
        created_deployment = ml_client.online_deployments.begin_create_or_update(deployment).result()
        
        logger.info("✅ Deployment créé/mis à jour avec succès!")
        logger.info(f"   Nom: {created_deployment.name}")
        logger.info(f"   État: {created_deployment.provisioning_state}")
        
        # Définir comme deployment par défaut
        logger.info("Définition du deployment comme par défaut...")
        endpoint = ml_client.online_endpoints.get(endpoint_name)
        endpoint.traffic = {deployment_name: 100}
        ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        logger.info("✅ Deployment défini comme par défaut")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du deployment: {e}")
        logger.error(f"   Type: {type(e).__name__}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Déployer un Managed Online Endpoint avec MLClient"
    )
    parser.add_argument(
        '--endpoint-name',
        default='telco-churn-endpoint-v7',
        help='Nom de l\'endpoint (défaut: telco-churn-endpoint-v7)'
    )
    parser.add_argument(
        '--skip-endpoint',
        action='store_true',
        help='Sauter la création de l\'endpoint'
    )
    parser.add_argument(
        '--region',
        default='norwayeast',
        help='Région Azure (défaut: norwayeast)'
    )
    
    args = parser.parse_args()
    
    # Déterminer les chemins de fichiers
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    endpoint_config = project_root / "azureml" / "endpoint.yml"
    deployment_config = project_root / "azureml" / "deployment.yml"
    
    logger.info(f"Répertoire du projet: {project_root}")
    logger.info(f"Configuration endpoint: {endpoint_config}")
    logger.info(f"Configuration deployment: {deployment_config}")
    
    if not endpoint_config.exists():
        logger.error(f"❌ Fichier de configuration endpoint non trouvé: {endpoint_config}")
        sys.exit(1)
    
    if not deployment_config.exists():
        logger.error(f"❌ Fichier de configuration deployment non trouvé: {deployment_config}")
        sys.exit(1)
    
    try:
        # Créer le MLClient
        ml_client = get_ml_client()
        
        # Créer l'endpoint
        if not args.skip_endpoint:
            if not create_endpoint(ml_client, args.endpoint_name):
                logger.error("Impossible de créer l'endpoint. Arrêt.")
                sys.exit(1)
        
        # Créer le deployment
        if not create_deployment(ml_client, args.endpoint_name, deployment_config):
            logger.error("Impossible de créer le deployment. Arrêt.")
            sys.exit(1)
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ DÉPLOIEMENT RÉUSSI!")
        logger.info(f"{'='*60}")
        logger.info(f"\nEndpoint: {args.endpoint_name}")
        logger.info(f"Workspace: {WORKSPACE_NAME}")
        logger.info(f"Resource Group: {RESOURCE_GROUP}")
        logger.info(f"\n💡 Pour tester l'endpoint:")
        logger.info(f"   az ml online-endpoint invoke --endpoint-name {args.endpoint_name} --request-file request.json")
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
