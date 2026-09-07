# 📚 INDEX - Documentation Azure ML Deployment

## 🎯 COMMENCER ICI

### 📋 Document Exécutif (Réponses directes aux 3 questions)
👉 **[SOLUTION_EXECUTIVE_SUMMARY.md](SOLUTION_EXECUTIVE_SUMMARY.md)** ⭐

**Contient:**
1. ✅ Pourquoi l'extension `az ml` perd le jeton ([N/A])
2. ✅ Comment forcer la suppression d'un endpoint bloqué
3. ✅ Alternative via SDK Python (MLClient)

---

## 🚀 DÉPLOIEMENT RAPIDE

### Quick Start (5 min)
```bash
cd telco-churn-mlops/scripts

# 1. Diagnostic
python 01_diagnostic_azure.py

# 2. Nettoyer (si nécessaire)
python 03_cleanup_endpoints.py --list

# 3. Déployer
python 02_deploy_mlclient.py --endpoint-name telco-churn-endpoint-v6
```

### Documentation des Scripts
👉 **[scripts/README.md](../scripts/README.md)**

**Contient:**
- 📖 Guide de chaque script
- 🔧 Workflow complet
- ⚠️ Pièges communs
- 🆘 Troubleshooting

---

## 🔧 TROUBLESHOOTING

### Guide Complet
👉 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** 

**Couvre:**
- 🔍 Diagnostic rapide
- ⚠️ Problème A: SubscriptionNotRegistered [N/A]
- 🚫 Problème B: Ghost Endpoint
- 🐍 Alternatives Python
- ✅ Checklist de déploiement
- ❓ FAQ

---

## 📦 FICHIERS DE CONFIGURATION

### Endpoint Configuration
- **[../azureml/endpoint.yml](../azureml/endpoint.yml)** - Managed Online Endpoint
- **[../azureml/deployment.yml](../azureml/deployment.yml)** - Deployment config

### Python Dependencies
- **[../scripts/requirements.txt](../scripts/requirements.txt)** - Packages requis

---

## 🛠️ SCRIPTS DISPONIBLES

### 4 Scripts principaux:

| Script | Utilité | Exécuter |
|--------|---------|----------|
| **01_diagnostic_azure.py** | ✅ Diagnostic complet | `python scripts/01_diagnostic_azure.py` |
| **02_deploy_mlclient.py** | 🚀 Déploiement via SDK Python | `python scripts/02_deploy_mlclient.py` |
| **03_cleanup_endpoints.py** | 🧹 Gérer endpoints bloqués | `python scripts/03_cleanup_endpoints.py --list` |
| **04_azure_recovery.sh** | 🔄 Réparation/configuration | `bash scripts/04_azure_recovery.sh help` |

---

## 🔀 Navigateur par Cas d'Usage

### Je rencontre l'erreur "SubscriptionNotRegistered [N/A]"
1. Lire: [SOLUTION_EXECUTIVE_SUMMARY.md#1️⃣](SOLUTION_EXECUTIVE_SUMMARY.md) (Partie 1)
2. Exécuter: `bash scripts/04_azure_recovery.sh login`
3. Puis: `python scripts/02_deploy_mlclient.py`

### J'ai un endpoint bloqué ("Ghost Endpoint")
1. Lire: [SOLUTION_EXECUTIVE_SUMMARY.md#2️⃣](SOLUTION_EXECUTIVE_SUMMARY.md) (Partie 2)
2. Exécuter: `python scripts/03_cleanup_endpoints.py --list`
3. Supprimer: `python scripts/03_cleanup_endpoints.py --delete <nom>`
4. Attendre 15-30 min, puis redéployer

### Je veux utiliser le SDK Python au lieu de CLI
1. Lire: [SOLUTION_EXECUTIVE_SUMMARY.md#3️⃣](SOLUTION_EXECUTIVE_SUMMARY.md) (Partie 3)
2. Installer: `pip install -r scripts/requirements.txt`
3. Exécuter: `python scripts/02_deploy_mlclient.py`

### Problème lors du déploiement
1. Lire: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Utiliser: `python scripts/01_diagnostic_azure.py`
3. Appliquer la solution correspondante

### Mon workspace n'est pas correctement configuré
1. Lire: [scripts/README.md#configuration](../scripts/README.md)
2. Exécuter: `bash scripts/04_azure_recovery.sh verify`
3. Configurer: `bash scripts/04_azure_recovery.sh configure-defaults`

---

## 📊 Vue d'ensemble des Solutions

### Solution 1: Diagnostic Azure
- **Fichier:** `scripts/01_diagnostic_azure.py`
- **Utile pour:** Vérifier que tout est configuré
- **Prérequis:** Azure CLI + authentification
- **Temps:** 2-5 min
- **Output:** Rapport détaillé + alertes

### Solution 2: Déploiement Python (⭐ RECOMMANDÉ)
- **Fichier:** `scripts/02_deploy_mlclient.py`
- **Utile pour:** Créer l'endpoint et le deployment
- **Prérequis:** Python + SDK azure-ai-ml
- **Temps:** 30-60 min (incluant provisioning)
- **Output:** Endpoint operationnel + URI de scoring

### Solution 3: Nettoyage des Endpoints
- **Fichier:** `scripts/03_cleanup_endpoints.py`
- **Utile pour:** Débloquer les ghost endpoints
- **Prérequis:** Python + SDK azure-ai-ml
- **Temps:** 1-30 min (selon état)
- **Output:** Endpoints supprimés + noms libérés

### Solution 4: Réparation Azure
- **Fichier:** `scripts/04_azure_recovery.sh`
- **Utile pour:** Réparer authentification/configuration
- **Prérequis:** Bash + Azure CLI
- **Temps:** 2-10 min
- **Output:** Configuration Azure réparée

---

## 🔐 Configuration requise

### Credentials Azure
```bash
# Abonnement
SUBSCRIPTION_ID="eb1cf44f-57ae-4310-8998-c0a2a0886a86"

# Ressources
RESOURCE_GROUP="rg-mlops-final"
WORKSPACE_NAME="churn"
REGION="norwayeast"

# Authentification
az login  # Interactive browser flow
```

### Dépendances Python
```bash
pip install -r scripts/requirements.txt
# Minimum: azure-ai-ml >= 1.8.0, azure-identity >= 1.11.0
```

### Dépendances Azure CLI
```bash
az --version  # Minimum: 2.40.0
az extension add --name ml  # Extension machine-learning-services
```

---

## 📈 Workflow recommandé

```
┌─────────────────────────────────────────────────────────┐
│  DÉMARRAGE                                              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  1. DIAGNOSTIC                                          │
│  → python scripts/01_diagnostic_azure.py               │
│  → Vérifier: Authentification ✅, Workspace ✅, Région ✅
└─────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        │ Problèmes détectés?                 │
    ✅ NON                              ⚠️ OUI
        │                                    │
        ↓                                    ↓
    CONTINUER            ┌──────────────────────────────┐
        │                │ Exécuter récupération:       │
        │                │ bash 04_azure_recovery.sh ..│
        │                └──────────────────────────────┘
        │                           ↓
        │                    Puis recommencer (1)
        │
        ↓
┌─────────────────────────────────────────────────────────┐
│  2. NETTOYAGE (OPTIONNEL)                              │
│  → python scripts/03_cleanup_endpoints.py --list       │
│  → Supprimer les endpoints v1-v5: --delete <nom>       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  3. DÉPLOIEMENT (PRINCIPAL)                            │
│  → python scripts/02_deploy_mlclient.py                │
│  → Attendre: Endpoint ✅, Deployment ✅                 │
│  → Durée: 30-60 min                                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  4. VÉRIFICATION                                        │
│  → python scripts/03_cleanup_endpoints.py --details    │
│  → État: Succeeded ✅                                   │
│  → URI: https://...inference.ml.azure.com/score        │
└─────────────────────────────────────────────────────────┘
                           ↓
                      ✅ SUCCÈS!
```

---

## 🎓 Ressources supplémentaires

### Microsoft Learn
- [Azure Machine Learning Overview](https://learn.microsoft.com/azure/machine-learning/)
- [Managed Online Endpoints](https://learn.microsoft.com/azure/machine-learning/concept-endpoints-online)
- [Azure ML SDK Python](https://learn.microsoft.com/python/api/azure-ai-ml/)

### GitHub
- [Azure ML Notebooks](https://github.com/Azure/MachineLearningNotebooks)
- [Azure ML SDK Issues](https://github.com/Azure/azureml-sdk-for-python/issues)

### Documentation locale
- [SOLUTION_EXECUTIVE_SUMMARY.md](SOLUTION_EXECUTIVE_SUMMARY.md) - Réponses détaillées
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Guide complet
- [../scripts/README.md](../scripts/README.md) - Documentation scripts

---

## 📞 Support

### Si aucune solution ne fonctionne:
1. Exécuter: `python scripts/01_diagnostic_azure.py > diag.log`
2. Inclure le fichier `diag.log` dans le ticket
3. Inclure aussi: Subscription ID, Workspace name, Error messages exacts

### Canaux de support:
- 📧 Support Azure ML
- 🐛 GitHub Issues: https://github.com/Azure/azureml-sdk-for-python/issues
- 💬 Microsoft Learn Forums

---

**Mise à jour:** 2026-08-12  
**Version:** 1.0  
**Auteur:** Azure ML DevOps Team
