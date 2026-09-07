import json
import logging
import os
import mlflow.sklearn
import pandas as pd


def init():
    """Initialisation : Chargement du modèle au démarrage de l'API."""
    global model
    # Azure ML définit automatiquement la variable AZUREML_MODEL_DIR
    model_dir = os.getenv("AZUREML_MODEL_DIR")

    # MLflow sauvegarde les artéfacts sous le sous-dossier 'best_xgb_model'
    model_path = os.path.join(model_dir, "best_xgb_model")

    logging.info(f"Chargement du modèle depuis : {model_path}")
    model = mlflow.sklearn.load_model(model_path)
    logging.info("Modèle chargé avec succès !")


def run(raw_data):
    """Traitement de chaque requête entrante."""
    try:
        # Conversion du JSON reçu en DataFrame pandas
        data = json.loads(raw_data)["data"]
        df = pd.DataFrame(data)

        # Prédictions (classe 0 ou 1 + probabilité de Churn)
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)[:, 1]

        # Formatage de la réponse HTTP
        return {
            "status": "success",
            "predictions": predictions.tolist(),
            "churn_probabilities": probabilities.tolist(),
        }

    except Exception as e:
        logging.error(f"Erreur lors de la prédiction : {str(e)}")
        return {"status": "error", "message": str(e)}