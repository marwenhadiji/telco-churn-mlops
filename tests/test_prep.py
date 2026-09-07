import pandas as pd
from prep import prepare_data


def make_fixture_csv(path):
    """Crée un mini CSV avec les mêmes problèmes que les vraies données Telco :
    un TotalCharges vide, un doublon, et des classes Churn équilibrées."""
    rows = []
    for i in range(5):
        rows.append({"customerID": f"000{i}-YES", "gender": "Female",
                     "TotalCharges": f"{100 + i}.5", "Churn": "Yes"})
    for i in range(5):
        rows.append({"customerID": f"000{i}-NO", "gender": "Male",
                     "TotalCharges": f"{200 + i}.0", "Churn": "No"})
    # Une ligne avec TotalCharges vide (espace), à nettoyer
    rows.append({"customerID": "BAD-ROW", "gender": "Female",
                 "TotalCharges": " ", "Churn": "Yes"})
    # Un doublon volontaire de la première ligne
    rows.append(rows[0].copy())

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


def test_prepare_data_cleans_and_splits(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    output_dir = tmp_path / "processed"
    make_fixture_csv(raw_csv)

    prepare_data(raw_path=str(raw_csv), output_dir=str(output_dir))

    train_path = output_dir / "train.csv"
    test_path = output_dir / "test.csv"
    assert train_path.exists()
    assert test_path.exists()

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    full_df = pd.concat([train_df, test_df])

    # customerID doit avoir été supprimé
    assert "customerID" not in full_df.columns

    # Churn doit être encodé en 0/1, pas "Yes"/"No"
    assert set(full_df["Churn"].unique()).issubset({0, 1})

    # La ligne avec TotalCharges vide et le doublon doivent avoir disparu
    # (12 lignes brutes -> au plus 10 lignes propres)
    assert full_df.shape[0] <= 10

    # Plus aucun doublon
    assert full_df.duplicated().sum() == 0
