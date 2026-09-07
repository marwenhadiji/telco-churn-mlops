import json
import numpy as np
import score


class FakeModel:
    """Simule un modèle MLflow chargé, sans dépendre d'Azure ML."""
    def predict(self, df):
        return np.array([1] * len(df))

    def predict_proba(self, df):
        return np.array([[0.3, 0.7]] * len(df))


def test_run_returns_success_for_valid_payload():
    score.model = FakeModel()  # court-circuite init(), qui a besoin d'AZUREML_MODEL_DIR
    payload = json.dumps({"data": [{"tenure": 12, "MonthlyCharges": 70.5}]})

    result = score.run(payload)

    assert result["status"] == "success"
    assert result["predictions"] == [1]
    assert result["churn_probabilities"] == [0.7]


def test_run_returns_error_for_malformed_json():
    score.model = FakeModel()
    result = score.run("not valid json")

    assert result["status"] == "error"
    assert "message" in result
