# 🔧 GUIDE DE TROUBLESHOOTING - Azure ML Deployment Failures

## 📋 Table des matières
1. [Diagnostic rapide](#diagnostic-rapide)
2. [Problème A: SubscriptionNotRegistered [N/A]](#problème-a-subscriptionnotregistered-na)
3. [Problème B: Ghost Endpoint](#problème-b-ghost-endpoint)
4. [Alternatives Python (Recommandé)](#alternatives-python-recommandé)
5. [Checklist de Déploiement](#checklist-de-déploiement)
6. [FAQ](#faq)

---

## 🔍 Diagnostic Rapide

### Étape 1: Exécuter le diagnostic complet
```bash
cd telco-churn-mlops/scripts
python 01_diagnostic_azure.py
```

Cet outil vérifie:
- ✅ Azure CLI installée et version
- ✅ Authentification active
- ✅ Abonnement correct
- ✅ Groupe de ressources accessible
- ✅ Workspace Azure ML présent
- ✅ Endpoints existants et leurs états
- ✅ Variables d'environnement
- ✅ SDK Python azure-ai-ml

### Étape 2: Si le diagnostic échoue
```bash
# Réinitialiser la session Azure
bash 04_azure_recovery.sh login

# Vérifier la configuration
bash 04_azure_recovery.sh verify

# Définir les paramètres par défaut
bash 04_azure_recovery.sh configure-defaults
```

---

## ⚠️ Problème A: SubscriptionNotRegistered [N/A]

### ❓ Symptôme
```
Error: Resource provider [N/A] isn't registered with Subscription [N/A].
```

### 🔴 Causes Possibles

| # | Cause | Indicateur | Solution |
|---|-------|-----------|----------|
| 1 | Token d'authentification expiré | CLI demande login à chaque commande | Login + reconnecter |
| 2 | Variables env Azure non définies | `echo $AZURE_SUBSCRIPTION_ID` vide | Définir les variables |
| 3 | Workspace non bien configuré | Diagnostic échoue étape 5 | Reconfigurer workspace |
| 4 | Provider Microsoft.MachineLearningServices non enregistré | Erreur lors de create/update | Enregistrer provider |
| 5 | Connexion réseau/firewall | Timeout sur requêtes | Vérifier réseau |

### ✅ Solutions Pas à Pas

#### **Solution 1A: Réauthentification complète**
```bash
# Étape 1: Vider le cache
bash 04_azure_recovery.sh clear-cache

# Étape 2: Reconnecter
bash 04_azure_recovery.sh login

# Étape 3: Vérifier
bash 04_azure_recovery.sh verify

# Étape 4: Configurer les defaults
bash 04_azure_recovery.sh configure-defaults
```

#### **Solution 1B: Forcer l'abonnement dans chaque commande**
```bash
# Ajouter --subscription à CHAQUE commande CLI
az account set --subscription eb1cf44f-57ae-4310-8998-c0a2a0886a86

# Vérifier que c'est défini
az account show --query id
# Output: eb1cf44f-57ae-4310-8998-c0a2a0886a86
```

#### **Solution 1C: Enregistrer les Resource Providers**
```bash
bash 04_azure_recovery.sh register-providers

# OU manuellement
az provider register --namespace Microsoft.MachineLearningServices --subscription eb1cf44f-57ae-4310-8998-c0a2a0886a86

# Attendre 10-15 minutes pour l'enregistrement
az provider show --namespace Microsoft.MachineLearningServices --query registrationState
# Output: "Registered"
```

#### **Solution 1D: Utiliser le SDK Python (RECOMMANDÉ ⭐)**
```bash
# Évite complètement les problèmes de CLI
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6
```

---

## 🚫 Problème B: Ghost Endpoint

### ❓ Symptôme
Après une tentative de création échouée d'endpoint:
```
az ml online-endpoint create: An endpoint with this name already exists.
az ml online-endpoint update: This endpoint has not been created successfully 
                              or is in deleting provisioning state. Please recreate endpoint.
```

### 🔴 Causes

| État | Cause | Solution |
|------|-------|----------|
| `Failed` | Création échouée (modèle manquant, env invalide, etc.) | Supprimer + recréer |
| `Deleting` | Suppression en cours (depuis suppression antérieure) | Attendre 15-30 min |
| `Updating` | Mise à jour en cours (timeout, erreur) | Attendre ou forcer suppression |
| `Creating` | Création en cours (timeout > 60 min) | Annuler et supprimer |

### ✅ Solutions Pas à Pas

#### **Étape 1: Identifier l'état de l'endpoint**
```bash
# Lister tous les endpoints
python 03_cleanup_endpoints.py --list

# Voir les détails
python 03_cleanup_endpoints.py --details telco-churn-endpoint-v6
```

#### **Étape 2: Supprimer l'endpoint bloqué**

**Option A: Suppression gracieuse (Recommandé)**
```bash
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v6
```

**Option B: Suppression forcée via CLI**
```bash
az ml online-endpoint delete \
  --name telco-churn-endpoint-v6 \
  --resource-group rg-mlops-final \
  --workspace-name churn \
  --subscription eb1cf44f-57ae-4310-8998-c0a2a0886a86 \
  --yes

# Vérifier la suppression
az ml online-endpoint list \
  --resource-group rg-mlops-final \
  --workspace-name churn
```

#### **Étape 3: Attendre avant de recréer**
```bash
# L'endpoint supprimé peut rester "réservé" pendant 15-30 minutes
# Utilisez un nouveau nom si vous ne pouvez pas attendre

# Option A: Attendre 20 minutes, puis recréer avec même nom
sleep 1200
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6

# Option B: Recréer immédiatement avec nouveau nom
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v7
```

#### **Étape 4: OPTION NUCLÉAIRE - Supprimer TOUS les endpoints**
```bash
# ⚠️ ATTENTION: Cela supprimera TOUS les endpoints du workspace
python 03_cleanup_endpoints.py --force-delete-all

# Puis recréer proprement
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6
```

---

## 🐍 Alternatives Python (Recommandé ⭐)

### ❓ Pourquoi utiliser Python plutôt que la CLI?

| Aspect | CLI Azure | SDK Python |
|--------|-----------|-----------|
| **Authentification** | Problèmes fréquents [N/A] | Gestion robuste |
| **Ghost Endpoints** | Difficile à déboguer | Gestion d'erreurs complète |
| **Timeouts** | Pas de retry automatique | Retry + exponential backoff |
| **Sérialisation YAML** | Parsing fragile | Validation complète |
| **Contrôle fin** | Limité | Accès à tous les paramètres |
| **Logs diagnostiques** | Faibles | Très détaillés |

### 📦 Installation

```bash
# Installer les dépendances
pip install azure-ai-ml azure-identity pyyaml

# Vérifier l'installation
python -c "from azure.ai.ml import MLClient; print('✅ OK')"
```

### 🚀 Utilisation

#### **Déploiement complet (Recommandé)**
```bash
python 02_deploy_mlclient.py \
  --endpoint-name telco-churn-endpoint-v6 \
  --region norwayeast
```

Cet outil:
1. ✅ Gère automatiquement l'authentification
2. ✅ Crée l'endpoint s'il n'existe pas
3. ✅ Crée le deployment avec toutes les configs
4. ✅ Définit le deployment par défaut
5. ✅ Active Application Insights
6. ✅ Configure les request settings
7. ✅ Affiche l'URI de scoring final

#### **Nettoyage des endpoints**
```bash
# Lister
python 03_cleanup_endpoints.py --list

# Supprimer un endpoint spécifique
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v6

# Voir les détails
python 03_cleanup_endpoints.py --details telco-churn-endpoint-v6

# Supprimer TOUS (avec confirmation)
python 03_cleanup_endpoints.py --force-delete-all
```

### 💻 Script Python personnalisé

Pour un contrôle encore plus fin, voici un template:

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

# Authentification automatique
credential = DefaultAzureCredential()

# Créer le client
ml_client = MLClient(
    credential=credential,
    subscription_id="eb1cf44f-57ae-4310-8998-c0a2a0886a86",
    resource_group_name="rg-mlops-final",
    workspace_name="churn"
)

# Créer/obtenir un endpoint
from azure.ai.ml.entities import ManagedOnlineEndpoint

endpoint = ManagedOnlineEndpoint(
    name="telco-churn-endpoint-v6",
    auth_mode="key",
    description="Telco Churn Prediction"
)

created_endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
print(f"✅ Endpoint: {created_endpoint.scoring_uri}")
```

---

## ✅ Checklist de Déploiement

### Avant le déploiement
- [ ] Exécuter diagnostic: `python 01_diagnostic_azure.py`
- [ ] Vérifier abonnement correct: `az account show`
- [ ] Vérifier workspace: `az ml workspace show --name churn`
- [ ] Vérifier modèle existe: `az ml model list --workspace-name churn`
- [ ] Vérifier environment existe: `az ml environment list --workspace-name churn`
- [ ] Nettoyer les endpoints bloqués: `python 03_cleanup_endpoints.py --list`

### Pendant le déploiement
- [ ] Utiliser SDK Python (02_deploy_mlclient.py) plutôt que CLI
- [ ] Monitorer les logs en direct
- [ ] Ne pas interrompre le processus (30-60 min normal)

### Après le déploiement
- [ ] Vérifier l'état: `python 03_cleanup_endpoints.py --list`
- [ ] Tester l'endpoint: `az ml online-endpoint invoke --endpoint-name telco-churn-endpoint-v6`
- [ ] Vérifier les logs: `az ml online-deployment get-logs --endpoint-name telco-churn-endpoint-v6 --deployment-name xgboost-deployment`
- [ ] Monitorer Application Insights

---

## ❓ FAQ

### Q1: J'ai attendu 30 min et je peux toujours pas recréer l'endpoint
**R:** Cela peut arriver si le nom est resté bloqué dans l'ARM. Solutions:
1. Essayer un nouveau nom: `telco-churn-endpoint-v7`
2. Contacter le support Azure ML
3. Utiliser une compute instance différente

### Q2: Le déploiement démarre mais ne finit jamais
**R:** Cela peut être dû à:
1. Instance type incorrect (Standard_DS2_v2 minimum recommandé)
2. Timeout réseau (vérifier les security groups)
3. Modèle trop volumineux (vérifier taille modèle)
4. Env conda corrompu (recréer l'environment)

**Solution:** Arrêter le déploiement et recréer:
```bash
python 03_cleanup_endpoints.py --delete telco-churn-endpoint-v6
# Attendre 5 min
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v7
```

### Q3: Comment puis-je voir les logs du déploiement?
**R:** Utilisez Azure CLI:
```bash
# Logs du deployment
az ml online-deployment get-logs \
  --endpoint-name telco-churn-endpoint-v6 \
  --deployment-name xgboost-deployment \
  --tail 50

# Logs du conteneur
az ml online-deployment get-logs \
  --endpoint-name telco-churn-endpoint-v6 \
  --deployment-name xgboost-deployment \
  --container inference_server \
  --tail 100
```

### Q4: Comment forcer une mise à jour du modèle?
**R:** Créer un nouveau deployment:
```bash
# Mettre à jour le deployment.yml avec nouveau model@version
# Puis déployer
python 02_deploy_mlclient.py --skip-endpoint --endpoint-name telco-churn-endpoint-v6
```

### Q5: Puis-je utiliser le même endpoint pour plusieurs modèles (A/B testing)?
**R:** Oui! Créer plusieurs deployments et splitter le trafic:
```python
from azure.ai.ml import MLClient

ml_client = MLClient(...)
endpoint = ml_client.online_endpoints.get("telco-churn-endpoint-v6")

# 70% -> xgboost-deployment, 30% -> random-forest-deployment
endpoint.traffic = {
    "xgboost-deployment": 70,
    "random-forest-deployment": 30
}

ml_client.online_endpoints.begin_create_or_update(endpoint).result()
```

---

## 📞 Support & Escalade

Si aucune solution ne fonctionne:

1. **Ouvrir un ticket Azure Support**
   - Inclure les logs de diagnostic
   - Inclure subscription ID et workspace name
   - Inclure les error messages exacts

2. **Forums Azure ML**
   - https://github.com/Azure/MachineLearningNotebooks/issues
   - https://github.com/Azure/azureml-sdk-for-python/issues

3. **Logs détaillés pour le support**
   ```bash
   python 01_diagnostic_azure.py > diagnostic_$(date +%s).log 2>&1
   az ml online-endpoint list --output json > endpoints_$(date +%s).json
   ```

---

**Mise à jour:** 2024-01-XX | **Auteur:** ML DevOps Team
