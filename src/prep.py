import os
import pandas as pd
from sklearn.model_selection import train_test_split

def prepare_data(raw_path="data/WA_Fn-UseC_-Telco-Customer-Churn.csv",
                  output_dir="data/processed"):
    print("🔄 Chargement des données...")

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Le fichier {raw_path} n'a pas été trouvé !")

    df = pd.read_csv(raw_path)

    print("🧹 Nettoyage des données...")
    # 1. Traitement des espaces et conversion de TotalCharges
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].str.strip(), errors='coerce')
    df = df.dropna(subset=['TotalCharges'])

    # 2. Suppression des doublons et de la colonne inutile customerID
    df = df.drop_duplicates()
    if 'customerID' in df.columns:
        df = df.drop(columns=['customerID'])

    # 3. Encodage de la variable cible (Churn: Yes/No -> 1/0)
    df['Churn'] = df['Churn'].map({'Yes': 1, 'No': 0})

    print("✂️ Séparation Train / Test...")
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['Churn'])

    # Sauvegarde des fichiers préparés
    os.makedirs(output_dir, exist_ok=True)
    train_df.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    test_df.to_csv(os.path.join(output_dir, "test.csv"), index=False)

    print(f"✅ Préparation terminée ! Train: {train_df.shape}, Test: {test_df.shape}")
    return train_df, test_df

if __name__ == "__main__":
    prepare_data()