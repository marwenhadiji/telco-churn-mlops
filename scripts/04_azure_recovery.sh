#!/usr/bin/env bash
# ============================================================================
# SCRIPT DE RÉPARATION AZURE ML - Commandes de Secours
# ============================================================================
# Utilisation: bash 04_azure_recovery.sh <action>
# Actions disponibles:
#   - login              → Se reconnecter à Azure
#   - verify             → Vérifier la configuration complète
#   - configure-defaults → Définir les paramètres par défaut
#   - restart-docker     → Redémarrer le daemon Docker
#   - clear-cache        → Vider le cache d'authentification
# ============================================================================

set -e

SUBSCRIPTION_ID="eb1cf44f-57ae-4310-8998-c0a2a0886a86"
RESOURCE_GROUP="rg-mlops-final"
WORKSPACE_NAME="churn"
REGION="norwayeast"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

function login_to_azure() {
    print_header "RECONNECTER À AZURE"
    
    echo "Vérification de la connexion actuelle..."
    
    if az account show &>/dev/null; then
        CURRENT_ACCOUNT=$(az account show --query name -o tsv)
        CURRENT_SUB=$(az account show --query id -o tsv)
        print_success "Déjà connecté : $CURRENT_ACCOUNT"
        print_info "Abonnement: $CURRENT_SUB"
        
        read -p "Voulez-vous vous reconnecter? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    print_info "Lancement de l'authentification interactive..."
    az login --use-device-code
    
    print_success "Authentification réussie!"
}

function verify_configuration() {
    print_header "VÉRIFICATION COMPLÈTE"
    
    # Vérifier Azure CLI
    print_info "1. Vérification Azure CLI..."
    if command -v az &> /dev/null; then
        print_success "Azure CLI installée: $(az version --output json | jq '.["azure-cli"]' -r)"
    else
        print_error "Azure CLI not found"
        return 1
    fi
    
    # Vérifier authentification
    print_info "2. Vérification authentification..."
    if az account show &>/dev/null; then
        ACCOUNT=$(az account show --query name -o tsv)
        print_success "Connecté en tant que: $ACCOUNT"
    else
        print_error "Pas d'authentification active"
        print_info "Exécutez: bash $0 login"
        return 1
    fi
    
    # Vérifier abonnement
    print_info "3. Vérification abonnement..."
    CURRENT_SUB=$(az account show --query id -o tsv)
    if [ "$CURRENT_SUB" == "$SUBSCRIPTION_ID" ]; then
        print_success "Abonnement correct: $SUBSCRIPTION_ID"
    else
        print_warning "Abonnement actif: $CURRENT_SUB"
        print_info "Attendu: $SUBSCRIPTION_ID"
        print_info "Correction: az account set --subscription $SUBSCRIPTION_ID"
    fi
    
    # Vérifier groupe de ressources
    print_info "4. Vérification groupe de ressources..."
    if az group show --name "$RESOURCE_GROUP" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
        print_success "Groupe de ressources trouvé: $RESOURCE_GROUP"
    else
        print_error "Groupe de ressources NOT found: $RESOURCE_GROUP"
        return 1
    fi
    
    # Vérifier workspace
    print_info "5. Vérification workspace..."
    if az ml workspace show --name "$WORKSPACE_NAME" --resource-group "$RESOURCE_GROUP" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
        print_success "Workspace trouvé: $WORKSPACE_NAME"
    else
        print_error "Workspace NOT found: $WORKSPACE_NAME"
        return 1
    fi
    
    # Vérifier Python SDK
    print_info "6. Vérification SDK Python..."
    if python3 -c "from azure.ai.ml import MLClient" 2>/dev/null; then
        print_success "azure-ai-ml SDK installé"
    else
        print_warning "azure-ai-ml SDK NOT found"
        print_info "Installation: pip install azure-ai-ml azure-identity"
    fi
    
    print_success "Vérification complète réussie!"
}

function configure_defaults() {
    print_header "CONFIGURATION DES PARAMÈTRES PAR DÉFAUT"
    
    print_info "Définition des variables par défaut pour Azure CLI..."
    
    az configure --defaults \
        subscription="$SUBSCRIPTION_ID" \
        group="$RESOURCE_GROUP" \
        workspace="$WORKSPACE_NAME"
    
    print_success "Paramètres par défaut configurés!"
    
    print_info "Vérification des defaults..."
    az configure --list-defaults
}

function clear_authentication_cache() {
    print_header "VIDER LE CACHE D'AUTHENTIFICATION"
    
    print_warning "Cette action va supprimer le cache local d'authentification"
    read -p "Continuer? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Opération annulée"
        return
    fi
    
    # Vider le cache
    AZ_CACHE="$HOME/.azure"
    
    if [ -d "$AZ_CACHE" ]; then
        print_info "Suppression de $AZ_CACHE..."
        rm -rf "$AZ_CACHE"
        print_success "Cache supprimé!"
    else
        print_info "Cache non trouvé"
    fi
    
    # Déconnecter
    print_info "Déconnexion de Azure..."
    az logout || true
    
    print_success "Cache d'authentification vidé!"
    print_info "Vous devez vous reconnecter: bash $0 login"
}

function restart_docker() {
    print_header "REDÉMARRER DOCKER DAEMON"
    
    if ! command -v docker &> /dev/null; then
        print_warning "Docker n'est pas installé"
        return
    fi
    
    print_info "État actuel du daemon Docker..."
    docker info &>/dev/null && print_success "Docker est actif" || print_warning "Docker est arrêté"
    
    print_info "Redémarrage de Docker..."
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        open -a Docker || print_error "Impossible de lancer Docker"
    elif [ "$(uname)" == "Linux" ]; then
        # Linux
        sudo systemctl restart docker 2>/dev/null || print_error "Impossible de redémarrer Docker (root requis)"
    fi
    
    sleep 5
    
    if docker info &>/dev/null; then
        print_success "Docker redémarré avec succès!"
    else
        print_error "Docker n'a pas pu être redémarré"
    fi
}

function register_providers() {
    print_header "ENREGISTRER LES RESOURCE PROVIDERS AZURE"
    
    PROVIDERS=(
        "Microsoft.MachineLearningServices"
        "Microsoft.Compute"
        "Microsoft.Storage"
        "Microsoft.ContainerRegistry"
        "Microsoft.KeyVault"
        "Microsoft.Insights"
    )
    
    print_info "Enregistrement des providers pour l'abonnement $SUBSCRIPTION_ID..."
    
    for provider in "${PROVIDERS[@]}"; do
        print_info "Enregistrement: $provider..."
        az provider register --namespace "$provider" --subscription "$SUBSCRIPTION_ID" || true
    done
    
    print_success "Tous les providers ont été enregistrés!"
    print_info "Note: L'enregistrement peut prendre 10-15 minutes"
}

function show_help() {
    cat << EOF
${BLUE}SCRIPT DE RÉPARATION AZURE ML${NC}

Usage: bash $0 <action>

Actions disponibles:

  ${GREEN}login${NC}                    Se reconnecter à Azure
  ${GREEN}verify${NC}                   Vérifier la configuration complète
  ${GREEN}configure-defaults${NC}       Définir les paramètres par défaut
  ${GREEN}register-providers${NC}       Enregistrer les resource providers
  ${GREEN}restart-docker${NC}           Redémarrer le daemon Docker
  ${GREEN}clear-cache${NC}              Vider le cache d'authentification
  ${GREEN}help${NC}                     Afficher cette aide

Exemples:
  bash $0 login
  bash $0 verify
  bash $0 configure-defaults

${YELLOW}Configuration:${NC}
  - Abonnement: $SUBSCRIPTION_ID
  - Groupe de ressources: $RESOURCE_GROUP
  - Workspace: $WORKSPACE_NAME
  - Région: $REGION

EOF
}

# Main
ACTION="${1:-help}"

case "$ACTION" in
    login)
        login_to_azure
        ;;
    verify)
        verify_configuration
        ;;
    configure-defaults)
        configure_defaults
        ;;
    register-providers)
        register_providers
        ;;
    restart-docker)
        restart_docker
        ;;
    clear-cache)
        clear_authentication_cache
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Action inconnue: $ACTION"
        show_help
        exit 1
        ;;
esac

exit 0
