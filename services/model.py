import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_model():

    df = pd.read_csv("backend/data/policies_dataset.csv")
    df = df.dropna()  # Remove rows with None values

    X = df[[
        "premium",
        "payment_term",
        "policy_term",
        "total_investment",
        "maturity_value",
        "roi",
        "claim_ratio"
    ]]

    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    joblib.dump(model, "backend/services/risk_model.pkl")

    return model


def load_model():
    path = "backend/services/risk_model.pkl"
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def predict_risk(data):
    """
    Predict policy risk level using the trained ML model.

    Accepts a dict with any of:
        premium, payment_term, policy_term, total_investment,
        maturity_value, roi, cagr, irr, claim_ratio

    Returns one of: 'low', 'medium', 'high'
    """
    model = load_model()

    if model is None:
        return "medium"  # fallback default

    # Only pass the features the model was trained on (from the CSV columns)
    # Extra keys (cagr, irr) are ignored safely here
    input_data = [[
        data.get("premium")          or 0,
        data.get("payment_term")     or 0,
        data.get("policy_term")      or 0,
        data.get("total_investment") or 0,
        data.get("maturity_value")   or 0,
        data.get("roi")              or 0,
        data.get("claim_ratio")      or 90,  # default industry avg claim ratio
    ]]

    try:
        prediction = model.predict(input_data)
        return str(prediction[0]).lower().strip()
    except Exception:
        return "medium"
