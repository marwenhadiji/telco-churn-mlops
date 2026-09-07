import json
import logging
import os
import sys

import mlflow.sklearn
import pandas as pd
from opencensus.ext.azure.log_exporter import AzureLogHandler

# --- Configuration du logging ---
# 1) On garde stdout : utile pour le debug local et les logs de conteneur Azure ML
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Forcé explicitement : basicConfig() est un no-op
                                 # ici car azmlinfsrv a déjà configuré le root logger.
if not logger.handlers:
    _stream_handler = logging.StreamHandler(sys.stdout)
    _stream_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(_stream_handler)

# 2) On ajoute le handler Azure Application Insights (traces réelles dans App Insights)
# Azure ML injecte automatiquement AML_APP_INSIGHTS_KEY quand app_insights_enabled=True,
# mais opencensus attend une "connection string", donc on la reconstruit ici.
instrumentation_key = os.environ.get("AML_APP_INSIGHTS_KEY")
if instrumentation_key:
    conn_str = f"InstrumentationKey={instrumentation_key}"
    logger.addHandler(AzureLogHandler(connection_string=conn_str))
    logger.info("AzureLogHandler configuré avec succès (App Insights actif).")
else:
    logger.warning("AML_APP_INSIGHTS_KEY introuvable : les logs ne partiront pas vers App Insights.")


def init():
    """Initialisation : Chargement du modèle au démarrage de l'API."""
    global model
    # Azure ML définit automatiquement la variable AZUREML_MODEL_DIR
    model_dir = os.getenv("AZUREML_MODEL_DIR")

    # MLflow sauvegarde les artéfacts sous le sous-dossier 'best_xgb_model'
    model_path = os.path.join(model_dir, "best_xgb_model")

    logger.info(f"Chargement du modèle depuis : {model_path}")
    model = mlflow.sklearn.load_model(model_path)
    logger.info("Modèle chargé avec succès !")


def run(raw_data):
    """Traitement de chaque requête entrante."""
    try:
        # Conversion du JSON reçu en DataFrame pandas
        data = json.loads(raw_data)["data"]
        df = pd.DataFrame(data)

        # Prédictions (classe 0 ou 1 + probabilité de Churn)
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)[:, 1]

        # Enregistrement des probabilités pour suivre les performances dans App Insights
        logger.info(f"PREDICTION_LOG: churn_probabilities={probabilities.tolist()}")

        # Formatage de la réponse HTTP
        return {
            "status": "success",
            "predictions": predictions.tolist(),
            "churn_probabilities": probabilities.tolist(),
        }

    except Exception as e:
        logger.error(f"Erreur lors de la prédiction : {str(e)}")
        return {"status": "error", "message": str(e)}