import mlflow
import mlflow.sklearn
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np

from sklearn.model_selection import GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


def get_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """Crée le ColumnTransformer (RobustScaler pour le numérique, OneHotEncoder pour le catégoriel)."""
    num_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', RobustScaler(), num_cols),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )
    return preprocessor


def evaluate_with_threshold(model, X_test, y_test, threshold: float = 0.55, model_name: str = "Modèle"):
    """Évalue le modèle avec un seuil de décision personnalisé."""
    # Obtenir les probabilités pour la classe positive (1)
    y_probs = model.predict_proba(X_test)[:, 1]

    # Application du seuil ajusté
    y_pred_adj = (y_probs >= threshold).astype(int)

    print(f"\n================ {model_name.upper()} OPTIMISÉ (Seuil {threshold}) ================")
    print(f"ROC AUC Score: {roc_auc_score(y_test, y_probs):.4f}")
    print("\n--- Rapport de Classification ---")
    print(classification_report(y_test, y_pred_adj))
    print("--- Matrice de Confusion ---")
    print(confusion_matrix(y_test, y_pred_adj))


def main():
    mlflow.set_experiment("telco-churn-training")
    # --- 1. CHARGEMENT DES DONNÉES PRÉPARÉES ---
    print("Chargement des données d'entraînement et de test depuis data/processed/...")
    train_df = pd.read_csv("data/processed/train.csv")
    test_df = pd.read_csv("data/processed/test.csv")

    # --- 2. SEPARATION FEATURES / TARGET ---
    X_train = train_df.drop('Churn', axis=1)
    y_train = train_df['Churn']
    
    X_test = test_df.drop('Churn', axis=1)
    y_test = test_df['Churn']

    print(f"Dimensions Train : X={X_train.shape}, y={y_train.shape}")
    print(f"Dimensions Test  : X={X_test.shape}, y={y_test.shape}")

    # --- 3. PRÉTRAITEMENT ---
    preprocessor = get_preprocessor(X_train)

    # --- 4. RANDOM FOREST OPTIMISÉ ---
    print("\n[1/2] Entraînement et validation de Random Forest...")
    rf_pipeline = ImbPipeline([
        ('preprocessor', preprocessor),
        ('smote', SMOTE(random_state=42)),
        ('classifier', RandomForestClassifier(random_state=42))
    ])

    param_grid_rf = {
        'classifier__n_estimators': [200],
        'classifier__max_depth': [10],
        'classifier__min_samples_split': [10]
    }

    grid_rf = GridSearchCV(rf_pipeline, param_grid_rf, cv=5, scoring='f1', n_jobs=-1)
    grid_rf.fit(X_train, y_train)

    print(f"Meilleurs paramètres RF : {grid_rf.best_params_}")
    evaluate_with_threshold(
        grid_rf.best_estimator_, X_test, y_test, threshold=0.55, model_name="Random Forest"
    )

    # --- 5. XGBOOST OPTIMISÉ AVEC TRACKING MLFLOW ---
    print("\n[2/2] Entraînement et validation d'XGBoost avec MLflow...")
    
    # On démarre l'enregistrement MLflow
    with mlflow.start_run(run_name="XGBoost_GridSearch"):
        
        xgb_pipeline = ImbPipeline([
            ('preprocessor', preprocessor),
            ('smote', SMOTE(random_state=42)),
            ('classifier', XGBClassifier(random_state=42, eval_metric='logloss'))
        ])

        param_grid_xgb = {
            'classifier__n_estimators': [100],
            'classifier__max_depth': [4],
            'classifier__learning_rate': [0.1]
        }

        grid_xgb = GridSearchCV(xgb_pipeline, param_grid_xgb, cv=5, scoring='f1', n_jobs=-1)
        grid_xgb.fit(X_train, y_train)

        print(f"Meilleurs paramètres XGB : {grid_xgb.best_params_}")
        evaluate_with_threshold(
            grid_xgb.best_estimator_, X_test, y_test, threshold=0.55, model_name="XGBoost"
        )
        
        # 👉 SAUVEGARDE ET TRACKING DANS AZURE ML
        # 1. Enregistrer les meilleurs hyperparamètres
        mlflow.log_params(grid_xgb.best_params_)
        
        # 2. Enregistrer la métrique de validation
        mlflow.log_metric("best_cv_f1_score", grid_xgb.best_score_)
        
        # ... (ton code précédent)
        # 3. Sauvegarder le pipeline complet
        mlflow.sklearn.log_model(grid_xgb.best_estimator_, "best_xgb_model")
        print("✅ Modèle XGBoost sauvegardé avec succès dans MLflow !")
        
        # 👉 NOUVEAU : ENREGISTREMENT DANS LE MODEL REGISTRY
        run = mlflow.active_run()
        model_uri = f"runs:/{run.info.run_id}/best_xgb_model"
        mlflow.register_model(model_uri=model_uri, name="Telco_Churn_XGBoost")
        print("✅ Modèle inscrit dans le Model Registry d'Azure ML !")


if __name__ == "__main__":
    main()