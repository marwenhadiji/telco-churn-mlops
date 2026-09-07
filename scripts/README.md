# Scripts de Deployment et Troubleshooting - Azure ML

## 📋 Vue d'ensemble

Ce dossier contient 4 scripts essentiels pour diagnostiquer et déployer le Managed Online Endpoint pour Telco Churn:

| Script | Utilité | Status |
|--------|---------|--------|
| `01_diagnostic_azure.py` | Diagnostic complet de l'authentification, abonnement, workspace | 🔧 Diagnostic |
| `02_deploy_mlclient.py` | Déploiement principal via SDK Python (contourne problèmes CLI) | 🚀 Déploiement |
| `03_cleanup_endpoints.py` | Gestion des endpoints bloqués ("Ghost Endpoints") | 🧹 Nettoyage |
| `04_azure_recovery.sh` | Script bash de réparation et configuration Azure | 🔄 Récupération |

---

## 🚀 Quick Start

### 1️⃣ Premier diagnostic
```bash
python 01_diagnostic_azure.py
```

### 2️⃣ Nettoyer les endpoints existants (si nécessaire)
```bash
python 03_cleanup_endpoints.py --list
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v5
```

### 3️⃣ Déployer l'endpoint
```bash
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6
```

### 4️⃣ Vérifier le déploiement
```bash
python 03_cleanup_endpoints.py --details telco-churn-endpoint-v6
```

---

## 📦 Dépendances

### Installation
```bash
# Via pip
pip install -r requirements.txt

# OU manuellement
pip install azure-ai-ml azure-identity pyyaml pandas numpy scikit-learn

# Pour déploiement MLflow
pip install azureml-mlflow
```

### Versions minimales
- Python 3.8+
- azure-ai-ml >= 1.8.0
- azure-identity >= 1.11.0

---

## 🔐 Configuration Azure requise

Avant d'utiliser les scripts, vérifiez:

```bash
# 1. Abonnement Azure for Students
export SUBSCRIPTION_ID="eb1cf44f-57ae-4310-8998-c0a2a0886a86"
export RESOURCE_GROUP="rg-mlops-final"
export WORKSPACE_NAME="churn"
export REGION="norwayeast"

# 2. Authentification
az login

# 3. Définir l'abonnement par défaut
az account set --subscription $SUBSCRIPTION_ID

# 4. Vérifier
az ml workspace show --name $WORKSPACE_NAME --resource-group $RESOURCE_GROUP
```

---

## 📖 Documentation détaillée de chaque script

### 1️⃣ `01_diagnostic_azure.py`

**Objectif:** Vérifier que tout est correctement configuré avant déploiement.

**Vérifie:**
- ✅ Azure CLI installée et version
- ✅ Authentification active (utilisateur + token)
- ✅ Abonnement correct
- ✅ Groupe de ressources accessible
- ✅ Workspace Azure ML présent et accessible
- ✅ Endpoints existants et leurs états
- ✅ Variables d'environnement Azure (AZURE_SUBSCRIPTION_ID, etc.)
- ✅ SDK Python azure-ai-ml installé

**Utilisation:**
```bash
# Diagnostic complet
python 01_diagnostic_azure.py

# Outputs:
# - Résumé de l'authentification
# - État du workspace
# - Liste des endpoints existants
# - Alertes si des configurations manquent
```

**Exemple de résultat:**
```
════════════════════════════════════════════════════════
  2. VÉRIFICATION AUTHENTIFICATION
════════════════════════════════════════════════════════

✅ Utilisateur connecté:
   ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Nom: user@example.com
   Type: user
```

**Dépannage:**
- Si authentification échoue → `bash 04_azure_recovery.sh login`
- Si workspace introuvable → Vérifier subscription/resource group
- Si endpoints affichent "Failed" → Utiliser `03_cleanup_endpoints.py` pour supprimer

---

### 2️⃣ `02_deploy_mlclient.py` ⭐ **À UTILISER PAR DÉFAUT**

**Objectif:** Déployer le Managed Online Endpoint + Deployment via SDK Python (évite problèmes CLI).

**Avantages vs CLI:**
- ✅ Gestion robuste de l'authentification
- ✅ Retry automatique sur erreurs transitoires
- ✅ Meilleure gestion des timeouts
- ✅ Logs détaillés pour debugging
- ✅ Validation complète des configurations

**Utilisation:**
```bash
# Déploiement simple (endpoint + deployment)
python 02_deploy_mlclient.py

# Avec options personnalisées
python 02_deploy_mlclient.py \
  --endpoint-name telco-churn-endpoint-v7 \
  --region norwayeast

# Sauter création endpoint (mise à jour uniquement)
python 02_deploy_mlclient.py --skip-endpoint
```

**Étapes effectuées:**
1. Authentification via DefaultAzureCredential
2. Vérification si endpoint existe déjà
3. Création de l'endpoint (si nécessaire)
4. Chargement de la configuration deployment (YAML)
5. Création du deployment
6. Définition du deployment par défaut
7. Activation Application Insights

**Output:**
```
════════════════════════════════════════════════════════
CRÉATION DE L'ENDPOINT: telco-churn-endpoint-v6
════════════════════════════════════════════════════════
✅ MLClient créé pour:
   - Subscription: eb1cf44f-57ae-4310-8998-c0a2a0886a86
   - Resource Group: rg-mlops-final
   - Workspace: churn

✅ Endpoint créé avec succès!
   Nom: telco-churn-endpoint-v6
   URI: https://telco-churn-endpoint-v6.norwayeast.inference.ml.azure.com/score
   État: Succeeded

✅ Deployment créé/mis à jour avec succès!
   Nom: xgboost-deployment
   État: Succeeded

✅ DÉPLOIEMENT RÉUSSI!
```

**Dépannage:**
- "Endpoint already exists" + "Failed state" → Utiliser `03_cleanup_endpoints.py --delete`
- Timeout pendant creation → Attendre 5 min et réessayer
- "Model not found" → Vérifier que le modèle est dans le Model Registry

---

### 3️⃣ `03_cleanup_endpoints.py`

**Objectif:** Gérer les endpoints bloqués ("Ghost Endpoints") en état Failed/Deleting.

**Fonctionnalités:**
- ✅ Lister tous les endpoints avec leurs états
- ✅ Afficher les détails complets d'un endpoint
- ✅ Supprimer un endpoint spécifique
- ✅ Supprimer TOUS les endpoints (avec confirmation)
- ✅ Lister les deployments associés

**Utilisation:**

```bash
# Lister tous les endpoints
python 03_cleanup_endpoints.py --list

# Afficher les détails
python 03_cleanup_endpoints.py --details telco-churn-endpoint-v6

# Supprimer un endpoint
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v5

# Supprimer TOUS les endpoints (demande confirmation!)
python 03_cleanup_endpoints.py --force-delete-all
```

**States d'endpoint et signification:**

| État | Signification | Action |
|------|---------------|--------|
| ✅ **Succeeded** | Endpoint opérationnel | Peut déployer/mettre à jour |
| ⏳ **Creating** | Création en cours | Attendre ou annuler |
| ⏳ **Updating** | Mise à jour en cours | Attendre |
| ❌ **Failed** | Création/mise à jour échouée | Supprimer et recréer |
| ⏳ **Deleting** | Suppression en cours | Attendre 15-30 min |

**Workflow typique pour un Ghost Endpoint:**

```bash
# 1. Vérifier son état
python 03_cleanup_endpoints.py --list
# Output: telco-churn-endpoint-v5 (Failed) ❌

# 2. Afficher les détails
python 03_cleanup_endpoints.py --details telco-churn-endpoint-v5
# Output: État: Failed, Raison: Model not found

# 3. Supprimer
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v5
# Output: ✅ Endpoint supprimé avec succès!

# 4. Attendre 15-30 min (réservation ARM)

# 5. Recréer avec même nom
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v5
```

---

### 4️⃣ `04_azure_recovery.sh`

**Objectif:** Script bash pour réparer des problèmes courants d'authentification Azure.

**Actions disponibles:**

```bash
# 1. Reconnecter à Azure
bash 04_azure_recovery.sh login
# Lance az login --use-device-code

# 2. Vérifier configuration complète
bash 04_azure_recovery.sh verify
# Vérifie: CLI, auth, subscription, resource group, workspace

# 3. Définir les paramètres par défaut
bash 04_azure_recovery.sh configure-defaults
# Configure: subscription, resource group, workspace

# 4. Enregistrer les Resource Providers Azure
bash 04_azure_recovery.sh register-providers
# Enregistre: MachineLearningServices, Compute, Storage, etc.

# 5. Vider le cache d'authentification
bash 04_azure_recovery.sh clear-cache
# Supprime ~/.azure et déconnecte

# 6. Redémarrer Docker (Linux/macOS)
bash 04_azure_recovery.sh restart-docker

# 7. Aide
bash 04_azure_recovery.sh help
```

**Quand utiliser:**

| Symptôme | Action |
|----------|--------|
| "Not authenticated" | `bash 04_azure_recovery.sh login` |
| "[N/A]" dans erreur | `bash 04_azure_recovery.sh clear-cache` puis `login` |
| "Subscription not found" | `bash 04_azure_recovery.sh configure-defaults` |
| Erreur "provider not registered" | `bash 04_azure_recovery.sh register-providers` |
| Tout est cassé | `bash 04_azure_recovery.sh verify` |

---

## 🔄 Workflow complet: De l'installation au déploiement

```bash
# ========== ÉTAPE 1: Configuration initiale ==========
cd telco-churn-mlops/scripts

# Installer les dépendances
pip install -r requirements.txt

# Vérifier la configuration Azure
bash 04_azure_recovery.sh verify

# ========== ÉTAPE 2: Diagnostic ==========
python 01_diagnostic_azure.py

# Si des problèmes: exécuter la récupération appropriée
bash 04_azure_recovery.sh configure-defaults

# ========== ÉTAPE 3: Nettoyage (si nécessaire) ==========
# Lister les endpoints existants
python 03_cleanup_endpoints.py --list

# Supprimer les endpoints bloqués
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v5

# ========== ÉTAPE 4: Déploiement ==========
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6

# ========== ÉTAPE 5: Vérification ==========
python 03_cleanup_endpoints.py --details telco-churn-endpoint-v6

# ========== ÉTAPE 6: Test ==========
az ml online-endpoint invoke \
  --endpoint-name telco-churn-endpoint-v6 \
  --request-file ../tests/request.json
```

---

## 📊 Monitoring après déploiement

```bash
# Voir les logs du deployment
az ml online-deployment get-logs \
  --endpoint-name telco-churn-endpoint-v6 \
  --deployment-name xgboost-deployment \
  --tail 50

# Voir les metrics (Application Insights)
az monitor metrics list \
  --resource-group rg-mlops-final \
  --resource-type Microsoft.MachineLearningServices/workspaces/onlineEndpoints \
  --resource-namespace Microsoft.MachineLearningServices \
  --name telco-churn-endpoint-v6

# Tester en continu
while true; do
  az ml online-endpoint invoke \
    --endpoint-name telco-churn-endpoint-v6 \
    --request-file ../tests/request.json
  sleep 5
done
```

---

## ⚠️ Pièges communs

| Piège | Symptôme | Éviter |
|------|----------|--------|
| Endpoint "zombie" | "Already exists" + "Cannot create" | Utiliser `03_cleanup_endpoints.py` |
| Token expiré | "[N/A]" dans erreur | `bash 04_azure_recovery.sh login` |
| Pas de provider | "Provider not registered" | `bash 04_azure_recovery.sh register-providers` |
| Mauvais workspace | "Workspace not found" | Vérifier subscription + resource group |
| Modèle manquant | "Model not found" | Vérifier Model Registry Azure ML |
| Timeout réseau | Deployment "hangs" | Vérifier security groups + NSG rules |

---

## 🆘 Obtenir de l'aide

### Si les scripts échouent

1. **Vérifier les logs détaillés:**
   ```bash
   python 02_deploy_mlclient.py 2>&1 | tee deployment.log
   ```

2. **Exécuter le diagnostic complet:**
   ```bash
   python 01_diagnostic_azure.py > diagnostic.log 2>&1
   ```

3. **Consulter le guide de troubleshooting:**
   - Voir [../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

4. **Contacter le support:**
   - Inclure les fichiers `.log` générés
   - Inclure l'output de `az account show`
   - Inclure le workspace name et subscription ID

---

**Dernière mise à jour:** 2026-08-12  
**Auteur:** ML DevOps Team
