import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from train import get_preprocessor, evaluate_with_threshold


def make_synthetic_frame(n=40):
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "tenure": rng.integers(0, 72, n),
        "MonthlyCharges": rng.uniform(20, 120, n),
        "gender": rng.choice(["Male", "Female"], n),
        "Contract": rng.choice(["Month-to-month", "One year", "Two year"], n),
    })
    y = pd.Series(rng.integers(0, 2, n), name="Churn")
    return df, y


def test_get_preprocessor_transforms_mixed_types():
    X, _ = make_synthetic_frame()
    preprocessor = get_preprocessor(X)
    X_transformed = preprocessor.fit_transform(X)

    assert X_transformed.shape[0] == X.shape[0]
    assert not np.isnan(X_transformed).any()


def test_evaluate_with_threshold_runs_without_error(capsys):
    X, y = make_synthetic_frame()
    preprocessor = get_preprocessor(X)
    X_transformed = preprocessor.fit_transform(X)

    clf = LogisticRegression(max_iter=200)
    clf.fit(X_transformed, y)

    class WrappedModel:
        """Simule un pipeline complet (preprocessing + classifieur)."""
        def predict_proba(self, X_raw):
            return clf.predict_proba(preprocessor.transform(X_raw))

    evaluate_with_threshold(WrappedModel(), X, y, threshold=0.5, model_name="Test")

    captured = capsys.readouterr()
    assert "ROC AUC Score" in captured.out
